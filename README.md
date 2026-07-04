# Chat With Your Robot

Using VLMs to interact with an expressive Reachy Mini robot (AIxHRI Summer School 2026).

## Prerequisites

- Docker and Docker Compose installed (see [docker setup guide](https://github.com/aixhri-summer-school-2026/docker-nvidia-tuto)).
- Reachy Mini connected by USB.
- Linux host with permission to run `sudo`.

## Setup

If you want to do the first part on your own in one of our two available machines.
tic.local or tac.local. You will first need to ssh into that machine with this specific command:

```bash
ssh -L 80XX:localhost:80XX userXX@remote-machine-ip
```
Where `XX` is your user number (e.g., `ssh -L 8010:localhost:8010 user10@remote-machine-ip`).


Clone the repository:

```bash
git clone git@github.com:aixhri-summer-school-2026/Tutorial_02_Chat_with_your_robot.git
cd Tutorial_02_Chat_with_your_robot

```
Checkout to the ssh_mode branch:

```bash
git checkout ssh_mode
```

## Container Registry (Pulling Images)

Normally this step is not needed but better to be sure you have the latest images. You can pull the latest images from the official container registry using the following commands:


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

*Look at the terminal output for the `http://127.0.0.1:88XX...` link and open it in your browser to access `first_module.ipynb`.*

### Phase 2: The Final Assignment (Hardware Deployment)
Unfortunately this part is not possible remotely. You will need to collaborate with someone else that has a local working setup!

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
