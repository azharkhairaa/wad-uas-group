# build frontend Vue
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# FastAPI yang juga menyajikan hasil build, web dan API satu origin
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 STATIC_DIR=/app/web
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY --from=web /web/dist ./web

# jalan sebagai user biasa, bukan root
RUN useradd --create-home lapangin && chown -R lapangin:lapangin /app
USER lapangin

EXPOSE 8000
# migrasi dulu baru server. Render mengisi PORT sendiri dan meneruskan IP asli lewat X-Forwarded-For
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
