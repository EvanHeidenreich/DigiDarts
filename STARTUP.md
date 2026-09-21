# Backend Startup Guide

How to get the DigiDarts backend running locally.

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
