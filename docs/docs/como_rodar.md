---
title: Como rodar o projeto
sidebar_label: Como rodar o projeto
sidebar_position: 8
---

# Como Rodar o Projeto: Guia de Inicialização Completo

Este guia detalha o processo de inicialização de todos os componentes do projeto, desde o ambiente de desenvolvimento até a execução dos serviços de Machine Learning. O projeto é modular, exigindo a ativação de diferentes serviços em suas respectivas pastas.

## 1. Pré-requisitos do Ambiente

Antes de iniciar qualquer componente, certifique-se de que seu ambiente de desenvolvimento atende aos seguintes requisitos:

| Requisito | Versão Mínima Recomendada | Propósito |
| :--- | :--- | :--- |
| **Git** | 2.x | Clonagem e gerenciamento do repositório. |
| **Node.js** | 18.x (LTS) | Execução do Frontend (React) e do Backend/API Gateway (Express). |
| **npm** | 9.x | Gerenciador de pacotes do Node.js. |
| **Python** | 3.10+ | Execução dos scripts de Machine Learning e do Serviço BentoML. |
| **Docker** | 20.x | Gerenciamento dos serviços em contêiner (Database e Datalake). |
| **Docker Compose** | 2.x | Orquestração de múltiplos contêineres. |

### 1.1. Clonagem do Repositório

O primeiro passo é clonar o repositório do projeto para sua máquina local:

```bash
git clone https://github.com/Inteli-College/2025-2A-T12-EC07-G03
cd 2025-2A-T12-EC07-G03/
```

## 2. Inicialização dos Serviços de Infraestrutura

Os serviços de infraestrutura (Database e Datalake) devem ser iniciados primeiro, pois são dependências críticas para os demais componentes.

### 2.1. Database (PostgreSQL)

O banco de dados PostgreSQL é utilizado para armazenar os dados de telemetria processados (`processed_data`) e os resultados das predições (`predictions`).

1.  **Navegue até a pasta do Database:**
    ```bash
    cd src/database
    ```
2.  **Inicie o contêiner Docker:**
    O `docker-compose.yml` nesta pasta irá configurar e iniciar o serviço PostgreSQL.
    ```bash
    docker compose up -d
    ```
    O parâmetro `-d` (detached) executa o contêiner em segundo plano.

### 2.2. Datalake (MinIO)

O MinIO, um armazenamento de objetos compatível com S3, é utilizado como Datalake para armazenar os artefatos dos modelos de Machine Learning (pesos e *scalers*).

1.  **Navegue até a pasta do Datalake:**
    ```bash
    cd ../datalake
    ```
2.  **Inicie o contêiner Docker:**
    ```bash
    docker compose up -d
    ```
3.  **Configuração:**
    Conforme mencionado, **consulte o guia de configuração** dentro da pasta `src/datalake` para criar os *buckets* necessários (ex: `models`) e garantir que as credenciais de acesso (definidas nas variáveis de ambiente do serviço BentoML) estejam corretas.

## 3. Inicialização dos Serviços de Backend e Frontend

Com a infraestrutura ativa, os serviços de aplicação podem ser iniciados.

### 3.1. Backend / API Gateway (Express.js)

O Backend, implementado em Express.js, atua como o API Gateway, roteando requisições do Frontend para o Serviço de Inferência de ML.

1.  **Navegue até a pasta do Backend:**
    ```bash
    cd ../backend
    ```
2.  **Instale as dependências:**
    ```bash
    npm install
    ```
3.  **Inicie o servidor de desenvolvimento:**
    ```bash
    npm run dev
    ```
    O servidor será iniciado, geralmente na porta `3001` ou conforme configurado no ambiente.

### 3.2. Frontend (React)

O Frontend é a interface de usuário que consome os dados e as predições do Backend.

1.  **Navegue até a pasta do Frontend:**
    ```bash
    cd ../frontend
    ```
2.  **Instale as dependências:**
    ```bash
    npm install
    ```
3.  **Inicie o servidor de desenvolvimento:**
    ```bash
    npm run dev
    ```
    O aplicativo React será iniciado, geralmente na porta `5173` ou conforme configurado.

## 4. Inicialização dos Serviços de Machine Learning e Dados

Estes serviços são responsáveis por alimentar o sistema com dados e fornecer a capacidade de predição.

### 4.1. Serviço de Treinamento e Inferência (BentoML)

O BentoML é utilizado para servir os modelos de Machine Learning (XGBoost e GRU) em um endpoint HTTP, que será consumido pelo API Gateway.

1.  **Navegue até a pasta de Treinamento:**
    ```bash
    cd ../treinamento
    ```
2.  **Inicie o serviço de inferência:**
    Este comando inicia o servidor BentoML, que carrega os modelos e expõe os endpoints de predição.
    ```bash
    python3 -m bentoml serve
    ```
    **Nota Técnica:** Para ambientes de produção, o BentoML é projetado para ser empacotado em um contêiner Docker e implantado. Consulte a documentação oficial do BentoML para comandos de *build* e *deploy* otimizados.

### 4.2. Pré-processamento de Dados

O script de pré-processamento é responsável por transformar os dados brutos de telemetria em um formato adequado para o treinamento e inferência dos modelos, inserindo-os na tabela `processed_data` do PostgreSQL.

1.  **Navegue até a pasta de Pré-processamento:**
    ```bash
    cd ../pre-processamento
    ```
2.  **Execute o script de entrada:**
    ```bash
    ./entrypoint.sh
    ```
    **Nota Técnica:** O script `entrypoint.sh` deve conter a lógica para executar o processo de pré-processamento (ex: um script Python) e garantir que as dependências necessárias estejam instaladas.

### 4.3. Coleta de Dados do Broker (MQTT/Telemetria)

Este script executa a coleta de dados em tempo real do *broker* de telemetria (MQTT, por exemplo), alimentando o sistema com novos dados que serão consumidos pelo pré-processamento.

1.  **Navegue até a pasta do Extrator:**
    ```bash
    cd ../scripts/broker_data_extractor
    ```
2.  **Execute o script principal:**
    ```bash
    python3 main.py
    ```
    **Nota Técnica:** Este script deve manter uma conexão ativa com o *broker* e persistir os dados brutos ou semi-processados em um local acessível ao pré-processamento.

## 5. Resumo da Ordem de Inicialização

Para garantir que todas as dependências sejam atendidas, a ordem de inicialização recomendada é:

1.  **Infraestrutura:** Database e Datalake (MinIO).
2.  **Serviço de ML:** Treinamento/Inferência (BentoML).
3.  **Fluxo de Dados:** Pré-processamento e Coleta de Dados do Broker.
4.  **Aplicação:** Backend/API Gateway e Frontend.

| Componente | Pasta | Comando de Inicialização |
| :--- | :--- | :--- |
| **Database** | `src/database` | `docker compose up -d` |
| **Datalake** | `src/datalake` | `docker compose up -d` |
| **Treinamento/Inferência** | `src/treinamento` | `python3 -m bentoml serve` |
| **Pré-processamento** | `src/pre-processamento` | `./entrypoint.sh` |
| **Coleta de Dados** | `src/scripts/broker_data_extractor` | `python3 main.py` |
| **Backend/API Gateway** | `src/backend` | `npm install && npm run dev` |
| **Frontend** | `src/frontend` | `npm install && npm run dev` |

Ao seguir esta ordem, o sistema estará totalmente operacional, com o Frontend exibindo dados em tempo real e resultados de predição gerados pelos modelos de Machine Learning.
