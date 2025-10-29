---
title: Serviço de Pré-Processamento de Dados (ETL)
sidebar_label: Pré-Processamento (ETL)
sidebar_position: 3
---

## 1. Propósito e Posição na Arquitetura

O **Serviço de Pré-Processamento de Dados** é o coração da nossa estratégia de dados, funcionando como um pipeline de **ETL (Extração, Transformação e Carga)** robusto e automatizado. Sua missão é converter os dados brutos e heterogêneos de telemetria, provenientes diretamente das motobombas, em um formato estruturado, limpo e enriquecido, pronto para análise e para o treinamento de modelos de *Machine Learning*.

Este serviço se posiciona entre o *Data Lake*, que armazena os dados brutos, e o *Data Warehouse*, que armazena os dados processados, garantindo um fluxo de dados confiável e contínuo.

## 2. Arquitetura Técnica Detalhada

A solução foi desenhada com base em princípios de MLOps, priorizando automação, reprodutibilidade e monitoramento.

### 2.1. Componentes da Solução

| Componente | Tecnologia | Responsabilidade |
| :--- | :--- | :--- |
| **Orquestração** | Docker + Cron | Gerencia o ciclo de vida do serviço e agenda a execução do pipeline a cada 10 minutos. |
| **Extração (E)** | Dremio + PyArrow | Conecta-se ao *Data Lake* (tabelas Iceberg) e extrai dados marcados como não processados. |
| **Transformação (T)** | Python, Pandas, Scikit-learn | Aplica um pipeline de limpeza, normalização e engenharia de features. |
| **Carga (L)** | SQLAlchemy + Psycopg2 | Insere os dados transformados no *Data Warehouse* (PostgreSQL). |
| **Logging** | Módulo `logging` do Python | Registra todas as operações, sucessos e falhas em um arquivo de log para auditoria e depuração. |

### 2.2. Lógica de Execução Automatizada

O serviço é empacotado em uma imagem Docker que contém o script Python, suas dependências e um agendador `cron`.

1.  **Inicialização do Contêiner:** O `entrypoint.sh` é executado quando o contêiner inicia. Ele tem duas funções:
    *   Inicia o serviço `cron` em segundo plano.
    *   Executa um `tail -f` no arquivo de log, permitindo que os logs do `cron` sejam transmitidos para a saída padrão do Docker (`docker logs`).

2.  **Agendamento do `cron`:** O arquivo `crontab` define a regra de execução:
    ```cron
    */10 * * * * cd /app && /usr/local/bin/python3 pre_processamento.py >> /var/log/script.log 2>&1
    ```
    *   `*/10 * * * *`: Executa a tarefa a cada 10 minutos, todos os dias.
    *   `>> /var/log/script.log 2>&1`: Redireciona toda a saída (`stdout`) e erros (`stderr`) para um arquivo de log, garantindo que todas as mensagens sejam capturadas.

## 3. O Pipeline de Transformação em Detalhes

O núcleo do serviço é o pipeline de transformação, construído com `scikit-learn.pipeline.Pipeline`. Essa abordagem garante que as etapas sejam sempre executadas na mesma ordem e que o pipeline possa ser facilmente versionado e reutilizado. As etapas são definidas como classes customizadas que herdam de `BaseEstimator` e `TransformerMixin`, garantindo total compatibilidade com o ecossistema Scikit-learn.

### Etapa 1: `AdjustTimestampColumn`
*   **Objetivo:** Padronizar a coluna de tempo.
*   **Ação:** Converte a coluna `timestamp`, que chega como texto em formato ISO8601, para o tipo `datetime` do Pandas. Esta é uma etapa crucial para permitir operações baseadas em tempo, como ordenação e reamostragem.

### Etapa 2: `RemoveDuplicatesAndNaN`
*   **Objetivo:** Limpeza inicial dos dados.
*   **Ação:** Realiza duas operações:
    1.  Preenche quaisquer valores ausentes (`NaN`) em uma coluna com o valor mais frequente (a moda) daquela coluna.
    2.  Remove quaisquer linhas que sejam duplicatas exatas, garantindo a unicidade dos registros.

### Etapa 3: `TreatHighValues`
*   **Objetivo:** Tratar valores extremos e identificar o estado de operação.
*   **Ação:** Aplica uma regra de negócio para lidar com leituras anômalas (provavelmente de erros de sensor).
    *   Valores na coluna `value` que excedem um limite (`max_limit`, padrão 20000) são considerados inválidos e substituídos por 0.
    *   Cria uma nova coluna booleana `running`, que é `1` se o valor está dentro do limite e `0` caso contrário. Esta coluna se torna um indicador fundamental para saber se a máquina estava operacional.

### Etapa 4: `FixBatteryAndAlternatorValues`
*   **Objetivo:** Corrigir um erro sistemático nos dados.
*   **Ação:** Para as leituras específicas de tensão da bateria (`Bat_V`) e do alternador (`Char_V`), os valores são divididos por 10. Isso corrige uma inconsistência de escala vinda da fonte de dados.

### Etapa 5: `PivotDataframe`
*   **Objetivo:** Reestruturar os dados para o formato de features.
*   **Ação:** Esta é a transformação mais complexa e importante. Ela converte o DataFrame do formato "longo" (uma linha por leitura de sensor) para o formato "largo" (uma linha por registro de tempo, com cada sensor como uma coluna).
    1.  **Pivoteamento:** Usa `pivot_table` para que cada `resource` único se torne uma coluna.
    2.  **Reamostragem:** Agrupa os dados por `motor_pump` e os reamostra em intervalos fixos (ex: 12 segundos). Isso padroniza a frequência dos dados e suaviza ruídos. Valores ausentes na janela são preenchidos com o último valor válido (`ffill`).
    3.  **Limpeza Final:** Remove duplicatas e preenche quaisquer `NaN` restantes com 0.

### Etapa 6: `RemoveZeroColumns`
*   **Objetivo:** Remover features não informativas.
*   **Ação:** Após o pivoteamento, algumas colunas podem conter apenas o valor 0 (sensores que não reportaram nada no período). Esta etapa identifica e remove essas colunas, pois elas não contribuem com informação para o modelo de ML.

### Etapa 7: Engenharia de Features
Nesta fase, o conhecimento de negócio é aplicado para criar novas features preditivas a partir dos dados existentes.

*   **`CreateMinutesRunningColumn`**: Calcula o tempo, em minutos, que a máquina está operando continuamente (`running == 1`). Isso cria uma feature de "tempo em atividade".
*   **`CreateVariationsColumns`**: Para uma lista de colunas importantes (pressão, temperatura, etc.), calcula a variação absoluta (`.diff()`) e percentual (`.pct_change()`) em relação à leitura anterior. Isso captura a **dinâmica** e a **tendência** do sistema, que são sinais preditivos poderosos.
*   **`CreateHydraulicColumns`**: Cria features específicas da bomba:
    *   `Hydraulic_Head`: A carga hidráulica (diferença entre pressão de saída e entrada), uma medida primária do trabalho da bomba.
    *   `Head_per_RPM`: Carga hidráulica normalizada pela rotação do motor, indicando eficiência.
    *   `Head_trend_per_minutes`: A tendência da carga hidráulica ao longo do tempo.
*   **`CreateMotorColumns`**: Cria features específicas do motor:
    *   `OilP_per_RPM`: Pressão do óleo normalizada pela rotação, para verificar se a lubrificação está adequada à carga.
    *   `CoolT_per_RPM`: Temperatura do líquido de arrefecimento normalizada pela rotação, um indicador de sobrecarga térmica.
    *   `Fuel_rate` e `Fuel_efficiency`: Taxa de consumo de combustível e eficiência geral do conjunto.

### Etapa 8: `GenericScaler`
*   **Objetivo:** Padronizar a escala das features.
*   **Ação:** Aplica o `StandardScaler` do Scikit-learn a todas as colunas numéricas (exceto as excluídas, como IDs). Isso transforma as features para que tenham média 0 e desvio padrão 1, o que é um pré-requisito para o bom desempenho de muitos algoritmos de ML.

### Etapa 9: `RemoveInfValues`
*   **Objetivo:** Limpeza final.
*   **Ação:** Substitui quaisquer valores infinitos (`inf` ou `-inf`), que podem surgir de divisões por zero nas etapas de engenharia de features, pelo valor 0.

## 4. Guia de Operações (Implantação e Monitoramento)

### 4.1. Implantação com Docker Compose

O `docker-compose.yml` orquestra a implantação do serviço.

```yaml
version: '3.8'

services:
  data-processor:
    build: .
    container_name: data-processor
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./logs:/var/log/app
```

*   `build: .`: Instruí o Docker Compose a construir a imagem a partir do `Dockerfile` no diretório atual.
*   `restart: unless-stopped`: Política de reinicialização que garante que o serviço se recupere de falhas.
*   `network_mode: host`: Simplifica a conexão com Dremio e PostgreSQL via `localhost`. Para produção, uma rede Docker dedicada (`bridge`) é uma alternativa mais segura.
*   `volumes`: Mapeia um diretório local para persistir os logs do serviço.

**Para implantar:**
```bash
# 1. Construir a imagem e iniciar o contêiner em segundo plano
docker-compose up --build -d

# 2. Verificar se o contêiner está em execução
docker-compose ps
```

### 4.2. Monitoramento

A observabilidade é a chave para manter a confiança no pipeline. A forma mais direta de monitorar a atividade é inspecionar os logs em tempo real.
```bash
# Acompanha os logs do contêiner (que estão sendo redirecionados do cron)
docker-compose logs -f data-processor
```
Procure por mensagens como:
*   `INFO - Listing Iceberg tables...`
*   `INFO - Processing table: NOME_DA_MAQUINA`
*   `INFO - Found X unprocessed records in table...`
*   `INFO - Successfully inserted X records into processed_data`
*   `INFO - Iceberg table NOME_DA_MAQUINA updated successfully`
