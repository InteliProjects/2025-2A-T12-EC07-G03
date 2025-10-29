# model_inference_gru.py
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Union

import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model

logger = logging.getLogger(__name__)

# =========================
# Constantes do seu treino
# =========================
TIME_STEPS = 60

# ORDEM EXATA usada no treino (todas as 8 features disponíveis)
EXPECTED_FEATURES = [
    "Eng_RPM", "Cool_T", "Oil_P", "Oil_L", "Recalque", "Succao", "Bat_V", "Char_V"
]

EXCLUDED_COLUMNS = {"timestamp", "motor_pump", "running", "target"}

TIME_COLUMN_CANDIDATES = ["timestamp", "time", "data_hora"]

DEFAULT_H5_PATH = os.getenv("GRU_MODEL_PATH", "models/nn_subsistemas_4heads.h5")
DEFAULT_SCALER_PATH = os.getenv("GRU_SCALER_PATH", "models/scaler_subs.pkl")


class GRULoader:
    """Carrega o modelo (.h5) e o scaler (.pkl)."""
    @staticmethod
    def load_keras_model(path: str = DEFAULT_H5_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(f"GRU model not found at: {path}")
        # compile=False para ignorar losses/metrics antigos
        model = load_model(path, compile=False)
        logger.info(f"GRU model loaded from: {path}")
        return model

    @staticmethod
    def load_scaler(path: str = DEFAULT_SCALER_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Scaler not found at: {path}")
        scaler = joblib.load(path)
        logger.info(f"Scaler loaded from: {path}")
        return scaler


class GRUDataProcessor:
    """Transforma payload (DF/JSON/sequence) em X (1,60,N) escalado."""
    def __init__(self, expected_features: List[str], scaler: Any):
        self.expected = expected_features
        self.scaler = scaler
        
        # Detecta quantas features o scaler/modelo espera
        self.scaler_n_features = getattr(scaler, "n_features_in_", None)
        
        # Se o scaler tem feature_names_in_, usa elas; senão, pega as primeiras N features
        if hasattr(scaler, "feature_names_in_"):
            self.model_features = list(scaler.feature_names_in_)
            logger.info(f"Modelo espera features: {self.model_features}")
        elif self.scaler_n_features is not None:
            # Pega as primeiras N features de EXPECTED_FEATURES
            self.model_features = expected_features[:self.scaler_n_features]
            logger.info(f"Modelo espera {self.scaler_n_features} features (sem nomes): usando {self.model_features}")
        else:
            # Fallback: assume que usa todas
            self.model_features = expected_features
            logger.warning("Não foi possível detectar features do scaler, usando todas")
        
        self.n_model_features = len(self.model_features)
        logger.info(f"Número de features para o modelo: {self.n_model_features}")

    def _parse_df(self, payload: Union[str, Dict, List, pd.DataFrame]) -> pd.DataFrame:
        if isinstance(payload, pd.DataFrame):
            return payload.copy()
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload
        if isinstance(data, dict):
            data = [data]
        return pd.DataFrame(data)

    def _sort_by_time(self, df: pd.DataFrame) -> pd.DataFrame:
        for c in TIME_COLUMN_CANDIDATES:
            if c in df.columns:
                df = df.copy()
                df[c] = pd.to_datetime(df[c], errors="coerce")
                return df.sort_values(c).reset_index(drop=True)
        return df.reset_index(drop=True)

    def _clean_align(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpa e alinha para as features que o MODELO precisa."""
        df = df.drop(columns=[c for c in df.columns if c in EXCLUDED_COLUMNS], errors="ignore").copy()
        
        # Garante que todas as features esperadas existem
        missing = set(self.expected) - set(df.columns)
        for m in missing:
            df[m] = 0.0
        
        # Seleciona apenas as features que o modelo usa
        df = df[self.model_features]
        
        # Converte para numérico
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        
        return df

    def _window_from_df(self, df: pd.DataFrame) -> np.ndarray:
        df = self._sort_by_time(df)
        df = self._clean_align(df)
        
        # Agora df tem apenas as N features que o modelo precisa
        X_scaled = self.scaler.transform(df.values)  # (n_rows, N)

        if X_scaled.shape[0] >= TIME_STEPS:
            win = X_scaled[-TIME_STEPS:, :]
        else:
            # padding no início com a 1ª linha escalada (ou zeros se vazio)
            base = X_scaled[[0], :] if X_scaled.shape[0] > 0 else np.zeros((1, self.n_model_features))
            pad = np.repeat(base, TIME_STEPS - X_scaled.shape[0], axis=0)
            win = np.vstack([pad, X_scaled])

        return win.reshape(1, TIME_STEPS, self.n_model_features)

    def _window_from_sequence(self, seq: Union[List[List[float]], np.ndarray]) -> np.ndarray:
        arr = np.asarray(seq, dtype=float)  # (T, ?) esperado
        
        # Se a sequência tem mais features que o modelo precisa, seleciona apenas as necessárias
        if arr.shape[1] > self.n_model_features:
            # Assume que as features estão na ordem de EXPECTED_FEATURES
            model_indices = [self.expected.index(feat) for feat in self.model_features]
            arr = arr[:, model_indices]
        
        if arr.ndim != 2 or arr.shape[1] != self.n_model_features:
            raise ValueError(f"sequence shape inválido: {arr.shape}, esperado (*, {self.n_model_features})")
        
        arr_scaled = self.scaler.transform(arr)
        
        if arr_scaled.shape[0] > TIME_STEPS:
            arr_scaled = arr_scaled[-TIME_STEPS:, :]
        elif arr_scaled.shape[0] < TIME_STEPS:
            base = arr_scaled[[0], :] if arr_scaled.shape[0] > 0 else np.zeros((1, self.n_model_features))
            pad = np.repeat(base, TIME_STEPS - arr_scaled.shape[0], axis=0)
            arr_scaled = np.vstack([pad, arr_scaled])
        
        return arr_scaled.reshape(1, TIME_STEPS, self.n_model_features)

    def to_window(self, payload: Union[str, Dict, List, pd.DataFrame]) -> np.ndarray:
        # Também aceita payload já como sequence T×N: {"sequence": [[...]*N, ...]}
        if isinstance(payload, dict) and "sequence" in payload:
            return self._window_from_sequence(payload["sequence"])
        df = self._parse_df(payload)
        return self._window_from_df(df)


class GRUInference:
    """
    Carrega artefatos e expõe:
      - get_model_info()
      - predict_health_indices(payload)
    """
    def __init__(self,
                 model_path: str = DEFAULT_H5_PATH,
                 scaler_path: str = DEFAULT_SCALER_PATH):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model = GRULoader.load_keras_model(model_path)
        self.scaler = GRULoader.load_scaler(scaler_path)
        
        # Detecta o número de features do modelo
        self.n_model_features = getattr(self.scaler, "n_features_in_", None)
        if self.n_model_features:
            logger.info(f"Modelo configurado para {self.n_model_features} features")
        
        # Detecta o número de saídas do modelo
        out_shape = getattr(self.model, "output_shape", None)
        if isinstance(out_shape, tuple) and len(out_shape) >= 2:
            self.n_outputs = out_shape[-1] if out_shape[-1] is not None else 1
        else:
            self.n_outputs = 1
        logger.info(f"Modelo configurado para {self.n_outputs} saída(s)")

    def get_model_info(self) -> Dict[str, Any]:
        """Retorna metadados úteis (timesteps/n_features inferidos do input_shape)."""
        try:
            in_shape = getattr(self.model, "input_shape", None)  # (None, T, F)
            out_shape = getattr(self.model, "output_shape", None)
            timesteps = None
            n_features = None
            if isinstance(in_shape, tuple) and len(in_shape) == 3:
                _, timesteps, n_features = in_shape

            # Detecta features do scaler
            scaler_features = None
            if hasattr(self.scaler, "feature_names_in_"):
                scaler_features = list(self.scaler.feature_names_in_)
            elif self.n_model_features:
                scaler_features = EXPECTED_FEATURES[:self.n_model_features]

            info = {
                "model_type": type(self.model).__name__,
                "library": "tensorflow.keras",
                "input_shape": in_shape,
                "output_shape": out_shape,
                "timesteps": timesteps,
                "n_features": n_features,
                "n_outputs": self.n_outputs,
                "file_size_mb": round(os.path.getsize(self.model_path) / (1024*1024), 2),
                "last_modified": datetime.fromtimestamp(
                    os.path.getmtime(self.model_path)
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "scaler_class": type(self.scaler).__name__,
                "scaler_has_feature_names": hasattr(self.scaler, "feature_names_in_"),
                "scaler_n_features_in": getattr(self.scaler, "n_features_in_", None),
                "model_features_used": scaler_features,
                "all_available_features": EXPECTED_FEATURES,
            }
            return info
        except Exception as e:
            logger.error(f"get_model_info error: {e}", exc_info=True)
            return {"error": str(e)}

    # ---------- Inferência ----------
    def _processor(self) -> GRUDataProcessor:
        return GRUDataProcessor(EXPECTED_FEATURES, self.scaler)

    @staticmethod
    def _bucket(v: float) -> str:
        if v < 40: return "ALERTA"
        if v < 70: return "ATENÇÃO"
        return "OK"

    def predict_health_indices(self, payload: Union[str, Dict, List, pd.DataFrame]) -> Dict[str, Any]:
        """
        Retorna índices de saúde (0–100).
        Suporta modelos com 1 ou 2 saídas.
        """
        try:
            processor = self._processor()
            X = processor.to_window(payload)   # (1,60,N) onde N é o número de features do modelo
            
            logger.info(f"Shape do input para o modelo: {X.shape}")
            
            y = self.model.predict(X, verbose=0)
            logger.info(f"Shape da saída do modelo: {y.shape}")
            
            # Flatten para garantir que temos um array 1D
            y_flat = y.flatten()
            
            include_raw = os.getenv("GRU_DEBUG_RAW", "0") == "1"
            
            # Adapta a resposta baseado no número de saídas
            if len(y_flat) == 1:
                # Modelo com 1 saída (índice geral de saúde)
                raw_health = float(y_flat[0])
                idx_health = float(np.clip(y_flat[0], 0.0, 100.0))
                
                resp = {
                    "success": True,
                    "indices": {
                        "saude_geral": round(idx_health, 2),
                    },
                    "status": {
                        "saude_geral": self._bucket(idx_health),
                    },
                    "meta": {
                        "timesteps": TIME_STEPS,
                        "n_features": processor.n_model_features,
                        "feature_order": processor.model_features,
                        "n_outputs": 1,
                    }
                }
                if include_raw:
                    resp["debug_raw_outputs"] = {
                        "saude_geral": raw_health,
                    }
            
            elif len(y_flat) == 2:
                # Modelo com 2 saídas (lubrificação e hidráulico)
                raw_lub = float(y_flat[0])
                raw_hid = float(y_flat[1])
                
                idx_lub = float(np.clip(y_flat[0], 0.0, 100.0))
                idx_hid = float(np.clip(y_flat[1], 0.0, 100.0))
                
                resp = {
                    "success": True,
                    "indices": {
                        "lubrificacao": round(idx_lub, 2),
                        "hidraulico": round(idx_hid, 2),
                    },
                    "status": {
                        "lubrificacao": self._bucket(idx_lub),
                        "hidraulico": self._bucket(idx_hid),
                    },
                    "meta": {
                        "timesteps": TIME_STEPS,
                        "n_features": processor.n_model_features,
                        "feature_order": processor.model_features,
                        "n_outputs": 2,
                    }
                }
                if include_raw:
                    resp["debug_raw_outputs"] = {
                        "lubrificacao": raw_lub,
                        "hidraulico": raw_hid,
                    }
            
            else:
                # Modelo com N saídas (genérico)
                indices = {}
                status = {}
                raw_outputs = {}
                
                for i, val in enumerate(y_flat):
                    raw_val = float(val)
                    clipped_val = float(np.clip(val, 0.0, 100.0))
                    key = f"indice_{i+1}"
                    
                    indices[key] = round(clipped_val, 2)
                    status[key] = self._bucket(clipped_val)
                    if include_raw:
                        raw_outputs[key] = raw_val
                
                resp = {
                    "success": True,
                    "indices": indices,
                    "status": status,
                    "meta": {
                        "timesteps": TIME_STEPS,
                        "n_features": processor.n_model_features,
                        "feature_order": processor.model_features,
                        "n_outputs": len(y_flat),
                    }
                }
                if include_raw:
                    resp["debug_raw_outputs"] = raw_outputs
            
            return resp
            
        except Exception as e:
            logger.error(f"predict_health_indices error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}