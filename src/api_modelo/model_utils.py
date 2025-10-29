import numpy as np
import pickle
import skfuzzy as fuzz
import pandas as pd
import os
import sys
from typing import Dict, Any, Tuple
import logging
import xgboost as xgb

logger = logging.getLogger(__name__)

# Lista padrão das features esperadas pelo FCM se o modelo não tiver nomes salvos
DEFAULT_FCM_FEATURES = [
    'Auto', 'Bat_V', 'Char_V', 'Cool_T', 'Eng_RPM', 'Fuel_Con', 'Fuel_L', 'Man', 'Oil_L', 'Oil_P',
    'Recalque', 'Starts_N', 'Stop', 'Succao', 'running', 'minutes_running',
    'Bat_V_variation', 'Char_V_variation', 'Cool_T_variation', 'Eng_RPM_variation',
    'Fuel_Con_variation', 'Fuel_L_variation', 'Oil_L_variation', 'Oil_P_variation',
    'Bat_V_variation_percentage', 'Char_V_variation_percentage', 'Cool_T_variation_percentage',
    'Eng_RPM_variation_percentage', 'Fuel_Con_variation_percentage', 'Fuel_L_variation_percentage',
    'Oil_L_variation_percentage', 'Oil_P_variation_percentage',
    'Hydraulic_Head', 'Head_per_RPM',
    'OilP_per_RPM', 'CoolT_per_RPM', 'Fuel_rate'
]

## Garantir que o diretório 'src' esteja no PYTHONPATH para importar a pipeline corretamente
try:
    SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)
except Exception:
    pass

class FCMPredictor:
    def __init__(self, model_path: str = None):
        default_model_path = os.path.join(os.path.dirname(__file__), 'model', 'fcm_model.pkl')
        self.model_path = model_path or default_model_path
        self.centers = None
        self.m = None
        self.scaler = None
        self.pre_pca_scaler = None
        self.pca = None
        self.feature_names = None
        self.expected_features = None
        self.is_loaded = False
        
        try:
            self.load_model()
        except Exception as e:
            logger.warning(f"Não foi possível carregar o modelo automaticamente: {e}")
    
    def load_model(self) -> bool:
        try:
            if not os.path.exists(self.model_path):
                logger.error(f"Arquivo do modelo não encontrado: {self.model_path}")
                return False
            
            # Alguns modelos foram salvos referenciando o módulo 'pipeline_functions' no topo do projeto.
            # Fazemos um alias para garantir que o unpickle consiga resolver as referências.
            try:
                from data_cleaning_pipeline import pipeline_functions as pf
                import sys as _sys
                _sys.modules['pipeline_functions'] = pf
            except Exception:
                pass

            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)

            # Aceitar diferentes chaves usadas no salvamento do modelo
            if isinstance(model_data, dict):
                centers_key_candidates = ['centroids', 'centers', 'cluster_centers', 'cluster_centers_', 'centroids_']
                m_key_candidates = ['m', 'fuzziness', 'fuzziness_parameter']
                scaler_key_candidates = ['scaler', 'standard_scaler', 'scaler_']
                pca_key_candidates = ['pca_model', 'pca', 'pca_', 'pca_model_']
                feat_key_candidates = ['feature_names', 'features', 'columns', 'feature_list', 'original_feature_names']

                def pick(d, keys):
                    for k in keys:
                        if k in d:
                            return d[k]
                    return None

                self.centers = pick(model_data, centers_key_candidates)
                self.m = pick(model_data, m_key_candidates)
                self.scaler = pick(model_data, scaler_key_candidates)
                self.pca = pick(model_data, pca_key_candidates)
                feats = pick(model_data, feat_key_candidates)
                if isinstance(feats, (list, tuple)):
                    self.feature_names = [str(x) for x in feats]

                # Tentar extrair features diretamente da pipeline salva (generic_scaler.cols_to_scale)
                try:
                    pipeline_obj = model_data.get('pipeline')
                    if pipeline_obj is not None:
                        # sklearn Pipeline
                        named_steps = getattr(pipeline_obj, 'named_steps', {})
                        gen_scaler = named_steps.get('generic_scaler') if isinstance(named_steps, dict) else None
                        cols_to_scale = getattr(gen_scaler, 'cols_to_scale', None) if gen_scaler is not None else None
                        if isinstance(cols_to_scale, list) and len(cols_to_scale) > 0:
                            self.feature_names = [str(c) for c in cols_to_scale]
                except Exception:
                    pass

                # Detectar um RobustScaler salvo (pré-PCA) nos valores do dicionário
                try:
                    for _k, _v in model_data.items():
                        if type(_v).__name__ == 'RobustScaler':
                            self.pre_pca_scaler = _v
                            break
                except Exception:
                    pass

                # Normalizações
                if self.centers is not None:
                    self.centers = np.array(self.centers)
                
                if any(v is None for v in [self.centers, self.m, self.scaler, self.pca]):
                    available_keys = list(model_data.keys())
                    logger.error(f"Chaves esperadas não encontradas no modelo FCM. Chaves disponíveis: {available_keys}")
                    self.is_loaded = False
                    return False
            else:
                logger.error("Formato do arquivo de modelo FCM inesperado. Esperado dict.")
                self.is_loaded = False
                return False
            
            # Determinar lista de features esperadas (prioriza o scaler pré-PCA, depois scaler padrão, depois defaults)
            try:
                if self.pre_pca_scaler is not None and hasattr(self.pre_pca_scaler, 'feature_names_in_'):
                    self.expected_features = [str(c) for c in list(self.pre_pca_scaler.feature_names_in_)]
            except Exception:
                self.expected_features = None

            if self.expected_features is None:
                try:
                    if hasattr(self.scaler, 'feature_names_in_'):
                        self.expected_features = [str(c) for c in list(self.scaler.feature_names_in_)]
                except Exception:
                    self.expected_features = None

            if self.expected_features is None:
                self.expected_features = list(DEFAULT_FCM_FEATURES)

            self.is_loaded = True
            logger.info("Modelo FCM carregado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar o modelo: {e}")
            self.is_loaded = False
            return False
    
    def validate_input_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        if not isinstance(data, dict):
            return False, "Dados devem ser um dicionário"
        
        if 'data' not in data:
            return False, "Chave 'data' não encontrada no JSON"
        
        input_data = data['data']
        if not isinstance(input_data, dict):
            return False, "Campo 'data' deve ser um dicionário"

        # Sanitiza chaves com espaços/lixo e ignora entradas não numéricas simples
        clean_input = {}
        for k, v in input_data.items():
            if isinstance(k, str):
                key = k.strip()
            else:
                key = str(k)
            clean_input[key] = v
        input_data = clean_input
        
        # Usa nomes de features esperadas detectadas no load_model
        expected_features = list(self.expected_features) if self.expected_features is not None else None

        if expected_features is not None:
            # Não exige todas as features; as ausentes serão preenchidas com 0.
            # Apenas valida que as fornecidas (interseção) são numéricas.
            provided_expected = [k for k in expected_features if k in input_data]
            for key in provided_expected:
                if not isinstance(input_data[key], (int, float)):
                    return False, f"Feature '{key}' deve ser um número"
            return True, ""
        
        # Fallback: sem nomes, exige quantidade correta com tipos numéricos
        expected_n = getattr(self.scaler, 'n_features_in_', 37)
        if len(input_data) != expected_n:
            return False, f"Esperado {expected_n} features, mas recebido {len(input_data)}"
        for key, value in input_data.items():
            if not isinstance(value, (int, float)):
                return False, f"Feature '{key}' deve ser um número"
        return True, ""
    
    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_loaded:
            raise RuntimeError("Modelo não foi carregado. Execute load_model() primeiro.")
        
        is_valid, error_msg = self.validate_input_data(data)
        if not is_valid:
            raise ValueError(error_msg)
        
        try:
            df_input = pd.DataFrame([data['data']])

            # Seleciona e ordena as colunas exatamente como no treino
            feature_order = list(self.expected_features)
            for col in feature_order:
                if col not in df_input.columns:
                    df_input[col] = 0
            df_input = df_input[feature_order]
            
            numeric_cols = df_input.select_dtypes(include=[np.number]).columns
            X_sample = df_input[numeric_cols].values
            
            X_scaled = self.scaler.transform(X_sample)
            
            X_pca = self.pca.transform(X_scaled)
            
            X_pca_t = X_pca.T 
            
            u = fuzz.cluster.cmeans_predict(X_pca_t, self.centers, self.m, error=1e-5, maxiter=300)
            u = u[0]
            
            label = np.argmax(u, axis=0)[0] + 1
            
            confidence = float(u[label-1, 0])
            
            result = {
                'status': 'success',
                'prediction': {
                    'cluster': int(label),
                    'confidence': confidence,
                    'memberships': {
                        f'cluster_{i+1}': float(u[i, 0]) 
                        for i in range(u.shape[0])
                    }
                },
                'model_info': {
                    'num_clusters': int(self.centers.shape[0]),
                    'fuzziness_parameter': float(self.m),
                    'input_features': len(numeric_cols)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erro durante a predição: {e}")
            raise RuntimeError(f"Erro durante a predição: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        if not self.is_loaded:
            return {
                'model_loaded': False,
                'error': 'Modelo não foi carregado'
            }
        
        return {
            'model_loaded': True,
            'model_path': self.model_path,
            'num_clusters': int(self.centers.shape[0]),
            'num_features': int(self.centers.shape[1]),
            'fuzziness_parameter': float(self.m),
            'scaler_type': type(self.scaler).__name__,
            'pca_components': int(self.pca.n_components_),
        }

fcm_predictor = FCMPredictor()


class XGBPredictor:
    def __init__(self, model_path: str = None):
        default_model_path = os.path.join(os.path.dirname(__file__), 'model', 'xgb_best_model.pkl')
        self.model_path = model_path or default_model_path
        self.model = None
        self.feature_names = None
        self.expected_features = None
        self.is_loaded = False

        try:
            self.load_model()
        except Exception as e:
            logger.warning(f"Não foi possível carregar o modelo XGBoost automaticamente: {e}")

    def load_model(self) -> bool:
        try:
            model_path = self.model_path
            if not os.path.exists(model_path):
                # Tentativa de fallback para o caminho do notebook
                fallback_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'notebooks', 'xgboost', 'xgb_best_model.pkl'))
                if os.path.exists(fallback_path):
                    logger.warning(f"Modelo XGBoost não encontrado em '{model_path}'. Usando fallback: '{fallback_path}'")
                    model_path = fallback_path
                else:
                    logger.error(f"Arquivo do modelo XGBoost não encontrado: {self.model_path}")
                    return False

            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)

            # Tenta extrair nomes de features do modelo treinado
            self.feature_names = None
            try:
                if hasattr(self.model, 'feature_names_in_'):
                    self.feature_names = [str(x) for x in self.model.feature_names_in_]
                else:
                    booster = getattr(self.model, 'get_booster', lambda: None)()
                    if booster is not None and getattr(booster, 'feature_names', None):
                        self.feature_names = list(booster.feature_names)
            except Exception:
                pass

            # Define expected feature order for inference
            self.expected_features = list(self.feature_names) if self.feature_names is not None else None

            self.is_loaded = True
            logger.info("Modelo XGBoost carregado com sucesso!")
            return True

        except Exception as e:
            logger.error(f"Erro ao carregar o modelo XGBoost: {e}")
            self.is_loaded = False
            return False

    def validate_input_data(self, data: Dict[str, Any]) -> Tuple[bool, str, pd.DataFrame]:
        if not isinstance(data, dict):
            return False, "Dados devem ser um dicionário", None

        if 'data' not in data:
            return False, "Chave 'data' não encontrada no JSON", None

        input_data = data['data']
        if isinstance(input_data, dict):
            df_input = pd.DataFrame([input_data])
        elif isinstance(input_data, list):
            # lista de registros
            try:
                df_input = pd.DataFrame(input_data)
            except Exception:
                return False, "Campo 'data' deve ser um dicionário ou lista de dicionários", None
        else:
            return False, "Campo 'data' deve ser um dicionário ou lista de dicionários", None

        # Se o modelo souber os nomes das features, não exige todas: preenche faltantes no predict
        if self.expected_features is not None:
            # Apenas garante que as features presentes na interseção sejam numéricas
            for col in df_input.columns:
                if col in self.expected_features:
                    if not pd.api.types.is_numeric_dtype(type(df_input[col].iloc[0])):
                        return False, f"Feature '{col}' deve ser numérica", None
            # Ordem será tratada no predict
            pass

        # Garante que todas as colunas sejam numéricas
        try:
            df_input = df_input.apply(pd.to_numeric, errors='raise')
        except Exception:
            return False, "Todas as features devem ser numéricas", None

        return True, "", df_input

    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_loaded:
            raise RuntimeError("Modelo não foi carregado. Execute load_model() primeiro.")

        is_valid, error_msg, df_input = self.validate_input_data(data)
        if not is_valid:
            raise ValueError(error_msg)

        try:
            # Seleciona/Reordena/Preenche colunas conforme esperado pelo modelo
            if self.expected_features is not None:
                for col in self.expected_features:
                    if col not in df_input.columns:
                        df_input[col] = 0
                df_input = df_input[self.expected_features]

            y_proba = self.model.predict_proba(df_input)[:, 1]
            y_pred = (y_proba >= data.get('threshold', 0.5)).astype(int)

            result = {
                'status': 'success',
                'prediction': {
                    'labels': [int(v) for v in y_pred.tolist()],
                    'probabilities': [float(v) for v in y_proba.tolist()],
                    'threshold': float(data.get('threshold', 0.5))
                },
                'model_info': self.get_model_info()
            }
            return result

        except Exception as e:
            logger.error(f"Erro durante a predição XGBoost: {e}")
            raise RuntimeError(f"Erro durante a predição: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        info = {
            'model_loaded': bool(self.is_loaded),
            'model_path': self.model_path,
            'feature_names_available': self.feature_names is not None,
            'num_features': int(len(self.feature_names)) if self.feature_names is not None else None,
            'algorithm': 'XGBoost (XGBClassifier)'
        }

        # Tenta verificar import da pipeline do local correto (data_cleaning_pipeline)
        try:
            from data_cleaning_pipeline import pipeline_functions as pf
            pipeline_classes = [
                name for name in [
                    'AdjustTimestampColumn', 'RemoveDuplicatesAndNaN', 'TreatHighValues',
                    'PivotDataframe', 'CreateMinutesRunningColumn', 'CreateVariationsColumns',
                    'CreateHydraulicColumns', 'CreateMotorColumns', 'GenericScaler',
                    'RemoveZeroColumns', 'RemoveInfValues', 'CreateTargetVariable'
                ] if hasattr(pf, name)
            ]
            info.update({
                'pipeline_imported': True,
                'pipeline_available_steps': pipeline_classes
            })
        except Exception as e:
            info.update({
                'pipeline_imported': False,
                'pipeline_error': str(e)
            })

        return info


xgb_predictor = XGBPredictor()
