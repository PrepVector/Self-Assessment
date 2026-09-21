# ─────────────────────────────────────────────────────────────────────────────
# Backend Dockerfile — PrepVector Cognitive Assessment API
#
# Base image: Microsoft's official Playwright-for-Python image. It ships
# Chromium plus every OS library Chromium needs (fonts, libnss, etc.), which is
# exactly what the PDF report renderer requires. The image tag is pinned to
# v1.61.0 to match `playwright==1.61.0` in requirements.txt — a version skew
# between the pip package and the bundled browser is the usual cause of
# "browser executable not found" errors.
# ─────────────────────────────────────────────────────────────────────────────
FROM mcr.microsoft.com/playwright/python:v1.61.0-noble

# Keep Python lean and unbuffered for clean container logs.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1. Install Python dependencies first so this layer is cached across code edits.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Ensure the Chromium build that matches this Playwright version is present.
#    The base image already includes it; this is a cheap, explicit safety net.
RUN playwright install chromium

# 3. Copy the application source.
COPY . .

# 4. The app writes CSV logs and PDF reports at runtime — make sure the dirs exist.
RUN mkdir -p /app/data /app/generated_reports

# The API listens on 8000 inside the container.
EXPOSE 8000

# Bind to 0.0.0.0 so the port is reachable from outside the container.
# No --reload in a container image; that's a local-dev convenience only.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
