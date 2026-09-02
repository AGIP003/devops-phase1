FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY --chown=appuser:appgroup . .

USER appuser

EXPOSE 5000

CMD ["sh", "-c", "exec gunicorn run:app --bind 0.0.0.0:${PORT:-5000} --workers ${WEB_CONCURRENCY:-3} --no-control-socket"]
