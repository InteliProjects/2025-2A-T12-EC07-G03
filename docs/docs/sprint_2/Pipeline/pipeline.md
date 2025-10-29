---
title: Pipeline
sidebar_label: Pipeline
sidebar_position: 1
---

# Pipeline de Limpeza e Pré-processamento de Dados

## Introdução

&emsp;Esta documentação descreve a pipeline de limpeza e pré-processamento de dados desenvolvida para preparar os dados de telemetria de máquinas para o treinamento de modelos de Machine Learning. O objetivo principal desta pipeline é transformar dados brutos, que podem conter ruídos, valores ausentes, inconsistências e formatos inadequados, em um formato limpo e estruturado, pronto para ser consumido por algoritmos de aprendizado de máquina.

&emsp;A pipeline é construída utilizando a funcionalidade `Pipeline` do `scikit-learn`, o que permite encadear uma série de transformações de dados de forma sequencial e organizada. Cada etapa da pipeline é uma classe customizada que implementa métodos `fit` e `transform`, garantindo compatibilidade com o ecossistema do `scikit-learn`.

## Como Usar a Pipeline

&emsp;A pipeline é definida como um objeto `Pipeline` do `scikit-learn`, o que a torna fácil de usar. Primeiro, é necessário carregar os dados brutos. Em seguida, a pipeline pode ser aplicada aos dados usando o método `fit_transform()`.

```python
import pandas as pd
from sklearn.pipeline import Pipeline

from pipeline_functions import AdjustTimestampColumn, RemoveDuplicatesAndNaN, TreatHighValues, \
     FixBatteryAndAlternatorValues, PivotDataframe, RemoveZeroColumns, CreateMinutesRunningColumn, \
     CreateVariationsColumns, GenericScaler, CreateHydraulicColumns, CreateMotorColumns, \
     CreateTargetVariable, RemoveInfValues, load_and_concat_data_from_csv

RESAMPLE_SECONDS = 12
TARGET_VARIABLE_NAME = "fail"
EXCLUDE_COLUMNS = ["timestamp", "motor_pump", "minutes_running", TARGET_VARIABLE_NAME]
VARIATION_COLUMNS = ["Bat_V", "Char_V", "Cool_T", "Eng_RPM", "Fuel_Con", "Fuel_L", "Oil_L", "Oil_P"]

pipeline = Pipeline(steps=[
    ## Data Cleaning
    ("adjust_timestamp", AdjustTimestampColumn()),
    ("remove_duplicates_and_nan", RemoveDuplicatesAndNaN()),
    ("treat_high_values", TreatHighValues()),
    ("fix_battery_and_alternator_values", FixBatteryAndAlternatorValues()),
    ("create_target_variable", CreateTargetVariable(target_variable_name=TARGET_VARIABLE_NAME)),
    ("pivot_dataframe", PivotDataframe(resample_seconds=RESAMPLE_SECONDS, target_variable_name=TARGET_VARIABLE_NAME)),
    ("remove_zero_columns", RemoveZeroColumns(target_variable_name=TARGET_VARIABLE_NAME)),
    ("create_minutes_running_column", CreateMinutesRunningColumn()),
    ("generic_scaler", GenericScaler(exclude_columns=EXCLUDE_COLUMNS)), ## Após essa etapa, os valores não vão ficar "estranhos"
    ("create_variation_columns", CreateVariationsColumns(columns=VARIATION_COLUMNS)),
    ("create_hydraulic_columns", CreateHydraulicColumns()),
    ("create_motor_columns", CreateMotorColumns()),
    ("remove_inf_values", RemoveInfValues())
])

data_itu415 = load_and_concat_data_from_csv("caminho/para/itu415_normal.csv")
data_itu844 = load_and_concat_data_from_csv("caminho/para/itu844_falha.csv")

# Aplicar a pipeline aos dados
data_itu415_processed = pipeline.fit_transform(data_itu415)
data_itu844_processed = pipeline.fit_transform(data_itu844)

# os dataframes processados agora estão prontos para rodar modelos, só é necessário os concatenar/mergear com base nas 
# colunas em comum
```

## Descrição das Funções da Pipeline

&emsp;Cada etapa da pipeline é implementada como uma classe customizada, derivada de `BaseEstimator` e `TransformerMixin` do `scikit-learn`, permitindo que sejam usadas dentro de um objeto `Pipeline`. Abaixo, detalhamos a funcionalidade de cada uma:

### `AdjustTimestampColumn`

*   **Propósito:** Ajusta e padroniza a coluna de `timestamp` no DataFrame. Garante que a coluna esteja no formato de data/hora correto e que possa ser usada como índice para operações baseadas em tempo.
*   **Parâmetros:** Nenhum parâmetro específico na inicialização.

### `RemoveDuplicatesAndNaN`

*   **Propósito:** Remove linhas duplicadas e trata valores ausentes (NaN) do DataFrame. Esta etapa é importante para garantir a integridade dos dados e evitar que valores faltantes interfiram nas etapas subsequentes de processamento ou no treinamento do modelo.
*   **Parâmetros:** Nenhum parâmetro específico na inicialização.

### `TreatHighValues`

*   **Propósito:** Identifica e trata valores excessivamente altos em colunas específicas que podem ser indicativos de erros de sensor ou leituras anômalas. A lógica exata de tratamento (e.g., substituição por NaN, capping) é implementada internamente na classe.
*   **Parâmetros:** Nenhum parâmetro específico na inicialização.

### `FixBatteryAndAlternatorValues`

*   **Propósito:** Corrige valores inconsistentes ou incorretos relacionados às leituras de bateria (`Bat_V`) e alternador (`Char_V`). Esta etapa é específica para o domínio dos dados de telemetria de máquinas, onde essas leituras podem apresentar padrões de erro conhecidos.
*   **Parâmetros:** Nenhum parâmetro específico na inicialização.

### `CreateTargetVariable`

*   **Propósito:** Cria a variável alvo (`target`) no DataFrame. Conforme descrito na documentação de classificação, esta variável é criada com base na origem dos dados (e.g., `itu415` para operação normal, `itu844` para falha).
*   **Parâmetros:**
    *   `target_variable_name` (str): O nome da coluna que será criada para a variável alvo (e.g., "fail").

### `PivotDataframe`

*   **Propósito:** Realiza uma operação de pivoteamento e reamostragem no DataFrame. Isso é comum em dados de séries temporais para agregar dados em intervalos regulares (e.g., a cada 12 segundos) e preparar o DataFrame para análise.
*   **Parâmetros:**
    *   `resample_seconds` (int): O intervalo de tempo em segundos para reamostrar os dados.
    *   `target_variable_name` (str): O nome da coluna da variável alvo, para garantir que ela seja tratada corretamente durante o pivoteamento.

### `RemoveZeroColumns`

*   **Propósito:** Remove colunas do DataFrame que contêm apenas valores zero (ou valores muito próximos de zero, dependendo da implementação interna). Essas colunas geralmente não fornecem informações úteis para o modelo e podem ser removidas para reduzir a dimensionalidade.
*   **Parâmetros:**
    *   `target_variable_name` (str): O nome da coluna da variável alvo, para garantir que ela não seja removida.

### `CreateMinutesRunningColumn`

*   **Propósito:** Cria uma nova feature que representa o tempo de execução da máquina em minutos. Esta pode ser uma feature importante para modelos de previsão de falhas, pois o tempo de operação pode estar correlacionado com o desgaste.
*   **Parâmetros:** Nenhum parâmetro específico na inicialização.

### `GenericScaler`

*   **Propósito:** Aplica uma técnica de escalonamento (e.g., StandardScaler, MinMaxScaler) às colunas numéricas do DataFrame. O escalonamento é fundamental para muitos algoritmos de Machine Learning, pois garante que todas as features contribuam igualmente para o modelo, evitando que features com grandes escalas dominem o processo de aprendizado.
*   **Parâmetros:**
    *   `exclude_columns` (list): Uma lista de nomes de colunas a serem excluídas do processo de escalonamento (e.g., `timestamp`, `target_variable_name`).

### `CreateVariationsColumns`

*   **Propósito:** Cria novas features que representam a variação (e.g., desvio padrão, diferença) de certas colunas ao longo do tempo. A variação de leituras de sensores pode ser um indicador importante de anomalias ou falhas iminentes.
*   **Parâmetros:**
    *   `columns` (list): Uma lista de nomes de colunas para as quais as features de variação serão criadas.

### `CreateHydraulicColumns`

*   **Propósito:** Cria features específicas relacionadas ao sistema hidráulico da máquina. Estas features são derivadas de outras colunas existentes e são projetadas para capturar informações relevantes sobre o desempenho hidráulico.
*   **Parâmetros:** Nenhum parâmetro específico na inicialização.

### `CreateMotorColumns`

*   **Propósito:** Cria features específicas relacionadas ao motor da máquina. Semelhante às colunas hidráulicas, estas features são engenheiradas para fornecer insights sobre o estado e o desempenho do motor.
*   **Parâmetros:** Nenhum parâmetro específico na inicialização.

### `RemoveInfValues`

*   **Propósito:** Remove ou trata valores infinitos (`inf` ou `-inf`) que podem ter sido introduzidos durante as etapas de transformação (e.g., divisões por zero). Valores infinitos podem causar problemas em muitos algoritmos de Machine Learning.
*   **Parâmetros:** Nenhum parâmetro específico na inicialização.

## Funções Auxiliares

&emsp;Além das etapas da pipeline, a função `load_and_concat_data_from_csv` é uma função auxiliar importante para carregar e combinar dados de múltiplos arquivos CSV.

### `load_and_concat_data_from_csv`

*   **Propósito:** Carrega dados de um ou mais arquivos CSV e os concatena em um único DataFrame. Esta função é útil para consolidar dados de diferentes fontes ou períodos antes de aplicar a pipeline de pré-processamento.
*   **Parâmetros:**
    *   `file_paths` (list ou str): Um caminho de arquivo CSV (string) ou uma lista de caminhos de arquivos CSV. Se for uma lista, os DataFrames serão concatenados.

## Conclusão

&emsp;Ao encapsular uma série de transformações em um objeto `Pipeline` do `scikit-learn`, podemos garantir a reprodutibilidade e a facilidade de uso, permitindo que os cientistas de dados se concentrem na construção e avaliação de modelos, em vez de gastar tempo excessivo com a manipulação de dados brutos. A modularidade das etapas também facilita a manutenção e a adição de novas transformações conforme as necessidades do projeto evoluem.