import os
import time
import logging
import re
from data_lake_functions import process_csv_to_iceberg_complete
from variables import motor_pumps

class DataLakeUploader:
    def __init__(self, log_directory, interval=120):
        self.log_directory = log_directory
        self.interval = interval
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info(f"Iniciando DataLakeUploader na pasta {self.log_directory}")
        while True:
            try:
                if not os.path.exists(self.log_directory):
                    self.logger.debug(f"Log directory does not exist yet: {self.log_directory}")
                    time.sleep(self.interval)
                    continue

                for folder in os.listdir(self.log_directory):
                    folder_path = os.path.join(self.log_directory, folder)
                    if not os.path.isdir(folder_path):
                        continue

                    self.logger.debug(f"Inspecting folder: {folder_path}")

                    for file in os.listdir(folder_path):
                        if not file.endswith('.csv'):
                            continue

                        file_path = os.path.join(folder_path, file)
                        try:
                            self.logger.info(f"Processing {file_path} to datalake...")
                            results = self._process_file(file_path)
                            if isinstance(results, dict) and results.get('success'):
                                try:
                                    os.remove(file_path)
                                    self.logger.info(f"Arquivo {file_path} enviado e removido.")
                                except Exception as e:
                                    self.logger.warning(f"Arquivo enviado mas não foi possível remover {file_path}: {e}")
                            else:
                                self.logger.error(f"Upload failed for {file_path}: {results}")
                        except Exception as e:
                            self.logger.error(f"Erro ao processar {file_path}: {e}")

            except Exception as e:
                self.logger.error(f"Erro no loop do uploader: {e}")

            time.sleep(self.interval)

    def _process_file(self, file_path: str) -> dict:
        """
        Process a CSV file: try to run the full pipeline if available, otherwise
        fall back to moving the file into a local minio_data folder for testing.
        Returns a dict with at least 'success': bool
        """
        if process_csv_to_iceberg_complete:
            try:
                # detect raw marker in filename and pass explicit flag
                filename = os.path.basename(file_path)
                is_raw = bool(re.search(r'raw', filename, re.IGNORECASE))
                return process_csv_to_iceberg_complete(csv_file_path=file_path, debug=False, is_raw=is_raw)
            except Exception as e:
                self.logger.error(f"Pipeline processing failed for {file_path}: {e}")
                return {'success': False, 'error': str(e)}

        try:
            filename = os.path.basename(file_path)
            machine = filename.split('_', 1)[0] if '_' in filename else 'unknown'

            dest_dir = os.path.join(os.getcwd(), 'minio_data', 'datalake', 'dados', machine)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, filename)
            
            os.replace(file_path, dest_path)
            self.logger.info(f"Fallback: moved {file_path} -> {dest_path}")
            return {'success': True, 'dest': dest_path}
        except Exception as e:
            self.logger.error(f"Fallback processing failed for {file_path}: {e}")
            return {'success': False, 'error': str(e)}
