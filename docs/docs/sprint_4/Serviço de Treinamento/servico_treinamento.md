---
title: Serviço de Treinamento de Modelos
sidebar_label: Serviço de Treinamento
sidebar_position: 4
---

## 1. Visão Geral e Arquitetura

O **Serviço de Treinamento de Modelos** é o componente da plataforma de MLOps responsável por orquestrar e executar o treinamento de novos modelos de *Machine Learning* sob demanda. Ele foi projetado como um sistema assíncrono para lidar com tarefas de longa duração sem bloquear o usuário, fornecendo uma experiência interativa e resiliente.

A arquitetura é composta por três serviços principais que trabalham em conjunto, orquestrados pelo `docker-compose`:

1.  **API (FastAPI):** A porta de entrada para os usuários. É uma API web leve e rápida que expõe endpoints para iniciar e monitorar os trabalhos de treinamento. Sua única responsabilidade é validar as requisições, criar um registro do trabalho no banco de dados e enfileirar a tarefa para execução.
2.  **Fila de Tarefas (Redis + Celery):** O coração do sistema assíncrono.
    *   **Redis:** Atua como *message broker* (intermediário de mensagens) e *backend* de resultados. Ele armazena as tarefas que precisam ser executadas e guarda o estado e o resultado de cada uma.
    *   **Celery Worker:** É o serviço "trabalhador". Ele fica constantemente monitorando a fila no Redis. Assim que uma nova tarefa de treinamento aparece, ele a consome e executa a lógica pesada: carregar dados, treinar o modelo, salvar os artefatos, etc.
3.  **Armazenamento de Artefatos (MinIO):** Um servidor de armazenamento de objetos compatível com o protocolo S3. É usado para armazenar os modelos treinados (arquivos `.pkl`) e outros artefatos, como relatórios de métricas.


## 2. O Fluxo de Treinamento Assíncrono

A interação do usuário com o serviço foi projetada para ser não-bloqueante. Em vez de o usuário fazer uma requisição e esperar minutos (ou horas) pela resposta, o sistema responde imediatamente e permite que o status seja consultado posteriormente.

O fluxo ocorre da seguinte maneira:

1.  **Início (Requisição):** O usuário envia uma requisição `POST` para o endpoint `/train`, especificando a máquina (`machine_name`) e o tipo de modelo (`indicator`) a ser treinado, junto com um intervalo de datas opcional.

2.  **Validação e Enfileiramento (API):**
    *   A API FastAPI recebe a requisição.
    *   Ela valida os parâmetros (ex: o indicador é válido? A máquina existe nos dados processados?).
    *   Se tudo estiver correto, ela cria uma nova entrada na tabela `training_jobs` do banco de dados PostgreSQL com o status `"pending"` e um `ID` de processo único (UUID).
    *   **Imediatamente**, ela retorna uma resposta `200 OK` ao usuário, contendo o `process_id` e o status `"pending"`. A interação do usuário com a API neste momento termina.

3.  **Execução em Segundo Plano (Celery Worker):**
    *   A API, ao criar o trabalho, também publicou uma nova tarefa na fila `training_queue` no Redis.
    *   O Celery Worker, que está ocioso aguardando trabalho, "pega" essa tarefa da fila.
    *   O Worker começa a executar a lógica de treinamento (a classe `ModelFactory`):
        *   Atualiza o status do trabalho no banco de dados para `"running"`.
        *   Conecta-se ao Data Warehouse (PostgreSQL) para buscar os dados processados.
        *   Executa a lógica de *labeling* para identificar eventos de pré-falha.
        *   Divide os dados em conjuntos de treino e teste.
        *   Realiza a otimização de hiperparâmetros com `GridSearchCV`.
        *   Treina o melhor modelo XGBoost.
        *   Salva o artefato do modelo (`.pkl`) no bucket `models` do MinIO.
        *   Salva os metadados do treinamento (métricas, parâmetros, caminho do artefato) na tabela `models` do PostgreSQL.
        *   Ao final, atualiza o status do trabalho na tabela `training_jobs` para `"completed"` ou `"failed"`, preenchendo a mensagem de erro, se houver.

4.  **Monitoramento (Polling):**
    *   Enquanto o Worker executa a tarefa em segundo plano, o usuário (ou um sistema de frontend) pode usar o `process_id` recebido na etapa 2 para consultar o endpoint `GET /status/{process_id}`.
    *   Este endpoint simplesmente consulta a tabela `training_jobs` e retorna o estado atual do trabalho: `pending`, `running`, `completed` ou `failed`.
    *   O usuário pode fazer "polling" (chamar este endpoint repetidamente em intervalos de tempo) para acompanhar o progresso.

5.  **Conclusão:**
    *   Quando a consulta ao endpoint `/status/{process_id}` retorna o status `"completed"`, a resposta também incluirá o `bucket_address`, que é o caminho para o modelo recém-treinado no MinIO, pronto para ser usado pelo serviço de inferência.

Este fluxo desacoplado é extremamente escalável e resiliente. Múltiplos trabalhos de treinamento podem ser enfileirados, e podemos escalar horizontalmente adicionando mais Celery Workers para processar a fila em paralelo.

## 3. Detalhamento dos Endpoints da API

A API (`treinamento.app`) é a interface de controle para o serviço.

### `POST /train`
Inicia um novo trabalho de treinamento de modelo.

**Corpo da Requisição (JSON):**
```json
{
  "indicator": "status",
  "machine_name": "MOTOBOMBA-007",
  "start_date": "2025-01-01",
  "end_date": "2025-08-31"
}
```
*   `indicator` (str): Por enquanto, define o tipo de modelo. No futuro, pode diferenciar entre modelos de classificação ("status") e de regressão ("health").
*   `machine_name` (str): O identificador da máquina para a qual o modelo será treinado.
*   `start_date` / `end_date` (date, opcional): Filtra o período dos dados a serem usados para o treinamento.

**Resposta Imediata (Sucesso):**
```json
{
  "process_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "pending"
}
```

### `GET /status/{process_id}`
Consulta o status de um trabalho de treinamento em andamento ou concluído.

**Parâmetros da URL:**
*   `process_id` (UUID): O ID retornado pela rota `/train`.

**Exemplo de Resposta (Trabalho Concluído):**
```json
{
  "process_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "indicator": "status",
  "machine_name": "MOTOBOMBA-007",
  "status": "completed",
  "error_message": null,
  "created_at": "2025-09-27T10:00:00Z",
  "updated_at": "2025-09-27T10:15:00Z",
  "finished_at": "2025-09-27T10:15:00Z",
  "bucket_address": "model/xgb_model_MOTOBOMBA-007_2025_09_27_10_15_00.pkl"
}
```

### `GET /health`
Um endpoint simples para verificação de saúde, usado para confirmar que o serviço da API está online.

## 4. Lógica de Treinamento (`ModelFactory`)

A classe `ModelFactory` encapsula toda a lógica de treinamento do modelo XGBoost.

*   **`_prepare_data`**:
    *   Carrega os dados processados do PostgreSQL para a máquina e período especificados.
    *   **Criação de Labels (Target):** Esta é uma etapa crucial. Um evento de falha é definido como uma queda percentual drástica na rotação do motor (`Eng_RPM_variation_percentage`). O método marca como "pré-falha" (`failure_label = 1`) todos os registros que ocorrem em uma janela de tempo (ex: 30 minutos) **antes** do evento de falha. Isso ensina o modelo a reconhecer os padrões que *antecedem* uma quebra.

*   **`_split_data`**:
    *   Divide os dados em conjuntos de treino (80%) e teste (20%) de forma cronológica. Isso é fundamental para séries temporais, pois garante que o modelo seja testado em dados "do futuro" que ele nunca viu.

*   **`train_xgboost`**:
    *   **Balanceamento de Classes:** Calcula `scale_pos_weight`, um hiperparâmetro do XGBoost que informa ao modelo que a classe "pré-falha" é muito mais rara (e mais importante) que a classe "normal". Isso evita que o modelo simplesmente ignore as falhas.
    *   **Otimização de Hiperparâmetros:** Usa `GridSearchCV` para testar sistematicamente várias combinações de hiperparâmetros (`n_estimators`, `max_depth`, etc.) e encontrar a que maximiza a métrica de `recall`, que é a mais importante para este problema (queremos minimizar os falsos negativos, ou seja, falhas não previstas).
    *   **Avaliação e Armazenamento:** Após encontrar o melhor modelo, ele calcula as métricas finais, salva o modelo no MinIO e registra os metadados no PostgreSQL.

## 5. Implantação e Operação

O `docker-compose.yml` define e conecta todos os serviços.

*   **Dependências:** O `depends_on` garante que a API e o Worker só iniciem depois que o Redis estiver saudável e pronto para aceitar conexões.
*   **Variáveis de Ambiente:** A configuração (URLs de banco de dados, chaves de acesso) é passada de forma segura através de variáveis de ambiente, seguindo as melhores práticas.
*   **Comandos:** Cada serviço tem um comando específico: `uvicorn` para iniciar a API e `celery worker` para iniciar o trabalhador, instruindo-o a escutar a fila `training_queue`.
*   **Volumes:** O código-fonte é montado como um volume, permitindo o desenvolvimento com *hot-reloading* (as alterações no código são refletidas sem a necessidade de reconstruir a imagem).
