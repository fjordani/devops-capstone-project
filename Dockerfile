FROM python:3.9-slim-bullseye

# Install system dependencies, including a compatible version of libpq
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the service package into the working directory
COPY service /app/service

# Create a non-root user and set permissions
RUN useradd --uid 1000 theia && chown -R theia /app

# Switch to the non-root user
USER theia

# Expose the application port
EXPOSE 8080

# Set the entry point to Gunicorn
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "service:app"]