# Chat With Your Robot

Using VLMs to interact with an expressive Reachy Mini robot (AIxHRI Summer School 2026).

If you are among the people who don't have an Nvidia GPU:
- You can follow the tutorial on a CPU-only machine.
If you don't have Ubuntu, you can check out the `ssh_mode` branch and follow the instructions to run the tutorial on a remote server; note that only the first module will be available in this case, as the second module requires a local Reachy Mini connection.

## Prerequisites

- Docker and Docker Compose installed (see [docker setup guide](https://github.com/aixhri-summer-school-2026/docker-nvidia-tuto)).
- Reachy Mini connected by USB.
- Linux host with permission to run `sudo`.

## Setup

Clone the repository:

```bash
git clone git@github.com:aixhri-summer-school-2026/Tutorial_02_Chat_with_your_robot.git
cd Tutorial_02_Chat_with_your_robot

```

Install udev rules (USB + camera symlink):

```bash
sudo bash scripts/usb_permissions.sh
sudo bash scripts/camera_rules.sh
```

If group permissions were updated, log out and log back in once.

## Container Registry (Pulling Images)

To save time during the practical exercises, you will not build the environments locally. Pre-built images are pulled directly from the official container registry.

```bash
# For machines with an NVIDIA GPU
docker pull aixhrisummerschool2026/aixhri-summer-school-2026:Tutorial_02_Chat_with_your_robot_gpu

# For machines without a GPU (CPU-only)
docker pull aixhrisummerschool2026/aixhri-summer-school-2026:Tutorial_02_Chat_with_your_robot_cpu

```

## Running the Tutorial

The tutorial is split into two distinct phases.

### Phase 1: Interactive Learning (Jupyter Lab)

In this phase, you will learn the fundamentals of local Vision-Language Models, JSON Schemas, and strict GBNF Grammars.

```bash
# Launch the Jupyter Lab environment
make module1-gpu   # (or make module1-cpu)

```

*Look at the terminal output for the `http://127.0.0.1:8888...` link and open it in your browser to access `first_module.ipynb`.*

### Phase 2: The Final Assignment (Hardware Deployment)

Once you have completed Module 1, you will use those skills to build a real-time reactive streaming loop with Reachy Mini.

```bash
# Launch the interactive terminal
make assignment-gpu  # (or make assignment-cpu)
```

*This will start the Reachy daemon in the background and drop you directly into the `/app/lab` folder. Edit `assignment.py` in your preferred IDE, and run it here using `python lab/assignment.py`.*

## Utilities

Stream logs:

```bash
make logs-gpu  # (or make logs-cpu)

```

Stop everything and clean up:

```bash
make down

```

---

## Maintainer Deployment

This category lists the commands required for maintainers to push updated images to the container registry.

To push a new image update, tag the local build and run the corresponding push command:

```bash
# Push GPU Image
docker push aixhrisummerschool2026/aixhri-summer-school-2026:Tutorial_02_Chat_with_your_robot_gpu

# Push CPU Image
docker push aixhrisummerschool2026/aixhri-summer-school-2026:Tutorial_02_Chat_with_your_robot_cpu

```
