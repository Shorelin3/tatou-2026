# Server image: minimal Flask + Gunicorn
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      git \
      ca-certificates \
      openssh-client \
      gosu \
 && rm -rf /var/lib/apt/lists/*

# Copy project description, to install dependencies
COPY pyproject.toml /app/pyproject.toml

# Install runtime dependencies
RUN pip install --no-cache-dir -e .

# Create a non-root user for the application
RUN useradd --create-home --shell /bin/bash tatou

# Copy application files
COPY src /app/src
COPY flag /app/flag
COPY entrypoint.sh /app/entrypoint.sh

# Protect the flag and prepare writable application storage
RUN chown root:root /app/flag \
 && chmod 600 /app/flag \
 && mkdir -p /app/storage \
 && chown -R tatou:tatou /app/storage \
 && chmod +x /app/entrypoint.sh

# Install dependencies again after copying project files
RUN pip install --no-cache-dir -e .

EXPOSE 5000

# Startup script performs initialization as root,
# then starts the application as the non-root user
CMD ["./entrypoint.sh"]
