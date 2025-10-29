---
title: API de Predição
sidebar_label: API de Predição
sidebar_position: 3
---

Esta API tem como principal objetivo expor modelos de Machine Learning via HTTP (REST),
facilitando a integração direta com aplicações frontend e outros serviços. O backend
padroniza contratos de entrada/saída, centraliza o versionamento dos modelos e oferece
observabilidade mínima (health, status, info), reduzindo o acoplamento entre UI e ML.

Você pode explorar a documentação interativa via Swagger UI em `/apidocs`.

### Base URL

- Local: `http://localhost:5000/api`

### Autenticação

- Não requer autenticação nesta versão (ambiente acadêmico).

---

### Health Check
- Método: GET
- Rota: `/health`
- Resposta 200:
```
{
  "status": "healthy",
  "message": "API is running"
}
```

---

### FCM - Predict
- Método: POST
- Rota: `/predict`
- Body (exemplo):
```
{
  "data": { "feature_1": 0.1, "feature_2": 1.2, "...": 3.4 }
}
```
- Resposta 200 (exemplo):
```
{
  "status": "success",
  "prediction": {
    "cluster": 2,
    "confidence": 0.87,
    "memberships": { "cluster_1": 0.10, "cluster_2": 0.87, "cluster_3": 0.03 }
  },
  "model_info": { "num_clusters": 3, "fuzziness_parameter": 2.0, "input_features": 37 }
}
```

---

### FCM - Model Info
- Método: GET
- Rota: `/model/info`

---

### XGBoost - Predict
- Método: POST
- Rota: `/xgb/predict`
- Body (uma amostra ou várias):
```
{
  "threshold": 0.5,
  "data": {
    "Eng_RPM": 1500,
    "Succao": 10,
    "Recalque": 40
  }
}
```
ou
```
{
  "threshold": 0.4,
  "data": [
    { "Eng_RPM": 1500, "Succao": 10, "Recalque": 40 },
    { "Eng_RPM": 1600, "Succao": 11, "Recalque": 41 }
  ]
}
```
- Resposta 200 (exemplo):
```
{
  "status": "success",
  "prediction": {
    "labels": [0, 1],
    "probabilities": [0.21, 0.76],
    "threshold": 0.5
  },
  "model_info": { "algorithm": "XGBoost (XGBClassifier)", "num_features": 37 }
}
```

---

### XGBoost - Model Info
- Método: GET
- Rota: `/xgb/model/info`

---

### Execução Local
1. Criar venv e instalar dependências:
```
pip install -r src/api_modelo/requirements.txt
```
2. Subir a API:
```
python src/api_modelo/app.py
```
3. Acessar Swagger UI:
```
http://localhost:5000/apidocs

---

## Objetivos e Arquitetura

- Objetivo central: permitir consumo dos modelos (FCM e XGBoost) por HTTP com payloads JSON
  simples e previsíveis, prontos para chamada a partir de SPAs, mobile apps ou sistemas legados.
- Arquitetura: Flask + Blueprints por modelo (`/api/predict` para FCM, `/api/xgb/*` para XGBoost),
  com CORS habilitado e Swagger (Flasgger) para documentação.
- Padronização: todos os endpoints retornam JSON com `status`/`error` e dados estruturados.

Fluxo alto nível:
1. Frontend coleta os sinais (sensores/variáveis derivadas) do equipamento/telemetria.
2. Envia JSON para endpoint do modelo.
3. API aplica validação, normalização mínima e chama o modelo.
4. Resposta padronizada com `prediction` e metadados de modelo.

---

## Contratos de Payload e Boas Práticas

- `Content-Type: application/json` obrigatório.
- Para FCM: campo `data` deve conter um dicionário de features numéricas. Features ausentes
  são preenchidas com 0; extras são ignoradas. Recomendamos enviar ao menos os sinais brutos:
  `Auto, Bat_V, Char_V, Cool_T, Eng_RPM, Fuel_Con, Fuel_L, Man, Oil_L, Oil_P, Recalque, Starts_N, Stop, Succao, running, minutes_running`.
- Para XGBoost: aceita tanto o conjunto completo quanto um subconjunto; features ausentes
  também são preenchidas com 0. Permite lote via `data` como array de objetos.

Idempotência: requisições com o mesmo payload produzem as mesmas respostas (modelos estáticos).

Tamanhos: mantenha o corpo de cada requisição com até algumas centenas de registros por chamada
para respostas rápidas (<1s) dependendo do ambiente.

---

## Modelo de Erros (HTTP + JSON)

- 200 OK: requisição processada com sucesso.
- 400 Bad Request: problema de validação no payload (tipo não numérico, JSON inválido etc.).
- 503 Service Unavailable: modelo não carregado/indisponível no momento.
- 500 Internal Server Error: erro inesperado durante a inferência.


Formato de erro:
```json
{
  "error": "Invalid input data",
  "message": "Detalhes do erro"
}
```

Boas práticas de cliente:
- Validar JSON localmente antes de enviar.
- Tratar `400/503/500` com mensagens de usuário e lógica de retry/backoff quando apropriado.

---

## Versionamento e Ciclo de Vida do Modelo

- A API pode carregar novos modelos sem alterar os contratos HTTP.
- Recomenda-se usar headers ou query params futuros (ex.: `?model_version=v2`) para
  alternar entre versões quando necessário.
- Monitoramento: expor métricas de latência e taxa de erro na infraestrutura (fora do escopo deste doc).
- Retreinamento: manter artefatos `.pkl` com versionamento semântico e changelog interno.

---

## Integração no Frontend (Exemplos)

### Fetch (JavaScript/TypeScript)
```ts
async function predictXGB(sample: Record<string, number>) {
  const resp = await fetch('http://localhost:5000/api/xgb/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ threshold: 0.5, data: sample })
  });
  if (!resp.ok) throw new Error('Erro na API');
  return await resp.json();
}

async function predictFCM(sample: Record<string, number>) {
  const resp = await fetch('http://localhost:5000/api/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: sample })
  });
  if (!resp.ok) throw new Error('Erro na API');
  return await resp.json();
}
```

### Axios
```ts
import axios from 'axios';

export const xgbPredict = async (sample: Record<string, number>) => {
  const { data } = await axios.post('http://localhost:5000/api/xgb/predict', {
    threshold: 0.5,
    data: sample
  });
  return data;
};

export const fcmPredict = async (sample: Record<string, number>) => {
  const { data } = await axios.post('http://localhost:5000/api/predict', { data: sample });
  return data;
};
```

### Tratamento de Resposta no Front
- XGBoost: usar `prediction.probabilities` para desenhar gauge/risco e `labels` para status.
- FCM: usar `prediction.cluster` e `memberships` para exibir regime atual e confiança.

```



