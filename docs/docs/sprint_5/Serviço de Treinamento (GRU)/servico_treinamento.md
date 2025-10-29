---
title: Serviço de Treinamento de Modelos
sidebar_label: Serviço de Treinamento
sidebar_position: 4
---

# Novas adições e modificações — Modelo GRU (Predição de Health Score)

## **1. Novo tipo de modelo**

Adicionado suporte ao tipo `"gru"` na `ModelFactory`, além do `"xgb"` já existente.

```python
if self.model_type == "xgb":
    self.train_xgboost()
elif self.model_type == "gru":
    self.train_gru()
```

---

## **2. Novo método `_prepare_data` (versão GRU)**

Implementa a preparação dos dados para previsão contínua do *health score*:

* Carrega dados de sensores (`processed_data`).
* Renomeia colunas `FlexAnalogue4_1` e `FlexAnalogue4_2` para `Recalque` e `Succao`, caso não existam.
* Calcula o *health score* com base em indicadores de **lubrificação** e **sistema hidráulico**:

  ```python
  health_lubrication = 0.5 * (Oil_P_norm + Oil_L_norm)
  health_hydraulic = 0.5 * (Recalque_norm + Succao_norm)
  health_score = 0.5 * health_lubrication + 0.5 * health_hydraulic
  ```
* Normaliza as features com `MinMaxScaler`.
* Retorna um `DataFrame` com `features` e `health_score`.

---

## **3. Novo método `_create_sequences`**

Cria janelas temporais de entrada no formato aceito pela GRU:

```python
def _create_sequences(data, sequence_length=60):
    X, y = [], []
    for i in range(len(data) - sequence_length):
        X.append(data[i:i + sequence_length, :-1])
        y.append(data[i + sequence_length, -1])
    return np.array(X), np.array(y)
```

---

## **4. Novo método `train_gru`**

Treina o modelo GRU para regressão contínua do *health score*.

**Principais etapas:**

* Divide dados em treino (80%) e teste (20%) respeitando a ordem temporal.
* Define arquitetura do modelo:

  ```python
  model = Sequential([
      GRU(64, return_sequences=True, input_shape=(timesteps, n_features)),
      Dropout(0.2),
      GRU(32),
      Dense(1)
  ])
  model.compile(optimizer='adam', loss='mse', metrics=['mae'])
  ```
* Treina com `EarlyStopping` e `ReduceLROnPlateau`.
* Avalia com **MAE**, **RMSE** e **R²**.
* Salva o modelo e *scaler* no MinIO:

  ```
  models/
  ├── gru_model_weights_MACHINE_TIMESTAMP.h5
  └── gru_model_scaler_MACHINE_TIMESTAMP.pkl
  ```
* Registra metadados no PostgreSQL (`model_type='gru'`).

---

## **5. Modificação no `_save_model_to_minio`**

Adaptação para suportar múltiplos formatos de artefato:

| Tipo  | Arquivos salvos          | Formato        |
| ----- | ------------------------ | -------------- |
| `xgb` | Modelo serializado       | `.pkl`         |
| `gru` | Pesos do modelo e scaler | `.h5` + `.pkl` |

---

## **6. Modificação no `_save_model_metadata`**

Inclusão do campo `model_type='gru'` e novas métricas de regressão no JSON de metadados:

```python
metrics = {
    "mae": mae_value,
    "rmse": rmse_value,
    "r2": r2_value
}
```

---

## **7. Novas dependências**

Adicionar ao ambiente:

```python
tensorflow
keras
scikit-learn
numpy
```
