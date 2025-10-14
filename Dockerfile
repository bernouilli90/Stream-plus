# Use Alpine Linux as base (lightweight image)
FROM python:3.11-alpine

# Metadata
LABEL maintainer="Stream Plus"
LABEL description="Stream Plus - Stream management and sorting for Dispatcharr"

# Default environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    USER_UID=1000 \
    USER_GID=1000

# Arguments for UID/GID (for backwards compatibility during build)
ARG USER_UID=1000
ARG USER_GID=1000

# Install system dependencies (ffmpeg and ffprobe)
RUN apk add --no-cache \
    ffmpeg \
    ffmpeg-libs \
    curl \
    su-exec \
    shadow \
    && rm -rf /var/cache/apk/*

# Create non-root user with customizable UID/GID
RUN addgroup -g ${USER_GID} streamplus && \
    adduser -D -u ${USER_UID} -G streamplus streamplus

# Create necessary directories
RUN mkdir -p /app /app/rules /app/tools && \
    chown -R streamplus:streamplus /app

# Set working directory
WORKDIR /app

# Copy requirements.txt first (to leverage Docker cache)
COPY --chown=streamplus:streamplus requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=streamplus:streamplus app.py models.py stream_sorter_models.py execute_rules.py ./
COPY --chown=streamplus:streamplus api/ ./api/
COPY --chown=streamplus:streamplus static/ ./static/
COPY --chown=streamplus:streamplus templates/ ./templates/

# Create file for ffprobe path
RUN mkdir -p /app/tools && \
    echo "/usr/bin/ffprobe" > /app/tools/ffprobe_path.txt && \
    chown -R streamplus:streamplus /app/tools

# Volume for rules (persistence)
VOLUME ["/app/rules"]

# Expose Flask port (configurable via environment variable)
EXPOSE 5000

# Custom entry point script
COPY --chown=streamplus:streamplus docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Switch to non-root user
USER streamplus

# Healthcheck to verify application is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Entry point
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command (start application)
CMD ["python", "app.py"]
