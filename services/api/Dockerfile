FROM ghcr.io/astral-sh/uv:0.9.26 AS uv
FROM python:3.12.13-slim
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /workspace
COPY pyproject.toml uv.lock ./
COPY packages/simulation packages/simulation
COPY services/api services/api
RUN uv sync --locked --no-dev
RUN useradd --system --uid 10001 --create-home monash
USER monash
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
