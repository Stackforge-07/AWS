FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend ./backend
COPY frontend/public/india-states.geojson ./frontend/public/india-states.geojson
COPY ml/artifacts ./ml/artifacts
COPY edge/models ./edge/models
RUN mkdir -p /app/data && useradd -m skyguard && chown -R skyguard:skyguard /app
USER skyguard
EXPOSE 8010
CMD ["uv", "run", "--no-sync", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8010"]
