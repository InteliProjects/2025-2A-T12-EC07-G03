# Proposta de Arquitetura

&emsp;Este documento apresenta a proposta de arquitetura para um sistema de **ingestão de dados**, **treinamento de modelos de Machine Learning**, e **utilização em produção** com feedback para retreinamento.

> 💡 Observação: caso seja julgado necessário, cada parte do sistema pode ser **hospedada separadamente na nuvem**, garantindo maior escalabilidade, flexibilidade e resiliência.

## 1. Criação do Modelo

### 1.1 Criação do Pipeline de Dados

* Integração com fontes de dados:

 * **Batch (dados estáticos)** → Arquivos CSV/XLSX
 * **Streaming (tempo real)** → API de teste/Broker MQTT

* Processos:

 * **Carga Inicial** → Popular o banco de série temporal com dados históricos.
 * **Carga em Tempo Real** → Inserção contínua de dados do broker/API.

### 1.2 Armazenamento de Informações e Modelos

* Banco de dados para séries temporais.
* Banco de dados preparado com dados já transformados.
* Armazenamento de modelos treinados em um bucket para armazenamento em nuvem.

> Exemplos de componentes viáveis para a nuvem:
>
> * Banco de séries temporais → **Amazon Timestream**, **InfluxDB Cloud**
> * Armazenamento de modelos → **Amazon S3**, **Google Cloud Storage**
> * Pipeline de ingestão → **AWS Kinesis**, **Google Pub/Sub**, **Azure Event Hubs**

## 2. Utilização do Modelo
### 2.1 Utilização pela Interface

* Usuários acessam via **Web App**.
* Backend conecta-se ao banco preparado e ao broker MQTT.
* Resultados retornam ao cliente via interface.

> Exemplos de hospedagem:
>
> * Web App → **Vercel**, **Netlify**, **AWS Amplify**
> * Backend → **AWS ECS (Fargate)**, **Google Cloud Run**, **Azure App Service**

### 2.2 Utilização via API

* API do modelo disponibiliza endpoints de previsão.
* Processos:

 * Script de previsão consome modelo treinado.
 * Saída em formato JSON.
 * Logs e métricas armazenados para monitoramento.

> Exemplos de hospedagem:
>
> * API → **AWS Lambda (serverless)** ou **Google Cloud Functions**

## 3. Manutenção do Modelo
### 3.1 Retreinamento

* Feedback é incorporado para ajuste contínuo do modelo.
* Novos dados alimentam pipeline.
* Métricas de performance monitoradas para decidir retreinamento.


> Exemplos de hospedagem:
>
> * Treinamento → **SageMaker (AWS)**, **Vertex AI (Google Cloud)**, **Azure Machine Learning**
> * Métricas → **Prometheus + Grafana Cloud**, **AWS CloudWatch**

## Legenda de Cores

* **Azul** → Batch / Dados Estáticos
* **Laranja** → Dados em Tempo Real
* **Roxo** → Uso / Interface

```mermaid
%%{init: {'flowchart': {'curve': 'stepAfter'}}}%%
flowchart TD;
   %% Estilos para tema escuro
       classDef batch fill:#4a90e2,stroke:#ffffff,stroke-width:1px,color:#ffffff;
       classDef realtime fill:#f5a623,stroke:#ffffff,stroke-width:1px,color:#000000;
       classDef feedback fill:#7ed321,stroke:#ffffff,stroke-width:1px,color:#000000;
       classDef uso fill:#b37feb,stroke:#ffffff,stroke-width:1px,color:#ffffff;
  


   csv[📄 CSV, XLSX]
   subgraph Ingestão de Dados
       api([🌐 API]):::batch --> carga([⚡ Carga Inicial]):::batch;
       carga[⚡ Carga Inicial]:::batch --> DB2([🗄 DB de Série Temporal]);
       DB2([🗄 DB de Série Temporal]) --> transformacao[🔄 Transformação / Limpeza];
       transformacao[🔄 Transformação / Limpeza] --> DB1([🗄 DB de Dados Preparados]);
       DB1([🗄 DB de Dados Preparados]) --> treinamento_modelo[🤖 Treinamento do Modelo];
       carga2[⚡ Carga em Tempo Real]:::realtime --> DB2([🗄 DB de Série Temporal]);
       broker([📡 Broker MQTT]):::realtime --> carga2[⚡ Carga em Tempo Real]:::realtime;
   end


   subgraph Treinamento do Modelo
       treinamento_modelo[🤖 Treinamento do Modelo] --> modelo([🧠 Modelo Treinado]);
       treinamento_modelo[🤖 Treinamento do Modelo] --> metricas([📊 Métricas de Treinamento]);
       modelo([🧠 Modelo Treinado]) --> s3([☁️ Armazenamento na Nuvem]);
   end


   subgraph Utilização do Modelo
       api2([🌐 API do Modelo]):::uso --> script([📜 Script de Previsão]):::usos;
       script([📜 Script de Previsão]):::uso --> json([📝 JSON de Previsão]):::uso;
       script([📜 Script de Previsão]):::uso --> metricas([📊 Métricas de Treinamento]);
       script([📜 Script de Previsão]):::uso --> s3([☁️ Armazenamento na Nuvem]);
       script([📜 Script de Previsão]):::uso --> DB1([🗄 DB de Dados Preparados]);
   end


   subgraph Interface do Usuário
       cliente([👤 Usuário]):::uso --> interface([💻 Web App]):::uso;
   end
       interface([💻 Web App]):::uso --> backend([🖥 Back End]):::uso;
       backend([🖥 Back End]):::uso --> broker([📡 Broker MQTT]):::realtime;
       backend([🖥 Back End]):::uso --> DB1([🗄 DB de Dados Preparados]);
