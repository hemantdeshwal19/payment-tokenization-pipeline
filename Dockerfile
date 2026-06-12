# Use slim image to minimize attack surface (fewer packages = fewer vulnerabilities)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user — running as root inside a container is a security risk
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy and install dependencies first (Docker layer caching — faster rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Start the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
