FROM alpine:3.21.3

ARG VERSION=0.0.1
ENV VERSION=${VERSION}

RUN apk add --no-cache python3 py3-pip tzdata

WORKDIR /app

COPY requirements.txt .

RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY config.py .
COPY utils.py .

COPY log_monitor.py .

COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

RUN mkdir -p /log

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/app/entrypoint.sh"]

