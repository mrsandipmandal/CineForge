FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CINEFORGE_HOME=/workspace \
    CINEFORGE_REMOTION_DIR=/opt/cineforge/remotion-composer \
    BACKLOT_HOST=0.0.0.0 \
    BACKLOT_PORT=4750

# Install FFmpeg, Node.js 22 LTS (required for Remotion + HyperFrames), and Chromium deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    ffmpeg \
    gnupg \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Stage and install Remotion dependencies separately for layer caching
COPY remotion-composer/package.json remotion-composer/package-lock.json /opt/cineforge/remotion-composer/
RUN cd /opt/cineforge/remotion-composer && npm ci --no-audit --no-fund
COPY remotion-composer/ /opt/cineforge/remotion-composer/

# Pre-warm HyperFrames CLI in npx cache
RUN npx --yes hyperframes --version || true

# Install CineForge package + MCP + free offline TTS
COPY . /app
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[all]"

RUN mkdir -p /workspace/projects /workspace/music_library

WORKDIR /workspace

EXPOSE 4750 8766

CMD ["cineforge", "studio", "--foreground", "--host", "0.0.0.0", "--port", "4750"]
