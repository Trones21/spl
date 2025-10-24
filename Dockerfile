# ---------- Base ----------
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# common system deps (extend as needed for numpy/pandas etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------- Poetry installer layer (cached) ----------
FROM base AS poetry
# install pipx and poetry
RUN python -m pip install --no-cache-dir pipx && \
    pipx install poetry && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry
# global poetry settings for containerized installs
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# ---------- deps (prod only) ----------
FROM poetry AS deps
# copy only files that affect dependency resolution for maximum cache hits
COPY pyproject.toml poetry.lock* ./
RUN poetry install --only main --no-root

# ---------- deps+dev (dev image) ----------
FROM poetry AS deps_dev
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root

# ---------- app (prod) ----------
FROM deps AS runtime
# copy source
COPY src ./src
COPY README.md ./README.md
COPY config ./config
# install the project package itself (editable off; install into site-packages)
RUN poetry install --only main

# create non-root user
RUN useradd -m appuser
USER appuser

# default command: use the console script created by poetry (`spl`)
ENTRYPOINT ["spl"]
# example: docker run ... spl --config config/example.shadow.toml

# ---------- app (dev) ----------
FROM deps_dev AS dev
COPY src ./src
COPY README.md ./README.md
COPY config ./config
RUN poetry install
RUN useradd -m appuser
USER appuser
ENTRYPOINT ["poetry", "run", "spl"]
