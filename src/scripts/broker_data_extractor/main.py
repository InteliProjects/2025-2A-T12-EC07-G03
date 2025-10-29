#!/usr/bin/env python3
"""
Programa MQTT que escuta tópicos e salva mensagens em arquivos CSV.
Cria novos arquivos a cada 10 minutos de log.
Lê configurações do arquivo .env e tópicos do arquivo topicos_dispositivos.txt
"""

import os
import threading
from broker import Broker
from logger import logger
from data_lake_uploader import DataLakeUploader

def run_broker():
    broker = Broker()
    logger.info(f"Tópicos configurados ({len(broker.mqtt_topics)}):")
    for i, topic in enumerate(broker.mqtt_topics, 1):
        logger.info(f"  {i:2d}. {topic}")
    broker.run()

def run_uploader():
    log_dir = os.getenv('LOG_DIRECTORY', './logs')
    uploader = DataLakeUploader(log_directory=log_dir)
    uploader.run()

def main():
    logger.info("Iniciando MQTT Logger e DataLakeUploader em threads...")
    logger.info("Configurações:")
    logger.info(f"  Broker: {os.getenv('MQTT_BROKER', 'localhost')}")
    logger.info(f"  Porta: {os.getenv('MQTT_PORT', '1883')}")
    logger.info(f"  Diretório de logs: {os.getenv('LOG_DIRECTORY', './logs')}")
    logger.info(f"  Intervalo de rotação: {os.getenv('LOG_INTERVAL_MINUTES', '10')} minutos")

    t1 = threading.Thread(target=run_broker)
    t2 = threading.Thread(target=run_uploader)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()
