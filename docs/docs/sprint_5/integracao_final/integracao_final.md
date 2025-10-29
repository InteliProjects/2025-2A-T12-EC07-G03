---
title: Integração Final
sidebar_label: Integração Final
sidebar_position: 2
---

# Integração Final: Fluxo de Dados Preditivos (Machine Learning e Frontend)

Este documento detalha a **integração completa** entre os serviços de Machine Learning (ML) e a interface de usuário (Frontend) da plataforma de monitoramento preditivo. O foco é descrever o fluxo de dados e a comunicação entre os componentes, garantindo a entrega de *insights* preditivos em tempo real para o usuário final.

## 1. Arquitetura de Integração e Componentes

A solução adota uma arquitetura de microsserviços, onde cada componente desempenha um papel específico no ciclo de vida da predição, desde a requisição até a visualização.

| Componente | Tecnologia | Papel na Integração | Protocolo de Comunicação |
| :--- | :--- | :--- | :--- |
| **Frontend** | React/TypeScript | Inicia a requisição de predição e visualiza os resultados. | HTTP (API Gateway), WebSocket/MQTT (Dados em Tempo Real) |
| **API Gateway** | Node.js/Express | Valida a requisição, roteia para o serviço de ML e gerencia a segurança. | HTTP (Entrada/Saída), `fetch` (Comunicação Interna) |
| **ML Inference Service** | BentoML/Python | Executa os modelos de ML (XGBoost e GRU) e gerencia o acesso a dados e modelos. | HTTP (Entrada/Saída), PostgreSQL (SQL), MinIO (S3 API) |
| **Banco de Dados** | PostgreSQL | Fonte de dados históricos (`processed_data`) e destino para persistência dos resultados de predição (`predictions`). | SQL (via `sqlalchemy` no BentoML) |
| **Armazenamento** | MinIO (S3) | Repositório dos artefatos dos modelos treinados (pesos e *scalers*). | S3 API (via `minio` client no BentoML) |

## 2. Fluxo de Dados de Inferência Preditiva

O processo de obtenção de uma predição de Machine Learning é um fluxo orquestrado que envolve a comunicação sequencial entre os componentes.

### 2.1. Iniciação da Requisição (Frontend)

O Frontend, desenvolvido em React/TypeScript, inicia o fluxo de duas maneiras principais:

1.  **Predição de Status (XGBoost):** O componente `Dashboard.tsx` executa `fetchStatusPredictions` periodicamente para obter o status de pré-falha de todas as máquinas.
2.  **Predição de Saúde (GRU):** O componente `MachineModal.tsx` permite ao usuário acionar manualmente a predição de saúde (`handlePrediction`) ou o `Dashboard.tsx` busca a predição de saúde (`fetchHealthPredictions`) para visualização no gráfico.

Ambas as ações resultam em uma chamada HTTP `POST` para o API Gateway, com o nome da máquina (`machine_name`) e, no caso do GRU, o endereço do modelo (`model_bucket_address`) e o horizonte de tempo (`time_steps`).

### 2.2. Roteamento e Validação (API Gateway)

O API Gateway (módulo `model-inference.js`) é o ponto de contato inicial e de segurança:

1.  **Validação:** Utiliza a biblioteca **Zod** para validar o *payload* da requisição (ex: `machine_name` é uma string, `time_steps` é um número inteiro). Isso previne que requisições malformadas atinjam o serviço de ML.
2.  **Roteamento:** O Gateway atua como um *proxy* reverso, encaminhando a requisição validada para o Serviço de Inferência de ML, que está rodando internamente em `http://localhost:3000`.

| Endpoint do Gateway | Rota Interna (BentoML) | Modelo Envolvido |
| :--- | :--- | :--- |
| `/model-inference/machine/xgboost/predict` | `http://localhost:3000/machine/xgboost/predict` | XGBoost (Classificação) |
| `/model-inference/machine/gru/predict` | `http://localhost:3000/machine/gru/predict` | GRU (Série Temporal) |

### 2.3. Execução da Inferência (BentoML)

O Serviço de Inferência (classe `ModelInferenceService` em `model_inference_service.py`) é o motor do processo:

1.  **Acesso ao Modelo (MinIO):** Para a inferência GRU (`predict_machine_gru`), o serviço utiliza o cliente **MinIO** para baixar dinamicamente os artefatos do modelo (pesos `.h5` e *scaler* `.pkl`) do *bucket* S3. Isso garante que a versão correta do modelo seja utilizada, mesmo que o modelo tenha sido treinado recentemente.
2.  **Acesso a Dados (PostgreSQL):** O serviço se conecta ao PostgreSQL via `sqlalchemy` para buscar os dados de telemetria necessários.
    *   **GRU:** Busca as últimas `time_steps` linhas da tabela `processed_data` para formar a sequência de entrada.
    *   **XGBoost:** Busca a última linha da tabela `processed_data`.
3.  **Processamento e Predição:** O *DataFrame* do Pandas é então passado para a classe de inferência (`GRUInference` ou `ModelInference`), que aplica o pré-processamento (como a normalização via *scaler* baixado) e executa a predição.

### 2.4. Persistência e Resposta

Após a execução da predição, o resultado segue um caminho duplo:

1.  **Persistência (PostgreSQL):** O resultado completo da predição (incluindo metadados, índices de saúde e status) é serializado em JSON e inserido na tabela `predictions` do PostgreSQL. Isso cria um histórico auditável de todas as inferências realizadas.
2.  **Resposta (JSON):** O resultado da predição é retornado como um objeto JSON para o API Gateway.

O API Gateway, por sua vez, retransmite essa resposta JSON para o Frontend, completando o ciclo.

## 3. Visualização e Interação no Frontend

O Frontend consome os resultados da predição para fornecer *feedback* visual imediato ao usuário.

### 3.1. Apresentação dos Resultados

*   **Dashboard:** Exibe o status de pré-falha (XGBoost) diretamente nos cartões das máquinas (`statusPrediction`) e utiliza os índices de saúde (GRU) para popular o **Gráfico de Barras** de Indicadores de Saúde (usando `recharts`).
*   **Modal de Detalhes:** O `MachineModal.tsx` apresenta os índices de saúde (GRU) de forma detalhada, utilizando **gráficos circulares** para mostrar o percentual de saúde de subsistemas (Hidráulico e Lubrificação) e aplicando cores dinâmicas (função `getStatusColor`) para indicar o nível de risco (`NORMAL`, `ATENÇÃO`, `ALERTA`).

### 3.2. Sincronização de Dados

A integração não se limita apenas às requisições de predição. O Frontend mantém uma conexão persistente (via WebSocket/MQTT, gerenciada pelo `useRealtimeData` hook) para receber dados de telemetria em tempo real. Isso garante que o *input* para as predições (os dados mais recentes) e a visualização dos dados brutos estejam sempre atualizados, criando um ambiente de monitoramento dinâmico.

## 4. Conclusão

A integração final entre o Frontend e os serviços de Machine Learning estabelece um **ciclo de feedback proativo** essencial para o sucesso do projeto.

O uso de um **API Gateway** desacopla a interface de usuário do complexo serviço de inferência, garantindo **segurança, validação e escalabilidade**. O **Serviço BentoML** oferece uma plataforma robusta para a execução de modelos heterogêneos (XGBoost para classificação pontual e GRU para análise de série temporal), com a capacidade crítica de carregar dinamicamente os artefatos de modelo do **MinIO**.

Essa arquitetura permite que a Itubombas não apenas visualize o estado atual de suas motobombas, mas também **antecipe falhas** com base em indicadores de saúde detalhados. A capacidade de acionar predições de saúde em diferentes horizontes de tempo, diretamente da interface do usuário, transforma a plataforma em uma ferramenta estratégica para a **manutenção preditiva**, reduzindo custos operacionais e maximizando a satisfação do cliente. O resultado é uma solução coesa e eficiente, onde o Machine Learning é traduzido em valor de negócio através de uma interface de usuário intuitiva e responsiva.


