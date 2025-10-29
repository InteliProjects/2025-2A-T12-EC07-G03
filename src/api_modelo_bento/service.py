from duckdb import query
import bentoml
from bentoml import api, service
from bentoml.models import BentoModel
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from bentoml.images import Image
import json

from minio import Minio
from minio.error import S3Error
import tempfile

import logging
from typing import Dict, Any
from model_inference_xgboost import ModelInference
from model_inference_gru import GRUInference, EXPECTED_FEATURES, TIME_STEPS
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(
    os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg2://admin:admin123@localhost:5435/SyncTelemetry"
    )
)

minio_config = {
            "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            "access_key": os.getenv("MINIO_ACCESS_KEY", "NUUVT0D4Q4XO1QI0BE37"),
            "secret_key": os.getenv("MINIO_SECRET_KEY", "4yOu7G4DwmikRWDA1+lKtj2jJKnTBiQ0AmluHkSY")
        }

# ======================
# Serviço BentoML
# ======================
@service(
    name="model_inference_service",
    image=Image(python_version="3.11").requirements_file("./requirements.txt"),
)
class ModelInferenceService:
    """
    Serviço BentoML para inferência de modelos.
    
    Estrutura de rotas:
        - /health -> Verifica se o serviço está ativo
        - /model/xgboost/predict -> Predição de falhas
        - /model/xgboost/info -> Informações sobre o modelo
        - /model/gru/predict               -> Índices de saúde (GRU)
        - /model/gru/info                  -> Informações do modelo GRU
        - /machine/predict                 -> Predição XGBoost com última linha do Postgres
        - /machine/gru/predict             -> Índices GRU com últimas N linhas do Postgres
    """

    def __init__(self):
        logger.info("Serviço inicializado.")

    # ======================
    # Health Check
    # ======================
    @api(route="/health")
    def health(self) -> Dict[str, Any]:
        """
        Endpoint para verificar se o serviço está ativo.
        """
        return {"status": "ok", "message": "Service is healthy"}

    # ======================
    # Predição com XGBoost
    # ======================
    @api(route="/model/xgboost/predict")
    def predict_xgboost(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Endpoint para realizar predição de falha usando XGBoost.
        """
        logger.info("Carregando modelo XGBoost para predição...")
        try:
            model_inference = ModelInference()
        except Exception as e:
            logger.error(f"Erro ao carregar o modelo: {e}", exc_info=True)
            return {"success": False, "error": f"Erro ao carregar o modelo: {e}"}

        try:
            input_df = pd.DataFrame([data])
            prediction_result = model_inference.predict_failure(input_df)
            return {"success": True, "result": prediction_result}
        except Exception as e:
            logger.error(f"Erro durante a predição: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    # ======================
    # Informações do modelo XGBoost
    # ======================
    @api(route="/model/xgboost/info")
    def model_info_xgboost(self) -> Dict[str, Any]:
        """
        Endpoint para obter informações do modelo XGBoost.
        """
        logger.info("Carregando modelo para obter informações...")
        try:
            model_inference = ModelInference()
            info = model_inference.get_model_info()
            return {"success": True, "model_info": info}
        except Exception as e:
            logger.error(f"Erro ao obter informações do modelo: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
        
    # ======================
    # GRU (índices de saúde)
    # ======================
    @api(route="/model/gru/info")
    def model_info_gru(self) -> Dict[str, Any]:
        """
        Metadados do GRU (input/output shape, timesteps, ordem das features, scaler).
        """
        logger.info("Carregando modelo GRU para obter informações...")
        try:
            mi = GRUInference()
            info = mi.get_model_info()
            return {"success": True, "model_info": info}
        except Exception as e:
            logger.error(f"Erro ao obter informações do modelo GRU: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
        
    @api(route="/model/gru/predict")
    def predict_gru(self, data: Any) -> Dict[str, Any]:
        """
        Inferência GRU diretamente do payload.

        Aceita:
           - JSON com 'sequence': [[... 8 cols ...], ...]  (T x 8)
           - JSON lista/dict estilo DataFrame, com colunas EXACTAS em EXPECTED_FEATURES

        O pré-processador interno:
          - ordena por timestamp, se existir;
          - alinha a ordem das colunas para EXPECTED_FEATURES;
          - aplica o scaler salvo;
          - recorta/pad para formar uma janela (1, 60, 8).
        """
        logger.info("Executando predição GRU a partir de payload JSON...")
        try:
            mi = GRUInference()
            result = mi.predict_health_indices(data)
            return result
        except Exception as e:
            logger.error(f"Erro durante a predição GRU: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    @api(route="/machine/gru/predict")
    def predict_machine_gru(self, machine_name: str, model_bucket_address: str, time_steps: int = TIME_STEPS) -> Dict[str, Any]:
        """
        Busca as últimas `time_steps` linhas para a máquina no Postgres e roda o GRU.

        Requisitos no banco:
            - tabela `processed_data` 
            - Colunas: timestamp, motor_pump, e as 8 features em EXPECTED_FEATURES
        """
        logger.info(f"Predição GRU para máquina={machine_name} (últimas {time_steps} linhas)...")
        try:
            quoted_features = [f'"{feature}"' for feature in EXPECTED_FEATURES]
            cols = ", ".join(["timestamp", "motor_pump"] + quoted_features)
            
            sql = f"""
                SELECT {cols}
                FROM processed_data
                WHERE motor_pump = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """
            df = pd.read_sql(sql, engine, params=(machine_name, time_steps))

            if df.empty:
                return {"success": False, "error": f"Nenhum dado encontrado para a máquina: {machine_name}"}
        
            if "timestamp" in df.columns:
                df = df.sort_values("timestamp").reset_index(drop=True)

            # Configurar cliente MinIO
            client = Minio(
                endpoint=minio_config["endpoint"],
                access_key=minio_config["access_key"],
                secret_key=minio_config["secret_key"],
                secure=False
            )

            model_weights_bucket_address = model_bucket_address
            model_scaler_bucket_address = model_bucket_address.replace("weights", "scaler").replace(".h5", ".pkl")

            logger.info(f"Baixando modelo: {model_weights_bucket_address}")
            logger.info(f"Baixando scaler: {model_scaler_bucket_address}")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".h5") as temp_weights_file:
                try:
                    client.fget_object(
                        bucket_name="models",
                        object_name=model_weights_bucket_address,
                        file_path=temp_weights_file.name
                    )
                    logger.info(f"Pesos do modelo baixados para: {temp_weights_file.name}")
                    weights_path = temp_weights_file.name
                except S3Error as e:
                    logger.error(f"Erro ao baixar pesos do MinIO: {e}", exc_info=True)
                    return {"success": False, "error": f"Erro ao baixar pesos do MinIO: {e}"}

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as temp_scaler_file:
                try:
                    client.fget_object(
                        bucket_name="models",
                        object_name=model_scaler_bucket_address,
                        file_path=temp_scaler_file.name
                    )
                    logger.info(f"Scaler baixado para: {temp_scaler_file.name}")
                    scaler_path = temp_scaler_file.name
                except S3Error as e:
                    logger.error(f"Erro ao baixar scaler do MinIO: {e}", exc_info=True)
                    return {"success": False, "error": f"Erro ao baixar scaler do MinIO: {e}"}

            mi = GRUInference(model_path=weights_path, scaler_path=scaler_path)
            result = mi.predict_health_indices(df)

            result.setdefault("meta", {})
            result["meta"].update({
                "machine": machine_name,
                "fetched_rows": int(len(df)),
                "feature_order": EXPECTED_FEATURES,
                "requested_time_steps": time_steps,
            })

            query = """
            INSERT INTO predictions (id, motor_pump, model_bucket_addres, timestamp, prediction, model_type)
            VALUES (gen_random_uuid(), :motor_pump, :model_bucket_addres, NOW(), :prediction, :model_type)
            """

            params = {
                "motor_pump": machine_name,
                "model_bucket_addres": model_bucket_address,
                "prediction": json.dumps(result),
                "model_type": "gru"
            }

            with engine.begin() as conn:
                conn.execute(text(query), params)

            return result

        except Exception as e:
            logger.error(f"Erro ao carregar o modelo GRU: {e}", exc_info=True)
            return {"success": False, "error": f"Erro ao carregar o modelo GRU: {e}"}


    @api(route="/machine/xgboost/predict")
    def predict_machine(self, machine_name: str, model_bucket_address: str) -> Dict[str, Any]:
        """
        Endpoint para realizar predição de falha em máquinas.
        """
        logger.info(f"Predição XGBoost para máquina={machine_name} com modelo {model_bucket_address}...")
        print(model_bucket_address)

        logger.info("Carregando modelo para predição de máquinas...")
        
        client = Minio(
                endpoint=minio_config["endpoint"],
                access_key=minio_config["access_key"],
                secret_key=minio_config["secret_key"],
                secure=False
            )

        with tempfile.NamedTemporaryFile() as temp_model_file:
                try:
                    client.fget_object(
                        bucket_name="models",
                        object_name=model_bucket_address,
                        file_path=temp_model_file.name
                    )
                    logger.info(f"Modelo baixado do MinIO para: {temp_model_file.name}")
                except S3Error as e:
                    logger.error(f"Erro ao baixar o modelo do MinIO: {e}", exc_info=True)
                    return {"success": False, "error": f"Erro ao baixar o modelo do MinIO: {e}"}

                model_bucket_address = temp_model_file.name
                logger.info(f"Usando modelo GRU em: {model_bucket_address}")

        try:
            model_inference = ModelInference()
        except Exception as e:
            logger.error(f"Erro ao carregar o modelo: {e}", exc_info=True)
            return {"success": False, "error": f"Erro ao carregar o modelo: {e}"}

        ## A lógica vai ser:
        ## Recebe o nome da máquina, procura o modelo específico daquela máquina
        ## pega a última linha no banco de dados daquela máquina
        ## faz a predição
        ## retorna se está saudável ou não

        query = """
                SELECT * 
                FROM processed_data 
                WHERE motor_pump = %s 
                ORDER BY timestamp DESC 
                LIMIT 1
                """

        df = pd.read_sql(query, engine, params=(machine_name,))
        if df.empty:
            return {"success": False, "error": f"Nenhum dado encontrado para a máquina: {machine_name}"}

         # Remove colunas desnecessárias
        df = df.drop(columns=['timestamp', 'motor_pump'])

        try:
            prediction_result = model_inference.predict_failure(df)

            query = """
            INSERT INTO predictions (id, motor_pump, model_bucket_addres, timestamp, prediction, model_type)
            VALUES (gen_random_uuid(), :motor_pump, :model_bucket_addres, NOW(), :prediction, :model_type)
            """

            params = {
                "motor_pump": machine_name,
                "model_bucket_addres": "ainda_não_implementado",
                "prediction": json.dumps(prediction_result),
                "model_type": "xgb"
            }

            with engine.begin() as conn:
                conn.execute(text(query), params)

            return {"success": True, "result": prediction_result}
        except Exception as e:
            logger.error(f"Erro durante a predição: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
