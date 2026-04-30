FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /usr/sbin/nologin appuser

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations

RUN chmod +x /app/backend/entrypoint.sh \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["/app/backend/entrypoint.sh"]
