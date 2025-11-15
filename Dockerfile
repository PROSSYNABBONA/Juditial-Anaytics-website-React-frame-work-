# Multi-stage build for React + FastAPI

# Stage 1: Build React frontend
FROM node:18-alpine AS frontend-build
WORKDIR /app
COPY judicial-dashboard/frontend/package*.json ./judicial-dashboard/frontend/
WORKDIR /app/judicial-dashboard/frontend
ENV NPM_CONFIG_UPDATE_NOTIFIER=false
ENV CI=true
# Ensure devDependencies are installed (react-scripts lives in devDeps)
RUN npm ci --include=dev
COPY judicial-dashboard/frontend/ ./
# Fix potential CRLF/permission on bin scripts (react-scripts)
RUN chmod -R +x node_modules/.bin || true
RUN npm run build

# Stage 2: Python backend with frontend
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system dependencies (for PDF/OCR if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements
COPY judicial-dashboard/backend/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY judicial-dashboard/backend/ ./backend/

# Copy built frontend from Stage 1
COPY --from=frontend-build /app/judicial-dashboard/frontend/build ./backend/app/static

# Create uploads directory
RUN mkdir -p ./backend/uploads

# Expose port
EXPOSE $PORT

# Run uvicorn
WORKDIR /app/backend
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

