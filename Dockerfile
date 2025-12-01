# Use uv image for faster Python dependency management
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Build argument for version (defaults to "local" for local builds)
ARG VERSION=local

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY cached_yfinance/ ./cached_yfinance/
COPY tools/ ./tools/
COPY scripts/ ./scripts/

# Install Python dependencies using uv
RUN uv sync --frozen

# Create cache directory
RUN mkdir -p /cache

# Make entrypoint script executable
RUN chmod +x ./scripts/entrypoint.sh
RUN chmod +x ./scripts/download_data.sh

RUN chmod 775 /app
RUN chown -R 1000:1000 /app

# Set default environment variables
ENV TICKER=""
ENV INTERVAL="1d"
ENV DAYS="60"
ENV CACHE_DIR="/cache"

# Set the entrypoint
ENTRYPOINT ["./scripts/entrypoint.sh"]

# Add labels for better container management
LABEL maintainer="markcallen"
LABEL description="Download historical stock data using cached-yfinance"
LABEL version="${VERSION}"

CMD ["scripts/download_data.sh"]
