import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, recall_score
import pickle
import minio
import logging
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

# Imports para GRU
import tensorflow as tf
from tensorflow import keras
from keras.models import Sequential
from keras.layers import GRU, Dense, Dropout
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
from keras.optimizers import Adam

class ModelFactory:
    
    def __init__(self, minio_config, engine):
        self.minio_config = minio_config
        self.engine = engine
        self.RPM_DROP_THRESHOLD_PERCENTAGE = -70.0
        self.PRE_FAILURE_WINDOW_MINUTES = 30
        
        # Configurações para GRU
        self.SEQUENCE_LENGTH = 60  # 60 timesteps (5 minutos se dados são de 5s)
        self.HEALTH_FEATURES = [
            'Oil_P', 'Oil_L', 'Recalque', 'Succao',
            'Eng_RPM', 'Oil_T', 'Fuel_T', 'Cool_T',
            'Bateria', 'Intake', 'Exaust'
        ]
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("ModelFactory inicializada com sucesso")

    def _prepare_data(self, machine_name, start_date, end_date, model_type):
        """Prepara os dados para treinamento"""
        self.logger.info(f"Iniciando preparação de dados para máquina {machine_name}")
        self.logger.info(f"Período: {start_date} até {end_date}")
        
        query = f"""SELECT * FROM processed_data WHERE motor_pump = '{machine_name}'
                    AND timestamp >= '{start_date}' AND timestamp <= '{end_date}'
                    ORDER BY timestamp ASC;"""
        
        try:
            df = pd.read_sql_query(query, con=self.engine)
            self.logger.info(f"Dados carregados com sucesso: {len(df)} registros")
        except Exception as e:
            self.logger.error(f"Erro ao carregar dados: {e}")
            raise
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Converter todas as colunas numéricas para float
        for col in df.columns:
            if col not in ['timestamp', 'motor_pump', 'id']:
                df[col] = df[col].astype(float)
        
        # Substituir valores infinitos e maiores que 20000 por NaN (depois tratamos)
        for col in df.columns:
            if col not in ['timestamp', 'motor_pump', 'id']:
                df[col] = df[col].replace([np.inf, -np.inf], np.nan)
                df.loc[df[col] > 20000, col] = np.nan
                df.loc[df[col] < -20000, col] = np.nan

        self.logger.info("Todas as colunas numéricas convertidas para float")

        if model_type == "xgb":
            df = df.drop(columns=['FlexAnalogue4_1', 'FlexAnalogue4_2', 'id'])
            self.logger.info("Colunas desnecessárias removidas")

            # Criar labels de falha
            df['failure_label'] = 0
            failure_events = df[df['Eng_RPM_variation_percentage'] <= self.RPM_DROP_THRESHOLD_PERCENTAGE]
            
            if not failure_events.empty:
                self.logger.info(f"Encontrados {len(failure_events)} eventos de falha")
                for index, event_row in failure_events.iterrows():
                    failure_timestamp = event_row['timestamp']
                    window_start_timestamp = failure_timestamp - pd.Timedelta(minutes=self.PRE_FAILURE_WINDOW_MINUTES)
                    window_mask = (df['timestamp'] >= window_start_timestamp) & (df['timestamp'] < failure_timestamp)
                    df.loc[window_mask, 'failure_label'] = 1
                
                failure_count = df['failure_label'].sum()
                self.logger.info(f"Labels de falha criados: {failure_count} registros marcados como pré-falha")
            else:
                self.logger.warning("Nenhum evento de falha encontrado nos dados")
            
            self.logger.info("Preparação de dados concluída")
            return df
        
        elif model_type == "gru":
            # Preparação de dados para GRU - foco em health score
            self.logger.info("Preparando dados para modelo GRU (Health Score)")
            
            # NOVO: Mapear colunas FlexAnalogue para Recalque/Succao se necessário
            if 'Recalque' not in df.columns and 'FlexAnalogue4_1' in df.columns:
                self.logger.info("'Recalque' não encontrado, usando 'FlexAnalogue4_1' como substituto")
                df['Recalque'] = df['FlexAnalogue4_1']
            
            if 'Succao' not in df.columns and 'FlexAnalogue4_2' in df.columns:
                self.logger.info("'Succao' não encontrado, usando 'FlexAnalogue4_2' como substituto")
                df['Succao'] = df['FlexAnalogue4_2']
            
            # Remover colunas desnecessárias (agora que já mapeamos)
            df = df.drop(columns=['FlexAnalogue4_1', 'FlexAnalogue4_2', 'id'], errors='ignore')
            
            # LOG: Verificar dados antes do cálculo
            self.logger.info("=== DIAGNÓSTICO DE DADOS ===")
            for col in ['Oil_P', 'Oil_L', 'Recalque', 'Succao']:
                if col in df.columns:
                    non_null = df[col].notna().sum()
                    total = len(df)
                    pct_valid = (non_null / total) * 100
                    if non_null > 0:
                        self.logger.info(f"{col}: {non_null}/{total} válidos ({pct_valid:.1f}%) | "
                                       f"min={df[col].min():.2f}, max={df[col].max():.2f}, "
                                       f"mean={df[col].mean():.2f}")
                    else:
                        self.logger.warning(f"{col}: TODOS OS VALORES SÃO NaN!")
                else:
                    self.logger.warning(f"{col}: COLUNA NÃO EXISTE!")
            
            # Calcular health score baseado em múltiplos indicadores
            df['health_score'] = self._calculate_health_score(df)
            
            # Verificar health score resultante
            valid_health = df['health_score'].notna().sum()
            self.logger.info(f"Health score válido: {valid_health}/{len(df)} registros ({(valid_health/len(df)*100):.1f}%)")
            
            if valid_health == 0:
                raise ValueError("ERRO CRÍTICO: Todos os health scores são NaN! Verifique os dados de entrada.")
            
            # Selecionar apenas features relevantes para health
            available_features = [f for f in self.HEALTH_FEATURES if f in df.columns]
            self.logger.info(f"Features selecionadas para GRU: {available_features}")
            
            df_health = df[['timestamp', 'motor_pump'] + available_features + ['health_score']].copy()
            
            # Tratar valores NaN: forward fill -> backward fill -> 0
            for col in available_features + ['health_score']:
                if col in df_health.columns:
                    df_health[col] = df_health[col].fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            self.logger.info(f"Dados preparados para GRU: {len(df_health)} registros")
        return df_health
        
    def _calculate_health_score(self, df):
        """
        Calcula um health score baseado em subsistemas críticos da máquina
        VERSÃO ROBUSTA: Trata dados NaN e outliers de forma defensiva

        Score varia de 0 (pior saúde) a 100 (melhor saúde)

        Subsistemas avaliados:
        1. Lubrificação (Oil_P, Oil_L)
        2. Hidráulico (Recalque, Succao)
        """

        # Validação de colunas obrigatórias
        required_cols = ['Oil_P', 'Oil_L', 'Recalque', 'Succao']
        for col in required_cols:
            if col not in df.columns:
                self.logger.warning(f"Coluna ausente: {col}. Criando com zeros.")
                df[col] = 0.0

        # Converter explicitamente para float e tratar NaN
        for col in required_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        self.logger.info("Calculando health score por subsistemas")

        def clip01(x):
            """Clip entre 0 e 1, tratando NaN"""
            x = np.nan_to_num(x, nan=0.0)
            return np.clip(x, 0.0, 1.0)

        def robust_minmax(x, percentile_low=1, percentile_high=99):
            """
            Normaliza robustamente usando percentis
            Retorna array normalizado entre 0 e 1
            """
            x = np.array(x, dtype=float)

            # Remover NaN temporariamente para calcular percentis
            x_valid = x[~np.isnan(x)]

            if len(x_valid) == 0:
                self.logger.warning("Todos os valores são NaN, retornando zeros")
                return np.zeros_like(x)

            # Calcular limites usando percentis dos dados válidos
            lo = np.percentile(x_valid, percentile_low)
            hi = np.percentile(x_valid, percentile_high)

            # Evitar divisão por zero
            if hi - lo < 1e-9:
                self.logger.warning(f"Range muito pequeno (lo={lo:.2f}, hi={hi:.2f}), usando valores médios")
                return np.full_like(x, 0.5)

            # Normalizar
            x_norm = (x - lo) / (hi - lo)
            x_norm = clip01(x_norm)

            return x_norm

        # Extrair arrays
        oil_p = df['Oil_P'].values.astype(float)
        oil_l = df['Oil_L'].values.astype(float)
        rec = df['Recalque'].values.astype(float)
        suc = df['Succao'].values.astype(float)

        # === SUBSISTEMA 1: LUBRIFICAÇÃO ===
        oil_p_norm = robust_minmax(oil_p)
        oil_l_norm = robust_minmax(oil_l)
        health_lube = 100.0 * (0.6 * oil_p_norm + 0.4 * oil_l_norm)

        # === SUBSISTEMA 2: HIDRÁULICO ===
        # Recalque: quanto maior, melhor
        rec_norm = robust_minmax(rec)

        # Sucção: valores negativos, quanto menor em módulo, melhor
        # Transformar para que valores próximos de zero sejam melhores
        suc_abs = np.abs(suc)
        suc_norm = robust_minmax(-suc_abs)  # Inverte: valores próximos de 0 ficam altos

        health_hyd = 100.0 * (0.7 * rec_norm + 0.3 * suc_norm)

        # === HEALTH SCORE FINAL ===
        # Combinar subsistemas com pesos
        health_score = (
            0.50 * health_lube +  # Lubrificação: crítico
            0.50 * health_hyd     # Hidráulico: muito importante
        )

        # Garantir range [0, 100] e tratar NaN
        health_score = np.nan_to_num(health_score, nan=0.0)
        health_score = np.clip(health_score, 0.0, 100.0)

        # Estatísticas finais
        self.logger.info(f"Health score calculado - Média: {health_score.mean():.2f}, "
                        f"Min: {health_score.min():.2f}, Max: {health_score.max():.2f}")
        self.logger.info(f"  Lubrificação: mean={health_lube.mean():.2f}, std={health_lube.std():.2f}")
        self.logger.info(f"  Hidráulico: mean={health_hyd.mean():.2f}, std={health_hyd.std():.2f}")

        return health_score
    
    def _create_sequences(self, data, target, sequence_length):
        """
        Cria sequências temporais para treinamento do GRU
        
        Args:
            data: DataFrame com features
            target: Array com targets (health_score)
            sequence_length: Tamanho da sequência
        
        Returns:
            X_seq: Array 3D (samples, timesteps, features)
            y_seq: Array 1D (samples,)
        """
        self.logger.info(f"Criando sequências com tamanho {sequence_length}")
        
        X_seq = []
        y_seq = []
        
        for i in range(len(data) - sequence_length):
            X_seq.append(data[i:i + sequence_length])
            y_seq.append(target[i + sequence_length])
        
        X_seq = np.array(X_seq)
        y_seq = np.array(y_seq)
        
        self.logger.info(f"Sequências criadas - Shape: {X_seq.shape}")
        return X_seq, y_seq
    
    
    def _split_data(self, df, model_type="xgb"):
        """Divide os dados em treino e teste"""
        self.logger.info("Iniciando divisão dos dados em treino e teste")
        if model_type == "xgb":
            y = df['failure_label']
            X = df.drop(columns=['failure_label', 'timestamp', 'motor_pump'])
            
            split_point = int(len(df) * 0.8)
            X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
            y_train, y_test = y.iloc[:split_point], y.iloc[split_point:]
            
            self.logger.info(f"Dados divididos - Treino: {len(X_train)} registros, Teste: {len(X_test)} registros")
            self.logger.info(f"Distribuição de classes no treino - Normal: {(y_train == 0).sum()}, Falha: {(y_train == 1).sum()}")
            self.logger.info(f"Distribuição de classes no teste - Normal: {(y_test == 0).sum()}, Falha: {(y_test == 1).sum()}")
            
            return X_train, X_test, y_train, y_test
    
        elif model_type == "gru":
            # Para GRU, usar split temporal
            self.logger.info("Preparando dados para GRU (split temporal)")
            
            # Separar features e target
            feature_cols = [col for col in df.columns if col not in ['timestamp', 'motor_pump', 'health_score']]
            X = df[feature_cols].values
            y = df['health_score'].values
            
            # Normalizar features
            self.scaler = MinMaxScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Criar sequências
            X_seq, y_seq = self._create_sequences(X_scaled, y, self.SEQUENCE_LENGTH)
            
            # Split temporal (80/20)
            split_point = int(len(X_seq) * 0.8)
            X_train = X_seq[:split_point]
            X_test = X_seq[split_point:]
            y_train = y_seq[:split_point]
            y_test = y_seq[split_point:]
            
            self.logger.info(f"Dados divididos para GRU - Treino: {X_train.shape}, Teste: {X_test.shape}")
            self.logger.info(f"Health score - Treino média: {y_train.mean():.2f}, Teste média: {y_test.mean():.2f}")
            
            return X_train, X_test, y_train, y_test
    
    def _save_model_to_minio(self, model, machine_name, model_type):
        """Salva o modelo no MinIO"""
        self.logger.info(f"Iniciando salvamento do modelo {model_type} para máquina {machine_name}")
        timestamp = pd.Timestamp.now().strftime('%Y_%m_%d_%H_%M_%S')

        if model_type == "xgb":
            file_path = f"{model_type}_best_model.pkl"

            with open(file_path, "wb") as f:
                pickle.dump(model, f)

            self.logger.info(f"Modelo XGBoost serializado em {file_path}")

        elif model_type == "gru":
            # Nomes no formato: gru_model_weights_MACHINE_timestamp.h5
            weights_filename = f"{model_type}_model_weights_{machine_name}_{timestamp}.h5"
            model.save(weights_filename)

            # Salvar scaler com formato: gru_model_scaler_MACHINE_timestamp.pkl
            scaler_filename = f"{model_type}_model_scaler_{machine_name}_{timestamp}.pkl"
            with open(scaler_filename, "wb") as f:
                pickle.dump(self.scaler, f)

            self.logger.info(f"Modelo GRU e scaler serializados")

        try:
            client = minio.Minio(
                endpoint=self.minio_config['endpoint'],
                access_key=self.minio_config['access_key'],
                secret_key=self.minio_config['secret_key'],
                secure=False
            )

            bucket_name = "models"

            if model_type == "xgb":
                object_name = f"{model_type}_model_{machine_name}_{timestamp}.pkl"
                client.fput_object(bucket_name, object_name, file_path)
                os.remove(file_path)
                self.logger.info(f"Modelo XGBoost salvo no MinIO: {object_name}")
                return object_name

            elif model_type == "gru":
                # Upload do modelo weights
                weights_object_name = f"{model_type}_model_weights_{machine_name}_{timestamp}.h5"
                client.fput_object(bucket_name, weights_object_name, weights_filename)
                os.remove(weights_filename)
                self.logger.info(f"Modelo GRU salvo no MinIO: {weights_object_name}")

                # Upload do scaler
                scaler_object_name = f"{model_type}_model_scaler_{machine_name}_{timestamp}.pkl"
                client.fput_object(bucket_name, scaler_object_name, scaler_filename)
                os.remove(scaler_filename)
                self.logger.info(f"Scaler salvo no MinIO: {scaler_object_name}")

                # Retornar dict com ambos os caminhos para GRU
                return {
                    'weights': weights_object_name,
                    'scaler': scaler_object_name
                }

        except Exception as e:
            self.logger.error(f"Erro ao salvar modelo no MinIO: {e}")
            raise
    
    def _save_model_metadata(self, machine_name, bucket_address, start_date, end_date, metrics, model_type):
        """Salva os metadados do modelo na tabela models do PostgreSQL"""
        self.logger.info(f"Salvando metadados do modelo para máquina {machine_name} no banco de dados")

        try:
            # Converter métricas para JSON
            metrics_json = json.dumps(metrics)

            # Query de inserção
            insert_query = text("""
                INSERT INTO models (machine_name, bucket_address, data_start_date, data_end_date, metrics, model_type)
                VALUES (:machine_name, :bucket_address, :data_start_date, :data_end_date, :metrics, :model_type)
            """)

            # Executar inserção
            with self.engine.connect() as connection:
                # Converte para datetime se é string, se não use como é
                start_dt = datetime.strptime(start_date, '%Y-%m-%d') if isinstance(start_date, str) else start_date
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') if isinstance(end_date, str) else end_date
                
                if bucket_address.startswith("models/"):
                    bucket_address = bucket_address[len("models/"):]

                connection.execute(insert_query, {
                    'machine_name': machine_name,
                    'bucket_address': bucket_address,
                    'data_start_date': start_dt,
                    'data_end_date': end_dt,
                    'metrics': metrics_json,
                    'model_type': model_type
                })
                connection.commit()

            self.logger.info("Metadados do modelo salvos com sucesso no banco de dados")
            return bucket_address

        except SQLAlchemyError as e:
            self.logger.error(f"Erro ao salvar metadados do modelo no banco de dados: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erro inesperado ao salvar metadados: {e}")
            raise
    
    def train_xgboost(self, machine_name, start_date, end_date):
        """Treina um modelo XGBoost"""
        self.logger.info(f"Iniciando treinamento do modelo XGBoost para máquina {machine_name}")
        
        # Preparar dados
        df = self._prepare_data(machine_name, start_date, end_date, model_type="xgb")
        X_train, X_test, y_train, y_test = self._split_data(df)
        
        # Calcular peso para balanceamento de classes
        count_normal = y_train.value_counts()[0]
        count_pre_failure = y_train.value_counts()[1] if 1 in y_train.value_counts() else 1
        scale_pos_weight = count_normal / count_pre_failure if count_pre_failure != 0 else 1
        
        self.logger.info(f"Peso calculado para balanceamento de classes: {scale_pos_weight:.2f}")
        
        # Criar modelo base
        xgb_model = xgb.XGBClassifier(
            objective='binary:logistic',
            eval_metric='logloss',
            scale_pos_weight=scale_pos_weight,
            random_state=42
        )
        
        self.logger.info("Iniciando otimização de hiperparâmetros com GridSearchCV")
        
        # Grid search para otimização de hiperparâmetros
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [4, 6, 8],
            'learning_rate': [0.05, 0.1, 0.2],
            'subsample': [0.8, 1.0]
        }
        
        grid_search = GridSearchCV(
            estimator=xgb_model,
            param_grid=param_grid,
            scoring='recall',
            cv=3,
            verbose=1,
            n_jobs=-1
        )
        
        grid_search.fit(X_train, y_train)
        
        # Obter melhor modelo
        best_model = grid_search.best_estimator_
        self.logger.info(f"Melhores parâmetros encontrados: {grid_search.best_params_}")
        
        # Calcular métricas
        y_pred_best = best_model.predict(X_test)
        y_pred_proba_best = best_model.predict_proba(X_test)[:, 1]
        auc_best = roc_auc_score(y_test, y_pred_proba_best)
        
        self.logger.info(f"AUC Score do modelo: {auc_best:.4f}")
        self.logger.info("Relatório de Classificação:")
        self.logger.info(classification_report(y_test, y_pred_best))

        # Salvar modelo no MinIO
        model_path = self._save_model_to_minio(best_model, machine_name, "xgb")
        
        # Preparar métricas para salvar no banco
        metrics = {
            'auc_score': (float(auc_best) if not np.isnan(auc_best) else 0),
            'best_params': grid_search.best_params_,
            'classification_report': classification_report(y_test, y_pred_best, output_dict=True),
            'train_size': len(X_train),
            'test_size': len(X_test),
            'failure_events_train': int((y_train == 1).sum()),
            'failure_events_test': int((y_test == 1).sum())
        }
        
        # Salvar metadados do modelo no banco de dados
        bucket_addr = self._save_model_metadata(machine_name, f"models/{model_path}", start_date, end_date, metrics, "xgb")
        
        self.logger.info("Treinamento do modelo XGBoost concluído com sucesso")
        
        return {
            'model': best_model,
            'auc_score': auc_best,
            'model_path': model_path,
            'best_params': grid_search.best_params_,
            'bucket_address': bucket_addr,
        }
    
    def train_gru(self, machine_name, start_date, end_date):
        """Treina um modelo GRU para predição de health score"""
        self.logger.info(f"Iniciando treinamento do modelo GRU para máquina {machine_name}")

        # Preparar dados
        df = self._prepare_data(machine_name, start_date, end_date, model_type="gru")
        X_train, X_test, y_train, y_test = self._split_data(df, model_type="gru")

        # Construir modelo GRU
        self.logger.info("Construindo arquitetura do modelo GRU")

        model = Sequential([
            GRU(128, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])),
            Dropout(0.2),
            GRU(64, return_sequences=True),
            Dropout(0.2),
            GRU(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1)  # Saída: health score contínuo
        ])

        # Compilar modelo
        optimizer = Adam(learning_rate=0.001)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])

        self.logger.info("Modelo GRU compilado")
        model.summary(print_fn=lambda x: self.logger.info(x))

        # Callbacks
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=15,
            restore_best_weights=True,
            verbose=1
        )

        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=15,
            min_lr=1e-6,
            verbose=1
        )

        # Treinar modelo
        self.logger.info("Iniciando treinamento do GRU")

        history = model.fit(
            X_train, y_train,
            validation_split=0.2,
            epochs=100,
            batch_size=32,
            callbacks=[early_stopping, reduce_lr],
            verbose=1
        )

        # Avaliar modelo
        self.logger.info("Avaliando modelo GRU")

        y_pred = model.predict(X_test).flatten()

        from sklearn.metrics import mean_squared_error, mean_absolute_error

        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mse)

        # Calcular R²
        ss_res = np.sum((y_test - y_pred) ** 2)
        ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
        r2 = 1 - (ss_res / ss_tot)

        self.logger.info(f"Métricas do modelo GRU:")
        self.logger.info(f"  MSE: {mse:.4f}")
        self.logger.info(f"  MAE: {mae:.4f}")
        self.logger.info(f"  RMSE: {rmse:.4f}")
        self.logger.info(f"  R²: {r2:.4f}")

        # Salvar modelo no MinIO (retorna dict com 'weights' e 'scaler')
        model_paths = self._save_model_to_minio(model, machine_name, "gru")

        # Preparar métricas para salvar no banco
        metrics = {
            'mse': float(mse),
            'mae': float(mae),
            'rmse': float(rmse),
            'r2_score': float(r2),
            'train_size': int(len(X_train)),
            'test_size': int(len(X_test)),
            'sequence_length': int(self.SEQUENCE_LENGTH),
            'features_used': [f for f in self.HEALTH_FEATURES if f in df.columns],
            'epochs_trained': len(history.history['loss']),
            'final_train_loss': float(history.history['loss'][-1]),
            'final_val_loss': float(history.history['val_loss'][-1]),
            'health_score_mean_train': float(y_train.mean()),
            'health_score_mean_test': float(y_test.mean()),
            'health_score_std_train': float(y_train.std()),
            'health_score_std_test': float(y_test.std()),
            'scaler_path': model_paths['scaler']  # Adicionar caminho do scaler nas métricas
        }

        # Salvar metadados do modelo no banco de dados (apenas .h5)
        bucket_addr = self._save_model_metadata(
            machine_name, 
            f"models/{model_paths['weights']}",  # Salva apenas o caminho do .h5
            start_date, 
            end_date, 
            metrics,
            "gru"
        )

        self.logger.info("Treinamento do modelo GRU concluído com sucesso")

        result = {
            'model': model,
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'r2_score': r2,
            'weights_path': model_paths['weights'],
            'scaler_path': model_paths['scaler'],
            'bucket_address': bucket_addr,
        }

        print(result)

        return result
    
    def train_model(self, model_type, machine_name, start_date, end_date):
        """Método principal para treinar modelos"""
        if model_type.lower() == 'xgboost':
            return self.train_xgboost(machine_name, start_date, end_date)
        elif model_type.lower() == 'gru':
            return self.train_gru(machine_name, start_date, end_date)
        else:
            raise ValueError(f"Tipo de modelo '{model_type}' não suportado. Use 'xgboost' ou 'gru'.")
