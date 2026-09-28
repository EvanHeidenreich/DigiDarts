# DigiDarts Startup Guide

How to get the DigiDarts backend and computer vision code running locally.

## Prerequisites

- **Docker Desktop** installed and running (check for the whale icon in your menu bar)
- Docker CLI available on your PATH — verify with:
  ```bash
  docker --version
  docker compose version
  ```

> **macOS PATH note:** If you installed Docker Desktop and get `command not found: docker` in your terminal, the CLI lives at `~/.docker/bin/docker` but may only be added to your PATH in `~/.zprofile` (login shells), not `~/.zshrc` (interactive shells). Terminals like VS Code's integrated terminal often only source `~/.zshrc`. Fix it with:
> ```bash
> echo 'export PATH="$PATH:$HOME/.docker/bin"' >> ~/.zshrc
> source ~/.zshrc
> ```

## Start the backend

From the repo root:

```bash
docker compose up --build
```

- `--build` rebuilds the image — needed the first time, or after changing `backend/requirements.txt` or the `Dockerfile`.
- On later runs with no dependency changes, you can drop it: `docker compose up`.
- To run in the background: `docker compose up --build -d`

The API will be available at **http://localhost:8000**.

Code under [backend/app](backend/app) is mounted as a live volume and Uvicorn runs with `--reload`, so code edits apply automatically without restarting the container.

## Stop the backend

```bash
docker compose down
```

(Ctrl+C first if it's running in the foreground.)

## Using the VS Code Dev Container (alternative)

This repo also includes a [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) config. In VS Code:

1. Install the **Dev Containers** extension.
2. Command Palette → **Dev Containers: Reopen in Container**.

This uses the same `docker-compose.yml`, attaches to the `backend` service, and runs `pip install -r requirements.txt` automatically.

## Computer Vision (uv)

The [computer_vision](computer_vision) code runs locally via [uv](https://docs.astral.sh/uv/) rather than in Docker, since it needs a real camera and (for debugging) a display — both of which the headless backend container doesn't have. `uv` manages its own virtual environment from the root [pyproject.toml](pyproject.toml)/`uv.lock`, completely separate from the backend's Docker setup — you can run both at the same time with no conflicts.

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify it's installed:

```bash
uv --version
```

> **PATH note:** the installer adds `~/.local/bin` to your PATH via a line in `~/.zshrc`, but that only takes effect in *new* terminal sessions. If `uv --version` says `command not found` right after installing, either open a new terminal tab or run:
> ```bash
> source ~/.zshrc
> ```

### Set up the environment

From the repo root:

```bash
uv sync
```

This creates a `.venv/` and installs everything listed in `pyproject.toml` (currently `opencv-python`, `numpy`, and `pytest` as a dev dependency). You don't need to run this by hand after every change — `uv add`/`uv remove` keep it in sync automatically, and `uv run` (below) will sync it for you if it's ever out of date.

### Run it

There's no server or container to "start" — every `uv run` invocation just runs that one command inside the project's venv and exits:

```bash
uv run python -m computer_vision.src.main --camera 0
```

To avoid typing `uv run` before every command, activate the venv once per terminal session instead:

```bash
source .venv/bin/activate
python -m computer_vision.src.main --camera 0
```

(stays active until you close the terminal or run `deactivate`)

### Run the tests

```bash
uv run python -m pytest computer_vision/tests
```

Use `python -m pytest`, not `uv run pytest` — the bare `pytest` script doesn't add the repo root to `sys.path`, so the `computer_vision.src.*` imports in the tests won't resolve.
