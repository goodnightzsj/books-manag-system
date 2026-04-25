# syntax=docker/dockerfile:1.7
# Multi-stage hardened image. The builder layer compiles wheels with build
# tools; the runtime layer only carries libpq5 / libmagic1 / pg_isready and
# the resolved Python deps, then drops to a non-root user.

FROM python:3.11-slim AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


FROM python:3.11-slim
WORKDIR /app

ARG APP_USER=books
ARG APP_UID=1000
ARG APP_GID=1000

# Runtime-only system deps. libpq5 -> SQLAlchemy psycopg2; libmagic1 ->
# python-magic; postgresql-client -> entrypoint.sh pg_isready.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    postgresql-client \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid ${APP_GID} ${APP_USER} \
    && useradd --uid ${APP_UID} --gid ${APP_GID} --create-home --shell /usr/sbin/nologin ${APP_USER}

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels /root/.cache

COPY --chown=${APP_USER}:${APP_USER} . .
RUN chmod +x /app/entrypoint.sh \
    && mkdir -p /app/books /app/uploads \
    && chown -R ${APP_USER}:${APP_USER} /app

USER ${APP_USER}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

EXPOSE 8000

# tini reaps zombie processes (Celery workers spawn many short-lived children).
ENTRYPOINT ["/usr/bin/tini", "--", "/app/entrypoint.sh"]
