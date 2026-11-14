# Container image (e.g. for Hugging Face Spaces, Railway, Fly.io).
# Hugging Face Spaces expects the app on port 7860: set PORT=7860 (default below).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=7860
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend
COPY data/results ./data/results

# The app writes downloaded cutouts to data/cache at runtime.
RUN mkdir -p data/cache && chmod -R a+rwX data

EXPOSE 7860
CMD ["sh", "-c", "uvicorn main:app --app-dir backend --host 0.0.0.0 --port ${PORT}"]
