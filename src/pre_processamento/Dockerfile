FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pre_processamento.py .
COPY pipeline_functions.py .

RUN touch /var/log/script.log

COPY crontab /etc/cron.d/script-cron

RUN chmod 0644 /etc/cron.d/script-cron

RUN crontab /etc/cron.d/script-cron

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 9000 9047 5434

ENTRYPOINT ["/entrypoint.sh"]