# syntax=docker/dockerfile:1.7
# Slimmed multi-stage build. The builder layer compiles wheels with build
# tools; the runtime layer only carries libpq5 + tini + the resolved
# Python deps, then drops to a non-root user.
#
# Targets ~150 MB compressed / ~580 MB on disk by:
#   - dropping `postgresql-client` (entrypoint uses Python TCP probe)
#   - dropping `libmagic1` (no `python-magic` import in the codebase)
#   - replacing PyMuPDF / pdfplumber / requests / flower with smaller libs
#     (see requirements.txt comments)
#   - pruning .dist-info, tests/, __pycache__, *.pyi inside site-packages
#   - stripping native shared objects in cryptography / Pillow / psycopg2
#   - uninstalling pip + setuptools after install

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

# Runtime-only deps:
#   - libpq5    : SQLAlchemy psycopg2 driver
#   - tini      : reaps zombie children (Celery worker spawns many)
#   - binutils  : `strip` for shrinking native .so files (removed afterwards)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tini \
    binutils \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid ${APP_GID} ${APP_USER} \
    && useradd --uid ${APP_UID} --gid ${APP_GID} --create-home --shell /usr/sbin/nologin ${APP_USER}

COPY --from=builder /wheels /wheels
COPY requirements.txt .

# Install everything first; then uninstall pip/setuptools (must precede
# RECORD-file pruning); then aggressive prune + strip; all one layer so
# the cleanup actually shrinks the final image.
RUN pip install --no-cache-dir --no-index --no-compile --find-links=/wheels -r requirements.txt \
    && python -m pip uninstall -y pip setuptools wheel || true \
    && SP=$(python -c "import site;print(site.getsitepackages()[0])") \
    && find "$SP" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true \
    && find "$SP" -type d -name 'tests'       -exec rm -rf {} + 2>/dev/null || true \
    && find "$SP" -type d -name 'test'        -exec rm -rf {} + 2>/dev/null || true \
    && find "$SP" -type d -name 'examples'    -exec rm -rf {} + 2>/dev/null || true \
    && find "$SP" -type f -name '*.pyi'       -delete 2>/dev/null || true \
    && find "$SP" -type f -name '*.pyc'       -delete 2>/dev/null || true \
    && find "$SP" -type f -name 'py.typed'    -delete 2>/dev/null || true \
    && find "$SP" -type f -name '*.so'        -exec strip --strip-unneeded {} + 2>/dev/null || true \
    && apt-get purge -y --auto-remove binutils \
    && rm -rf /wheels /root/.cache /tmp/* /var/tmp/* \
              /usr/share/man /usr/share/doc /usr/share/doc-base /usr/share/info \
              /usr/local/lib/python3.11/ensurepip

COPY --chown=${APP_USER}:${APP_USER} . .
RUN chmod +x /app/entrypoint.sh \
    && mkdir -p /app/books /app/uploads \
    && chown -R ${APP_USER}:${APP_USER} /app

USER ${APP_USER}

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "--", "/app/entrypoint.sh"]
