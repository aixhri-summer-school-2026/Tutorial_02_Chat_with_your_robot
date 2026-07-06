.PHONY: build-cpu build-gpu module1-cpu module1-gpu assignment-cpu assignment-gpu down install-rules logs-cpu logs-gpu

USER_NUM := $(shell whoami | sed 's/user//')
PORT := 80$(USER_NUM)

export UID := $(shell id -u)
export GID := $(shell id -g)

# --- Build targets separated ---
build-cpu:
	docker compose --profile cpu build

build-gpu:
	docker compose --profile gpu build

# --- MODULE 1: Jupyter Lab (first_module.ipynb) ---
module1-cpu:
	docker compose --profile cpu run --rm -p $(PORT):$(PORT) --name reachy-$(USER) \
	reachy-mini-cpu jupyter lab --ip=0.0.0.0 --port=$(PORT) --no-browser \
	--notebook-dir=/app/lab --ServerApp.token='' --ServerApp.password='' --ServerApp.allow_root=True

module1-gpu:
	docker compose --profile gpu run --rm -p $(PORT):$(PORT) --name reachy-$(USER) \
	reachy-mini-gpu jupyter lab --ip=0.0.0.0 --port=$(PORT) --no-browser \
	--notebook-dir=/app/lab --ServerApp.token='' --ServerApp.password='' --ServerApp.allow_root=True

# --- ASSIGNMENT: Interactive Terminal (assignment.py) ---
assignment-cpu:
	@echo "This assignment can only be done locally you should collaborate with someone else."
assignment-gpu:
	@echo "This assignment can only be done locally you should collaborate with someone else."

down:
	docker compose --profile cpu --profile gpu down

install-rules:
	bash scripts/camera_rules.sh && bash scripts/usb_permissions.sh

logs-cpu:
	docker compose logs -f reachy-mini-cpu

logs-gpu:
	docker compose logs -f reachy-mini-gpu