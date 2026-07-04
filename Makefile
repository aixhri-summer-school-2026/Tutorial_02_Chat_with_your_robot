.PHONY: build-cpu build-gpu module1-cpu module1-gpu assignment-cpu assignment-gpu down install-rules logs-cpu logs-gpu

export UID := $(shell id -u)
export GID := $(shell id -g)

# --- Build targets separated ---
build-cpu:
	docker compose --profile cpu build

build-gpu:
	docker compose --profile gpu build

# --- MODULE 1: Jupyter Lab (first_module.ipynb) ---
module1-cpu:
	docker compose --profile cpu run --rm reachy-mini-cpu jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --notebook-dir=/app/lab --ServerApp.token='' --ServerApp.password='' --ServerApp.allow_root=True

module1-gpu:
	docker compose --profile gpu run --rm reachy-mini-gpu jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --notebook-dir=/app/lab --ServerApp.token='' --ServerApp.password='' --ServerApp.allow_root=True

# --- ASSIGNMENT: Interactive Terminal (assignment.py) ---
assignment-cpu:
	docker compose --profile cpu run --rm -it reachy-mini-cpu /bin/bash -c "reachy-mini-daemon & cd /app/lab && /bin/bash"

assignment-gpu:
	docker compose --profile gpu run --rm -it reachy-mini-gpu /bin/bash -c "reachy-mini-daemon & cd /app/lab && /bin/bash"

down:
	docker compose --profile cpu --profile gpu down

install-rules:
	bash scripts/camera_rules.sh && bash scripts/usb_permissions.sh

logs-cpu:
	docker compose logs -f reachy-mini-cpu

logs-gpu:
	docker compose logs -f reachy-mini-gpu