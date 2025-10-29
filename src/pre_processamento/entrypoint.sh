#!/bin/bash

service cron start

echo "Executando script inicial..."
cd /app && python3 pre_processamento.py

echo "Cron iniciado. Monitorando logs..."
tail -f /var/log/script.log