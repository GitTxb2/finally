# ---------- Stage 1: build the Next.js static export ----------
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend

# Copy manifest files first for better layer caching.
COPY frontend/package.json frontend/package-lock.json* ./

# Use npm ci when a lockfile is present; fall back to npm install otherwise.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY frontend/ ./

# Next.js with `output: 'export'` writes the static site to ./out
RUN npm run build


# ---------- Stage 2: backend runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/backend/.venv \
    PATH="/app/backend/.venv/bin:${PATH}" \
    STATIC_DIR=/app/static \
    DB_PATH=/app/db/finally.db

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv via the official standalone installer (does not require Python).
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && mv /root/.local/bin/uvx /usr/local/bin/uvx

WORKDIR /app/backend

# Install python deps from the lockfile first for caching.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy backend source and finish project install.
COPY backend/ ./
RUN uv sync --frozen --no-dev

# Copy the built frontend into /app/static for FastAPI to serve.
COPY --from=frontend-build /app/frontend/out /app/static

# Volume target for the SQLite database. The backend creates finally.db here on first request.
RUN mkdir -p /app/db
VOLUME ["/app/db"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/api/health || exit 1

CMD ["uv", "run", "--frozen", "--no-dev", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
