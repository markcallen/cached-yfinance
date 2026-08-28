FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

ARG VERSION=local

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOME=/tmp
ENV UV_CACHE_DIR=/tmp/uv-cache

COPY pyproject.toml uv.lock README.md ./
COPY cached_yfinance/ ./cached_yfinance/
COPY tools/ ./tools/
COPY scripts/ ./scripts/

RUN uv sync --frozen

RUN mkdir -p /cache /tmp/uv-cache \
    && chmod +x ./scripts/entrypoint.sh ./scripts/download_data.sh \
    && chown -R 1000:1000 /app /cache /tmp/uv-cache

ENV TICKER=""
ENV INTERVAL="1d"
ENV DAYS="60"
ENV CACHE_DIR="/cache"

LABEL maintainer="markcallen"
LABEL description="Download historical stock data using cached-yfinance"
LABEL version="${VERSION}"

USER 1000:1000

ENTRYPOINT ["./scripts/entrypoint.sh"]
CMD ["./scripts/download_data.sh"]
