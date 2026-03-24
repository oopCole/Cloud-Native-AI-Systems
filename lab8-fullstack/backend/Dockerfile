FROM python:3.11-slim

WORKDIR /srv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY lab8-ai /srv/lab8-ai
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -e /srv/lab8-ai

COPY lab8-fullstack/backend /srv/backend
WORKDIR /srv/backend
RUN pip install --no-cache-dir -e .

COPY lab8-fullstack/backend/scripts/docker_entrypoint.py /docker_entrypoint.py

EXPOSE 8000
ENTRYPOINT ["python", "/docker_entrypoint.py"]
