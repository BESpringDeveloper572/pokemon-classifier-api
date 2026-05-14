# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MODEL_NAME="skshmjn/Pokemon-classifier-gen9-1025"

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup -d /home/appuser -m appuser

# Set up cache directories in the user's home and ensure they are writable
ENV U2NET_HOME=/home/appuser/.u2net
RUN mkdir -p /home/appuser/.u2net /home/appuser/.cache/pokebase /app/app/data/model /app/app/data/cache \
    && chown -R appuser:appgroup /home/appuser /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files and set ownership
COPY --chown=appuser:appgroup . .

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
