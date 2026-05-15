#!/usr/bin/env bash
# Start the FinAlly container on macOS / Linux. Idempotent: safe to run repeatedly.
#
# Usage:
#   scripts/start_mac.sh            # build if missing, run if not running
#   scripts/start_mac.sh --build    # force rebuild before starting
#   scripts/start_mac.sh --open     # open browser once container is up

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

IMAGE="finally:latest"
CONTAINER="finally"
VOLUME="finally-data"
PORT="8000"

FORCE_BUILD=0
OPEN_BROWSER=0
for arg in "$@"; do
  case "${arg}" in
    --build) FORCE_BUILD=1 ;;
    --open)  OPEN_BROWSER=1 ;;
    -h|--help)
      sed -n '2,7p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: ${arg}" >&2
      exit 2
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed or not on PATH." >&2
  exit 1
fi

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "No .env found — creating one from .env.example."
    cp .env.example .env
    echo "Edit .env to set OPENROUTER_API_KEY before using the AI chat."
  else
    echo "Error: .env not found and no .env.example to copy from." >&2
    exit 1
  fi
fi

# Build if forced or image missing.
if [ "${FORCE_BUILD}" -eq 1 ] || ! docker image inspect "${IMAGE}" >/dev/null 2>&1; then
  echo "Building image ${IMAGE}..."
  docker build -t "${IMAGE}" .
fi

# Ensure the data volume exists (docker run -v will auto-create, but be explicit).
docker volume inspect "${VOLUME}" >/dev/null 2>&1 || docker volume create "${VOLUME}" >/dev/null

# If a container by this name already exists, handle its state.
if docker container inspect "${CONTAINER}" >/dev/null 2>&1; then
  STATE="$(docker inspect -f '{{.State.Status}}' "${CONTAINER}")"
  case "${STATE}" in
    running)
      echo "Container ${CONTAINER} is already running."
      ;;
    paused)
      echo "Unpausing ${CONTAINER}..."
      docker unpause "${CONTAINER}" >/dev/null
      ;;
    *)
      echo "Removing stopped container ${CONTAINER} and recreating..."
      docker rm -f "${CONTAINER}" >/dev/null
      docker run -d \
        --name "${CONTAINER}" \
        --restart unless-stopped \
        -p "${PORT}:8000" \
        -v "${VOLUME}:/app/db" \
        --env-file .env \
        "${IMAGE}" >/dev/null
      ;;
  esac
else
  echo "Starting ${CONTAINER}..."
  docker run -d \
    --name "${CONTAINER}" \
    --restart unless-stopped \
    -p "${PORT}:8000" \
    -v "${VOLUME}:/app/db" \
    --env-file .env \
    "${IMAGE}" >/dev/null
fi

URL="http://localhost:${PORT}"
echo "FinAlly is starting at ${URL}"
echo "Tail logs:  docker logs -f ${CONTAINER}"
echo "Stop with:  scripts/stop_mac.sh"

if [ "${OPEN_BROWSER}" -eq 1 ]; then
  if command -v open >/dev/null 2>&1; then
    open "${URL}"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "${URL}" >/dev/null 2>&1 || true
  fi
fi
