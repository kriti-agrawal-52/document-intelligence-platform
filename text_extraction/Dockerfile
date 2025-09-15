# Multi-stage build for text_extraction service
FROM python:3.11-slim-bullseye as builder

# Install build dependencies and PDF processing tools
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY text_extraction/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim-bullseye

# Install runtime dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy DocumentDB certificate
COPY text_extraction/global-bundle.pem /app/global-bundle.pem

# Copy application code
COPY text_extraction/ ./text_extraction/
COPY shared/ ./shared/
COPY config.yml ./config.yml

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/extract/health', timeout=5)"

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "text_extraction.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]