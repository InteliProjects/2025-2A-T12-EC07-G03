"""
check.py — Verificação dos artefatos do GRU (modelo .h5 e scaler .pkl)

O que ele faz:
1) Confere se os arquivos existem (paths fixos ou via variáveis de ambiente).
2) Carrega o scaler (joblib) e imprime infos úteis.
3) Carrega o modelo Keras (.h5) com compile=False para ignorar losses/metrics antigas.
4) Mostra input_shape / output_shape e (se possível) a ativação da última camada.

Vars de ambiente (opcionais):
- GRU_MODEL_PATH  (default: models/nn_subsistemas_4heads.h5)
- GRU_SCALER_PATH (default: models/scaler_subs.pkl)
"""

import os
import warnings
import joblib
import numpy as np

# Silencia o warning de versão diferente do sklearn ao deserializar (opcional)
from sklearn.exceptions import InconsistentVersionWarning
warnings.filterwarnings("once", category=InconsistentVersionWarning)

from tensorflow.keras.models import load_model


# -----------------------------
# Paths (ambiente ou default)
# -----------------------------
DEFAULT_MODEL_PATH = "models/nn_subsistemas_4heads.h5"
DEFAULT_SCALER_PATH = "models/scaler_subs.pkl"

MODEL_PATH = os.getenv("GRU_MODEL_PATH", DEFAULT_MODEL_PATH)
SCALER_PATH = os.getenv("GRU_SCALER_PATH", DEFAULT_SCALER_PATH)


def main():
    print("Arquivos existem?")
    print("  scaler:", os.path.exists(SCALER_PATH), SCALER_PATH)
    print("  model :", os.path.exists(MODEL_PATH),  MODEL_PATH)

    # -----------------------------
    # Carrega e inspeciona o SCALER
    # -----------------------------
    scaler = None
    if os.path.exists(SCALER_PATH):
        try:
            scaler = joblib.load(SCALER_PATH)
            print("\n[SCALER]")
            print("classe:", type(scaler).__name__)
            print("tem .transform? ->", hasattr(scaler, "transform"))
            # Infos de features (se disponíveis)
            fn_in = getattr(scaler, "feature_names_in_", None)
            nf_in = getattr(scaler, "n_features_in_", None)
            print("tem feature_names_in_? ->", fn_in is not None)
            print("n_features_in_:", nf_in)
            if fn_in is not None:
                fn_in_list = list(fn_in)
                print("primeiras features:", fn_in_list[:min(8, len(fn_in_list))])
            # Se for Pipeline, mostra steps
            try:
                from sklearn.pipeline import Pipeline
                if isinstance(scaler, Pipeline):
                    print("Pipeline steps:", [name for name, _ in scaler.steps])
            except Exception:
                pass
        except Exception as e:
            print("\n[SCALER] ERRO ao carregar:", e)
    else:
        print("\n[SCALER] Arquivo não encontrado.")

    # -----------------------------
    # Carrega e inspeciona o MODELO KERAS
    # -----------------------------
    if os.path.exists(MODEL_PATH):
        try:
            print("\n[MODELO KERAS]")
            # compile=False para ignorar losses/metrics antigas (ex.: 'keras.metrics.mae')
            model = load_model(MODEL_PATH, compile=False)
            print("classe:", type(model).__name__)
            print("input_shape:", getattr(model, "input_shape", None))   # (None, T, F)
            print("output_shape:", getattr(model, "output_shape", None)) # (None, 1) ou (None, 2)

            # tenta inspecionar a última camada
            try:
                last = model.layers[-1]
                act = getattr(last, "activation", None)
                print("ultima camada:", type(last).__name__)
                if act:
                    print("ativacao da ultima camada:", getattr(act, "__name__", act))
            except Exception as e:
                print("nao consegui ler ativacao da ultima camada:", e)

            # dica: timesteps e n_features
            in_shape = getattr(model, "input_shape", None)
            if isinstance(in_shape, tuple) and len(in_shape) == 3:
                _, timesteps, n_features = in_shape
                print(f"timesteps inferido: {timesteps}")
                print(f"n_features inferido: {n_features}")
                if scaler is not None and hasattr(scaler, "n_features_in_"):
                    print(f"n_features do scaler: {scaler.n_features_in_}")
                    if isinstance(n_features, int) and isinstance(scaler.n_features_in_, (int, np.integer)):
                        if n_features != scaler.n_features_in_:
                            print("ATENÇÃO: n_features do modelo difere do scaler — verifique ordem/seleção de colunas.")
            else:
                print("Observação: input_shape não é triplo (batch, timesteps, n_features). Verifique se o modelo é realmente sequencial/GRU.")

        except Exception as e:
            print("\n[MODELO KERAS] ERRO ao carregar:", e)
            print("Dica: usar compile=False já está aplicado. Se persistir, pode haver camadas customizadas.")
    else:
        print("\n[MODELO KERAS] Arquivo não encontrado.")


if __name__ == "__main__":
    main()
