# syntax=docker/dockerfile:1

# Single image for the whole uv workspace: every backend service shares the same
# dependency closure, so they all run from this image and differ only by the
# `ristops start <app>` command passed by compose.

FROM python:3.14-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# workspace members are installed from source, so the whole tree is part of the
# dependency resolution and there is no separate deps-only layer to cache
COPY pyproject.toml uv.lock ./
COPY packages/ packages/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.14-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# curl only exists for the healthcheck (docker-compose.yaml) — slim base images ship neither
# curl nor wget, and the alternative is a python -c/urllib one-liner, which is unusual enough
# to read as a mistake rather than a deliberate choice
RUN apt-get update && apt-get install --no-install-recommends -y curl \
    && rm -rf /var/lib/apt/lists/*

# workspace packages are installed as editable, so the venv points back at
# /app/packages/*/src and the source tree must ship with it
COPY --from=builder /app /app

RUN groupadd --system ristops \
    && useradd --system --gid ristops --no-create-home ristops \
    && chown -R ristops:ristops /app

USER ristops
WORKDIR /app

ENTRYPOINT ["ristops"]
