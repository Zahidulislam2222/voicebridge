# The caller supplies the registry-verified immutable Python image reference.
ARG PYTHON_IMAGE
FROM ${PYTHON_IMAGE}
ARG APP_UID
ARG APP_GID
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements-runtime.lock ./
RUN python -m pip install --no-cache-dir -r requirements-runtime.lock
COPY pyproject.toml ./
COPY apps/api ./apps/api
COPY alembic.ini ./
COPY data/core ./data/core
COPY config/provider-profiles.json ./config/provider-profiles.json
COPY config/observation-profiles.json ./config/observation-profiles.json
RUN python -m pip install --no-deps --no-build-isolation .
USER ${APP_UID}:${APP_GID}
ENTRYPOINT ["python", "-m", "voicebridge.cli"]
