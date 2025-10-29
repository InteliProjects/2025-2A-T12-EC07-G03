import paho.mqtt.client as mqtt
import os
import time
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from logger import Logger, logger
from variables import topics

class Broker:
    def __init__(self):
        # Carregar variáveis do arquivo .env
        load_dotenv()
        
        # Configurações das variáveis de ambiente
        self.mqtt_broker = os.getenv('HOST_IP', 'localhost')
        self.mqtt_port = int(os.getenv('HOST_PORT', '1883'))
        self.mqtt_username = os.getenv('MQTT_USERNAME')
        self.mqtt_password = os.getenv('MQTT_PASSWORD')
        self.log_directory = os.getenv('LOG_DIRECTORY', './logs')
        self.log_interval_minutes = float(os.getenv('LOG_INTERVAL_MINUTES', '10'))
        
        # Ler tópicos do arquivo topicos_dispositivos.txt
        self.mqtt_topics = topics if topics else ["#"]
        
        # Configurações internas
        self.current_log_file = None
        self.last_rotation = datetime.now()
        self.messages_buffer = []
        self.client = None
        self.is_running = False
        
        # Criar diretório de logs se não existir
        Path(self.log_directory).mkdir(parents=True, exist_ok=True)

        # Inicializar cliente MQTT
        self._setup_mqtt_client()

        # Inicializar e configurar logger (compartilhar referências de estado)
        self.logger = Logger()
        # injetar dependências/estado que Logger espera usar
        self.logger.log_directory = self.log_directory
        self.logger.log_interval_minutes = self.log_interval_minutes
        self.logger.messages_buffer = self.messages_buffer
        self.logger.current_log_file = self.current_log_file
        self.logger.last_rotation = self.last_rotation
        
    def _setup_mqtt_client(self):
        """Configura o cliente MQTT"""
        self.client = mqtt.Client()
        
        # Configurar callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # Configurar autenticação se fornecida
        if self.mqtt_username and self.mqtt_password:
            self.client.username_pw_set(self.mqtt_username, self.mqtt_password)
            
        # Configurar TLS se necessário
        if os.getenv('MQTT_TLS', 'false').lower() == 'true':
            self.client.tls_set()
            
    def _on_connect(self, client, userdata, flags, rc):
        """Callback chamado quando conecta ao broker MQTT"""
        if rc == 0:
            logger.info(f"Conectado ao broker MQTT {self.mqtt_broker}:{self.mqtt_port}")
            
            # Inscrever nos tópicos
            for topic in self.mqtt_topics:
                topic = topic.strip()
                if topic:
                    client.subscribe(topic)
                    logger.info(f"Inscrito no tópico: {topic}")
        else:
            logger.error(f"Falha na conexão MQTT com código: {rc}")
            
    def _on_message(self, client, userdata, msg):
        """Callback chamado quando uma mensagem é recebida"""
        try:
            # Verificar se precisa rotacionar o arquivo de log
            self.logger._check_rotation()
            
            # Preparar dados da mensagem
            message_data = {
                'timestamp': datetime.now().isoformat(),
                'topic': msg.topic,
                'payload': msg.payload.decode('utf-8') if msg.payload else '',
                'qos': msg.qos,
                'retain': msg.retain
            }    
                
            # Adicionar ao buffer
            self.messages_buffer.append(message_data)
            
                
            logger.info(f"Mensagem recebida do tópico {msg.topic}: {message_data['payload'][:100]}...")
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            
    def _on_disconnect(self, client, userdata, rc):
        """Callback chamado quando desconecta do broker MQTT"""
        if rc != 0:
            logger.warning(f"Desconexão inesperada do broker MQTT. Código: {rc}")
        else:
            logger.info("Desconectado do broker MQTT")
      
    def connect(self):
        """Conecta ao broker MQTT"""
        try:
            logger.info(f"Conectando ao broker MQTT {self.mqtt_broker}:{self.mqtt_port}")
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
            
            # Iniciar loop em thread separada
            self.is_running = True
            self.client.loop_start()
            
            logger.info("Cliente MQTT iniciado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao broker MQTT: {e}")
            raise
            
    def disconnect(self):
        """Desconecta do broker MQTT"""
        try:
            self.is_running = False
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()

            logger.info("Cliente MQTT desconectado")
            
        except Exception as e:
            logger.error(f"Erro ao desconectar: {e}")
            
    def run(self):
        """Executa o logger MQTT"""
        try:
            self.connect()
            
            # Manter o programa rodando
            while self.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Interrupção recebida, encerrando...")
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
        finally:
            self.disconnect()
