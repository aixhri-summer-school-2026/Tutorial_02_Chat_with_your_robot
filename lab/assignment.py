import os
import time
import re
import threading
import cv2
import torch
import numpy as np
import scipy.signal
from PIL import Image
from pocket_tts import TTSModel
from reachy_mini import ReachyMini
from reachy_mini.motion.recorded_move import RecordedMove, RecordedMoves
from reachy_mini.media.audio_utils import save_audio_to_wav
from silero_vad import load_silero_vad
from faster_whisper import WhisperModel
from llama_cpp import LlamaGrammar
from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
import base64
from io import BytesIO

MODEL_PATH = "/app/models/gemma-4-E4B-it-Q4_K_M.gguf"
CLIP_PATH = "/app/models/mmproj-BF16.gguf"

# Gag the Audio Pipeline Logs
import logging
logging.getLogger("reachy_mini").setLevel(logging.WARNING)
os.environ["GST_DEBUG"] = "0"
os.environ["RUST_LOG"] = "error"

# ====================================================================
# HELPER FUNCTIONS (Do not modify these)
# ====================================================================

def stream_tts(mini, tts_model, voice_state, text, interrupt_event):
    if interrupt_event.is_set(): return
    target_sr = mini.media.get_output_audio_samplerate()
    model_sr = tts_model.sample_rate
    total_audio_duration = 0.0
    start_time = time.time()

    for chunk_tensor in tts_model.generate_audio_stream(voice_state, text):
        if interrupt_event.is_set(): return
        audio_chunk = chunk_tensor.numpy().astype(np.float32)
        if model_sr != target_sr:
            num_samples = int(len(audio_chunk) * target_sr / model_sr)
            audio_chunk = scipy.signal.resample(audio_chunk, num_samples).astype(np.float32)
        chunk_duration = len(audio_chunk) / target_sr
        total_audio_duration += chunk_duration
        mini.media.push_audio_sample(audio_chunk)
        elapsed = time.time() - start_time
        ahead_by = total_audio_duration - elapsed
        if ahead_by > 0.1: time.sleep(ahead_by - 0.05)

    elapsed = time.time() - start_time
    remaining = total_audio_duration - elapsed
    if remaining > 0 and not interrupt_event.is_set(): time.sleep(remaining + 0.1)

def monitor_barge_in(mini, vad_model, interrupt_event, playback_active):
    mini.media.start_recording()
    target_sr = 16000
    vad_window_samples = 512
    samplerate = mini.media.get_input_audio_samplerate()
    audio_samples_stream = []

    while playback_active.is_set() and not interrupt_event.is_set():
        sample = mini.media.get_audio_sample()
        if sample is not None:
            audio_samples_stream.append(sample)
            current_buffer = np.concatenate(audio_samples_stream, axis=0)
            samples_needed_raw = int(samplerate * (vad_window_samples / target_sr))
            if len(current_buffer) >= samples_needed_raw:
                chunk_to_process = current_buffer[:samples_needed_raw]
                audio_samples_stream = [current_buffer[samples_needed_raw:]]
                if chunk_to_process.ndim > 1: chunk_to_process = chunk_to_process[:, 0]
                if samplerate != target_sr:
                    num_target_samples = int(len(chunk_to_process) * target_sr / samplerate)
                    chunk_16k = scipy.signal.resample(chunk_to_process, num_target_samples).astype(np.float32)
                else: chunk_16k = chunk_to_process

                vad_input = chunk_16k[:vad_window_samples]
                if len(vad_input) == vad_window_samples:
                    tensor = torch.from_numpy(vad_input).unsqueeze(0)
                    speech_prob = vad_model(tensor, target_sr).item()
                    if speech_prob > 0.4:
                        print("\n[BARGE-IN DETECTED] Interrupting...")
                        interrupt_event.set()
                        mini.media.stop_playing()
                        break
        time.sleep(0.01)
    mini.media.stop_recording()

def listen_for_user(mini, vad_model, stt_model):
    target_sr = 16000
    vad_window_samples = 512
    SILENCE_TOLERANCE_SECONDS = 1.0
    mini.media.start_recording()
    start_time = time.time()
    while mini.media.get_audio_sample() is None:
        if time.time() - start_time > 2.0:
            mini.media.stop_recording()
            return ""
        time.sleep(0.01)

    samplerate = mini.media.get_input_audio_samplerate()
    print("\n🎤 State: WAITING - Start speaking whenever you are ready... (Press Ctrl+C to exit)")
    is_speaking = False
    silence_start_time = None
    audio_samples_stream = []
    recorded_speech_chunks = []

    try:
        while True:
            sample = mini.media.get_audio_sample()
            if sample is not None:
                audio_samples_stream.append(sample)
                current_buffer = np.concatenate(audio_samples_stream, axis=0)
                samples_needed_raw = int(samplerate * (vad_window_samples / target_sr))
                if len(current_buffer) >= samples_needed_raw:
                    chunk_to_process = current_buffer[:samples_needed_raw]
                    leftover = current_buffer[samples_needed_raw:]
                    audio_samples_stream = [leftover] if len(leftover) > 0 else []
                    if chunk_to_process.ndim > 1: chunk_to_process = chunk_to_process[:, 0]
                    if samplerate != target_sr:
                        num_target_samples = int(len(chunk_to_process) * target_sr / samplerate)
                        chunk_16k = scipy.signal.resample(chunk_to_process, num_target_samples).astype(np.float32)
                    else: chunk_16k = chunk_to_process

                    vad_input = chunk_16k[:vad_window_samples]
                    if len(vad_input) == vad_window_samples:
                        tensor = torch.from_numpy(vad_input).unsqueeze(0)
                        speech_prob = vad_model(tensor, target_sr).item()
                        if speech_prob > 0.4:
                            if not is_speaking:
                                print("🗣️ State: SPEAKING - Recording voice...")
                                is_speaking = True
                                mini.goto_target(antennas=[0.6, 0.6], duration=0.2)
                            silence_start_time = None
                        else:
                            if is_speaking:
                                if silence_start_time is None: silence_start_time = time.time()
                                elapsed_silence = time.time() - silence_start_time
                                if elapsed_silence >= SILENCE_TOLERANCE_SECONDS:
                                    print("⏱️ State: SILENCE DETECTED - Finished phrase. Transcribing...")
                                    mini.goto_target(antennas=[0.0, 0.0], duration=0.3)
                                    break
                        if is_speaking: recorded_speech_chunks.append(chunk_to_process)
            time.sleep(0.01)
        mini.media.stop_recording()
        if recorded_speech_chunks:
            audio_data = np.concatenate(recorded_speech_chunks, axis=0)
            os.makedirs("tests/test_output", exist_ok=True)
            output_file = "tests/test_output/chat_input.wav"
            save_audio_to_wav(audio_data, samplerate, output_file)
            segments, info = stt_model.transcribe(output_file, beam_size=5)
            transcription = " ".join([segment.text.strip() for segment in segments]).strip()
            print(f"You: {transcription}")
            return transcription
    except KeyboardInterrupt:
        mini.media.stop_recording()
        return "quit"
    mini.media.stop_recording()
    return ""

def image_to_base64_data_uri_from_pil(pil_image: Image.Image):
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")
    base64_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{base64_data}"


# ====================================================================
# MAIN ASSIGNMENT
# ====================================================================

def main():
    print("Loading AI Models and Datasets...")

    # Load VLM
    chat_handler = Llava15ChatHandler(clip_model_path=CLIP_PATH)
    local_vlm = Llama(
        model_path=MODEL_PATH,
        chat_handler=chat_handler,
        n_gpu_layers=-1,
        n_ctx=8192,
        verbose=False,
    )

    # Load Audio Models
    tts_model = TTSModel.load_model(language="english")
    voice_state = tts_model.get_state_for_audio_prompt("alba")
    vad_model = load_silero_vad()
    stt_model = WhisperModel("tiny.en", device="cuda", compute_type="float16")

    # Load the Emotion Library
    emotions_library = RecordedMoves("pollen-robotics/reachy-mini-emotions-library")

    # TODO 1: Compile your GBNF Grammar
    # 1. Define a GBNF string that forces the model to output a motion in brackets, followed by text.
    # 2. Allow at least these motions: "cheerful1", "sad1", "confused1", "dance1", "rage1"
    # 3. Compile it using LlamaGrammar.from_string()

    # compiled_grammar = ...

    with ReachyMini() as mini:
        print("\n=== Reactive Voice Chat Started ===")
        while True:
            # Listen for user audio
            prompt = listen_for_user(mini, vad_model, stt_model)
            if not prompt or prompt.lower() in ["quit", "exit"]: break

            # Grab Camera Frame
            frame = mini.media.get_frame()
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)) if frame is not None else None
            image_data_uri = image_to_base64_data_uri_from_pil(pil_image) if pil_image is not None else None

            # TODO 2: Build the Messages Array
            # Create the OpenAI-style `messages` list.
            # - Write a System Prompt that grounds Reachy in its physical embodiment and forces the [ACTION] format.
            # - Add at least 3 Few-Shot examples to show the model how to react instantly without explaining itself.
            # - Pass the current user `prompt` and `image_data_uri` at the end.

            messages = [
                # YOUR PROMPT ARRAY HERE
            ]

            # Setup Interruption Events (Barge-In)
            interrupt_event = threading.Event()
            playback_active = threading.Event()
            playback_active.set()

            barge_in_thread = threading.Thread(
                target=monitor_barge_in,
                args=(mini, vad_model, interrupt_event, playback_active),
            )
            barge_in_thread.start()

            # TODO 3: Start the VLM Stream
            # Call `local_vlm.create_chat_completion(...)`
            # Ensure you pass: messages, max_tokens, a low temperature, stream=True, and your compiled grammar.

            # stream = ...

            sentence_buffer = ""
            action_extracted = False
            mini.media.start_playing()

            # TODO 4: Process the Stream
            # Write a `for chunk in stream:` loop to process the generated tokens.
            # Requirements:
            # A. Extract the text content from the chunk dictionary safely.
            # B. If you detect a closed bracket "]", extract the action name using regex.
            # C. Fetch the action from `emotions_library` and execute it in a BACKGROUND THREAD.
            # D. Strip the bracketed action text completely out of `sentence_buffer`.
            # E. Once the action is stripped, check for punctuation (`[.!?\n]`) in the buffer.
            # F. When a full sentence forms, slice it out of the buffer and send it to `stream_tts()`.

            # YOUR STREAMING LOOP HERE

            # Speak any leftover text in the buffer when generation finishes
            if sentence_buffer.strip() and action_extracted and not interrupt_event.is_set():
                print(f"🗣️ Reachy: {sentence_buffer.strip()}")
                stream_tts(mini, tts_model, voice_state, sentence_buffer.strip(), interrupt_event)

            # Clean up Barge-in monitor
            playback_active.clear()
            barge_in_thread.join(timeout=1.0)
            if not interrupt_event.is_set():
                mini.media.stop_playing()

if __name__ == "__main__":
    main()