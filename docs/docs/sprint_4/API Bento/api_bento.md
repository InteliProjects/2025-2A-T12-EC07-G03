---
title: API de Inferência com BentoML
sidebar_label: API com BentoML
sidebar_position: 1
---

## 1. Visão Geral da API de Inferência

Para transformar os modelos de *Machine Learning* do projeto em uma solução funcional, foi desenvolvida uma API (Interface de Programação de Aplicações) de inferência. Esta API serve como a ponte entre os modelos preditivos treinados e os sistemas consumidores, permitindo a análise de dados em tempo real para prever falhas nas motobombas.

A tecnologia escolhida para esta tarefa foi o **BentoML**, um framework de código aberto projetado para simplificar o processo de empacotar, servir e gerenciar modelos de aprendizado de máquina em ambientes de produção.

## 2. Por que usar o BentoML?

A escolha do BentoML foi estratégica, visando agilidade, robustez e escalabilidade para a solução de IA da Itubombas. Os principais benefícios são:

*   **Empacotamento Padronizado:** O BentoML cria um "Bento", um pacote auto-contido que inclui o modelo treinado, o código de pré-processamento e todas as dependências de software. Isso garante consistência e reprodutibilidade em qualquer ambiente, do desenvolvimento à produção.
*   **Servidor de Inferência Otimizado:** Ele gera automaticamente um servidor de API de alto desempenho, com suporte nativo a processamento assíncrono e em lote (*batch processing*), maximizando a vazão de predições e reduzindo a latência.
*   **Implantação Simplificada (Deploy):** Com um único comando, o BentoML pode gerar uma imagem Docker para a API. Isso padroniza o processo de implantação em qualquer provedor de nuvem (AWS, Azure, GCP) ou em servidores locais (on-premises) usando orquestradores como Kubernetes.
*   **Gerenciamento Centralizado de Modelos:** Inclui um repositório local de modelos (*Model Store*) que ajuda a versionar e organizar os artefatos de modelo, facilitando o rastreamento e a governança.
*   **Escalabilidade Nativa:** A arquitetura do BentoML é projetada para escalar horizontalmente, permitindo que a solução cresça para atender a um volume crescente de dados e requisições sem a necessidade de grandes reestruturações.

## 3. Instalação e Execução Local

Para executar a API em um ambiente de desenvolvimento, siga os passos abaixo.

### Pré-requisitos

*   Python 3.11 ou superior
*   Git
*   Acesso a um banco de dados PostgreSQL (para o endpoint de máquina)

### Passos para Instalação

1.  **Clone o Repositório do Projeto:**
    ```bash
    git clone <url-do-seu-repositorio>
    cd <nome-do-repositorio>
    ```

2.  **Instale as Dependências:**
    O arquivo `requirements.txt` contém todas as bibliotecas Python necessárias. Crie um ambiente virtual e instale-as:
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configure a Variável de Ambiente do Banco de Dados:**
    A API precisa de acesso ao banco de dados para consultar os dados mais recentes de uma máquina. Exporte a `DATABASE_URL` no seu terminal:
    ```bash
    export DATABASE_URL="postgresql+psycopg2://admin:admin123@localhost:5434/SyncTelemetry"
    ```
    > **Nota:** Substitua os dados de conexão pelos do seu ambiente.

### Executando a API

1.  **Inicie o Servidor BentoML:**
    No diretório raiz do projeto (onde está o seu arquivo `service.py`), execute o seguinte comando:
    ```bash
    bentoml serve service:ModelInferenceService --reload
    ```
    *   `bentoml serve`: Comando principal para iniciar o servidor.
    *   `service:ModelInferenceService`: Aponta para o arquivo `service.py` e a classe `ModelInferenceService` que define a API.
    *   `--reload`: Um modo de desenvolvimento que reinicia o servidor automaticamente a cada alteração no código.

2.  **Acesse a Interface Interativa:**
    Após a inicialização, o servidor estará disponível em `http://localhost:3000`. Abra este endereço no seu navegador para acessar a interface do Swagger UI, onde é possível visualizar e testar todos os endpoints de forma interativa.

## 4. Detalhamento dos Endpoints

A API expõe rotas específicas para monitoramento, predição e obtenção de informações.

### `GET /health`

Verifica a saúde e a disponibilidade do serviço. É fundamental para sistemas de monitoramento e orquestradores (como Kubernetes ) saberem se a aplicação está funcionando corretamente.

**Exemplo de Requisição (`curl`):**
```bash
curl -X GET http://localhost:3000/health
```

**Exemplo de Resposta (Sucesso ):**
```json
{
  "status": "ok",
  "message": "Service is healthy"
}
```

---

### `POST /model/xgboost/predict`

Realiza uma predição de falha com base em um conjunto de dados de telemetria fornecido no corpo da requisição. Este endpoint é ideal para cenários de simulação ou para obter uma predição sob demanda com dados específicos.

**Exemplo de Requisição (`curl`):**
```bash
curl -X POST http://localhost:3000/model/xgboost/predict \
-H "Content-Type: application/json" \
-d '{
    "rotacao_motor_rpm": 1800,
    "pressao_oleo_bar": 4.5,
    "tensao_bateria_v": 24.1,
    "tensao_alternador_v": 27.8
}'
```

**Exemplo de Resposta (Sucesso ):**
```json
{
  "success": true,
  "result": {
    "prediction": "Operação Saudável",
    "probability": 0.05,
    "timestamp": "2025-09-27T13:30:00Z"
  }
}
```

**Exemplo de Resposta (Erro - Dados Inválidos):**
```json
{
  "success": false,
  "error": "Erro durante a predição: Colunas esperadas ['rotacao_motor_rpm', 'pressao_oleo_bar', ...] não encontradas."
}
```

---

### `POST /machine/predict`

Endpoint mais prático para a operação, pois recebe apenas o nome de uma máquina (`motor_pump`). A API se encarrega de buscar os dados telemétricos mais recentes dessa máquina diretamente no banco de dados, realizar a predição e retornar o resultado.

**Parâmetros da Requisição:**
*   `machine_name` (string, query param): O identificador único da máquina.

**Exemplo de Requisição (`curl`):**
```bash
curl -X POST "http://localhost:3000/machine/predict?machine_name=MOTOBOMBA-007"
```

**Exemplo de Resposta (Sucesso ):**
```json
{
  "success": true,
  "result": {
    "prediction": "Risco de Falha Iminente",
    "probability": 0.89,
    "timestamp": "2025-09-27T13:35:10Z"
  }
}
```

**Exemplo de Resposta (Erro - Máquina não encontrada):**
```json
{
  "success": false,
  "error": "Nenhum dado encontrado para a máquina: MOTOBOMBA-999"
}
```

---

### `GET /model/xgboost/info`

Fornece metadados sobre o modelo XGBoost em uso, como sua versão, data de criação e tags associadas. É útil para governança e para garantir que a versão correta do modelo está em produção.

**Exemplo de Requisição (`curl`):**
```bash
curl -X GET http://localhost:3000/model/xgboost/info
```

Esse endpoint irá retornar dados como nome do modelo, métricas, data de treinamento, funcionalidade e afins.

---
Além dos endpoints do modelo **XGBoost**, a API também expõe rotas para o modelo **GRU (Gated Recurrent Unit)**, responsável por calcular os índices de saúde de **Lubrificação** e **Hidráulico** das motobombas.


### `GET /model/gru/info`

Fornece metadados sobre o modelo GRU carregado, incluindo formato de entrada e saída, número de *time steps*, ordem das features e informações do scaler usado no pré-processamento.

**Exemplo de Requisição (`curl`):**

```bash
curl -X GET http://localhost:3000/model/gru/info
```
**Exemplo de Resposta:**

```json
{
  "success": true,
  "model_info": {
    "model_type": "Sequential",
    "library": "tensorflow.keras",
    "input_shape": [null, 60, 8],
    "output_shape": [null, 2],
    "timesteps": 60,
    "n_features": 8,
    "file_size_mb": 0.49,
    "last_modified": "2025-09-26 10:47:28",
    "scaler_class": "MinMaxScaler",
    "scaler_has_feature_names": false,
    "scaler_n_features_in": 8,
    "feature_order": [
      "Eng_RPM", "Cool_T", "Oil_P", "Oil_L",
      "Recalque", "Succao", "Bat_V", "Char_V"
    ]
  }
}
```
---
### `POST /model/gru/predict`

Executa a predição do modelo GRU diretamente a partir de um payload JSON fornecido na requisição.

**Exemplo de Requisição (`curl`):**

```bash
curl -X POST http://localhost:3000/model/gru/predict \
-H "Content-Type: application/json" \
-d '{
  "Eng_RPM": 0.07,
  "Cool_T": 80,
  "Oil_P": 3.2,
  "Oil_L": 7.8,
  "Recalque": 4.0,
  "Succao": 1.1,
  "Bat_V": 26.4,
  "Char_V": 27.2
}'
```
**Exemplo de Resposta:**

```json
{
  "success": true,
  "indices": { "lubrificacao": 73.32, "hidraulico": 65.50 },
  "status": { "lubrificacao": "OK", "hidraulico": "ATENÇÃO" },
  "meta": {
    "timesteps": 60,
    "n_features": 8,
    "feature_order": [
      "Eng_RPM", "Cool_T", "Oil_P", "Oil_L",
      "Recalque", "Succao", "Bat_V", "Char_V"
    ]
  }
}
```
---

### `POST /machine/gru/predict`

Esse endpoint busca automaticamente no banco de dados PostgreSQL os últimos registros de uma máquina específica e executa a predição GRU.

**Parâmetros da Requisição:**

- `machine_name` (string): Identificador da motobomba.
- `time_steps` (opcional, int, padrão=60): Quantidade de registros históricos a buscar.

**Exemplo de Requisição (`curl`):**

```bash
curl -X POST "http://localhost:3000/machine/gru/predict?machine_name=MOTOBOMBA-007&time_steps=60"
```

**Exemplo de Resposta:**

```json
{
  "success": true,
  "indices": { "lubrificacao": 75.10, "hidraulico": 68.40 },
  "status": { "lubrificacao": "OK", "hidraulico": "OK" },
  "meta": {
    "machine": "MOTOBOMBA-007",
    "fetched_rows": 60,
    "feature_order": [
      "Eng_RPM", "Cool_T", "Oil_P", "Oil_L",
      "Recalque", "Succao", "Bat_V", "Char_V"
    ],
    "requested_time_steps": 60,
    "timesteps": 60,
    "n_features": 8
  }
}
```

Além do valor numérico, a API classifica automaticamente o índice em faixas de status:

- `OK`: valor ≥ 70
- `ATENÇÃO`: 40 ≤ valor < 70
- `ALERTA`: valor < 40

Isso permite que os sistemas consumidores interpretem facilmente os números como estados operacionais:

```json
{
  "indices": { "lubrificacao": 73.3, "hidraulico": 65.5 },
  "status": { "lubrificacao": "OK", "hidraulico": "ATENÇÃO" }
}
```
  **Exemplo:** No resultado acima, a motobomba está com lubrificação em ordem, mas o subsistema hidráulico exige acompanhamento, pois já está na faixa de ATENÇÃO.


