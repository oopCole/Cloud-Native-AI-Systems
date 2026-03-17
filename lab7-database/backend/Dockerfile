FROM python:3.11-slim

WORKDIR /srv/backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml /srv/backend/pyproject.toml

RUN python -m pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
      "fastapi>=0.100.0" \
      "uvicorn[standard]>=0.22.0" \
      "httpx>=0.24.0" \
      "python-dotenv>=1.0.0" \
      "psycopg[binary]>=3.1.0"

COPY . /srv/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
