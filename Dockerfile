
# Dockerfile with Redis Caching - Drop-in Replacement
# Use this to update your existing Docker container

FROM python:3.12-slim

# Install system dependencies including Redis
RUN apt-get update && apt-get install -y \
    redis-server \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/cache

# Configure Redis for container use
RUN sed -i 's/bind 127.0.0.1/bind 0.0.0.0/' /etc/redis/redis.conf && \
    sed -i 's/# port 6379/port 6379/' /etc/redis/redis.conf && \
    sed -i 's/# save 900 1/save 900 1/' /etc/redis/redis.conf && \
    sed -i 's/# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf && \
    sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf

# Create startup script
RUN echo '#!/bin/bash\n\
# Start Redis in background\n\
redis-server /etc/redis/redis.conf --daemonize yes\n\
\n\
# Wait for Redis to start and be ready\n\
echo "Waiting for Redis to start..."\n\
for i in {1..10}; do\n\
    if redis-cli ping > /dev/null 2>&1; then\n\
        echo "Redis started successfully"\n\
        break\n\
    else\n\
        echo "Redis not ready yet, waiting... ($i/10)"\n\
        sleep 1\n\
    fi\n\
done\n\
\n\
# Final Redis check\n\
if ! redis-cli ping > /dev/null 2>&1; then\n\
    echo "Redis failed to start, continuing without caching..."\n\
    export REDIS_AVAILABLE=false\n\
else\n\
    echo "Redis is running and ready"\n\
    export REDIS_AVAILABLE=true\n\
fi\n\
\n\
# Start Flask application\n\
exec gunicorn --bind 0.0.0.0:5007 --workers 2 --timeout 60 app:app\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 5007 6379

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5007/health && redis-cli ping || exit 1

# Start both Redis and Flask
CMD ["/app/start.sh"]
