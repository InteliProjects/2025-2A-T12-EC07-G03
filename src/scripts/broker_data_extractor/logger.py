import logging
import csv
import os
from datetime import datetime
import json
from variables import motor_pumps

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Logger:
    """Lightweight logger responsible for writing raw and processed CSVs.

    This class expects the caller (Broker) to set these attributes after
    instantiation:
      - log_directory: str
      - log_interval_minutes: int
      - messages_buffer: list (shared reference)
      - last_rotation: datetime
      - current_log_file: optional holder
    """

    def _check_rotation(self):
        now = datetime.now()
        if (now - self.last_rotation).total_seconds() >= self.log_interval_minutes * 60:
            self._rotate_log_file()

    def _rotate_log_file(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.create_files_with_timestamp(timestamp)

    def create_files(self):
        return self.create_files_with_timestamp(None)

    def create_files_with_timestamp(self, timestamp: str = None):
        # Só cria arquivos se houver mensagens no buffer
        if not self.messages_buffer:
            logger.info("Nenhuma mensagem no buffer, arquivos de log não serão criados.")
            return None

        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        name = f"mqtt_log_{timestamp}"
        folderpath = os.path.join(self.log_directory, name)
        os.makedirs(folderpath, exist_ok=True)

        filepath_raw = os.path.join(folderpath, f"raw_{timestamp}.csv")
        motor_pumps_messages = {mp: [] for mp in motor_pumps}

        # Write raw log containing original messages (timestamp, topic, payload, qos, retain)
        try:
            self._write_csv(filepath_raw, self.messages_buffer, fieldnames=['timestamp', 'topic', 'payload', 'qos', 'retain'])
        except Exception as e:
            logger.warning(f"Falha ao salvar raw CSV em {filepath_raw}: {e}")

        # Process messages and group by motor_pump
        processed = self._process_messages(self.messages_buffer)

        for i, row in enumerate(processed):
            log = {
                'ID': i,
                'timestamp': row.get('timestamp', ''),
                'motor_pump': row.get('device', ''),
                'resource': row.get('sensor', ''),
                'value': row.get('value', ''),
            }

            motor_pump = row.get('device', '')
            if motor_pump:
                parts = motor_pump.split('/')
                normalized = parts[0]
            else:
                normalized = ''

            if normalized in motor_pumps:
                motor_pumps_messages[normalized].append(log)

        processed_fieldnames = ['ID', 'timestamp', 'motor_pump', 'resource', 'value']

        processed_files = []
        for motor_pump, msgs in motor_pumps_messages.items():
            if not msgs:
                continue
            filepath_processed = os.path.join(folderpath, f"{motor_pump}_{timestamp}.csv")
            self._write_csv(filepath_processed, msgs, fieldnames=processed_fieldnames)
            processed_files.append(filepath_processed)

        self.current_log_file = {'folder': folderpath, 'raw': filepath_raw, 'processed': processed_files}
        self.last_rotation = datetime.now()

        try:
            # clear the shared buffer reference
            self.messages_buffer.clear()
        except Exception:
            self.messages_buffer = []

        logger.info(f"Novo diretório de logs criado: {folderpath}")
        return self.current_log_file

    def _write_csv(self, filepath, data, fieldnames=None):
        if fieldnames is None:
            if data and isinstance(data[0], dict):
                fieldnames = list(data[0].keys())
            else:
                fieldnames = ['timestamp', 'device', 'motor_pump', 'resource', 'qos', 'retain']

        with open(filepath, "w", encoding="utf-8", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            if data:
                writer.writerows(data)

        logger.info(f"Salvas {len(data) if data else 0} mensagens em {filepath}")

    def _process_messages(self, messages):
        processed = []
        for msg in messages:
            try:
                topic_parts = msg['topic'].split('/')
                device = topic_parts[1] if len(topic_parts) > 1 else ''
                sensor = topic_parts[-1] if topic_parts else ''
                payload_dict = json.loads(msg['payload'].replace('""', '"'))
                device_id = list(payload_dict.keys())[0]
                p_code = list(payload_dict[device_id].keys())[0]
                r_code = list(payload_dict[device_id][p_code].keys())[0]
                value = payload_dict[device_id][p_code][r_code]
            except Exception:
                device, sensor, value = '', '', ''

            processed.append({
                'timestamp': msg['timestamp'],
                'device': device,
                'sensor': sensor,
                'value': value,
                'qos': msg.get('qos', ''),
                'retain': msg.get('retain', '')
            })
        return processed

    def _create_initial_log_file(self):
        self.create_files_with_timestamp(None)
