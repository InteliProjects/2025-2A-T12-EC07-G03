---
title: Exploração dos dados
sidebar_label: Exploração Inicial dos dados
sidebar_position: 1
---

# Exploração e Tratamento dos Dados

## Introdução

O presente documento descreve a exploração, o tratamento e preparação de dados de bombas hidráulicas para entender sua qualidade, identificar padrões relevantes e preparar um pipeline que permita análises preditivas futuras. Por apresentarem informações mais completas nos datasets disponilizados, as principais máquinas analisadas foram:

- **ITU-415**
- **ITU-693**

Além disso, houve um primeiro olhar para a **ITU-844**, utilizada em um cenário de classificação binária.

Nesta etapa, a intenção foi entender a qualidade dos dados brutos, o comportamento dos sinais e criar hipóteses de análise.

## Descrição dos Dados

### Estrutura Original

- Formato **long**: cada linha contém `timestamp`, `motor_pump`, `resource`, `value`.

- **Fontes:** arquivos CSV com leituras de sensores.

- **Período analisado:**
    - **ITU-415:** 01/06/2025 a 17/07/2025
    - **ITU-693:** 13/05/2025 a 22/07/2025

### **Principais Sensores**

Foi selecionado sensores mais diretamente relacionados à saúde operacional do motos e da bomba:

| Sensor        | Descrição                               | Unidade | Justificativa |
|---------------|-----------------------------------------|---------|---------------|
| **Eng_RPM**   | Rotação do motor                        | RPM     | Indica esforço do motor; quedas ou picos anormais são sinais diretos de falha. |
| **Oil_P**     | Pressão do óleo                         | mca     | Essencial para lubrificação; queda rápida pode causar travamento. |
| **Cool_T**    | Temperatura do líquido de arrefecimento | °C      | Importante para detectar superaquecimento. |
| **Fuel_Con**  | Consumo de combustível                  | L       | **Não utilizado:** todos os valores estavam >2bi → substituídos por 0 no tratamento → coluna ficou zerada e sem utilidade. |
| **Fuel_L**    | Nível de combustível no tanque          | %       | Importante para prever paradas. |
| **Oil_L**     | Nível de óleo do motor                  | %       | Indicador crítico de manutenção preventiva. |
| **Bat_V**     | Tensão da bateria                       | V       | Baixas tensões afetam partida e estabilidade elétrica. |
| **Char_V**    | Tensão do alternador                    | V       | Falhas no sistema de carga podem comprometer a operação. |
| **Recalque**  | Pressão de saída da bomba               | mca     | Mede desempenho hidráulico da bomba. |
| **Sucção**    | Pressão de entrada da bomba (ITU-693)            | kPa     | Necessária para calcular carga hidráulica. |
| **FlexAnalogue** | Canal analógico genérico (ITU-415)   | –       | Pode representar sensor auxiliar. |

### Diferenças entre máquinas

- **ITU-415** → possui `FlexAnalogue`, mas não possui Sucção.
- **ITU-693** → possui `Sucção` (variável considerada valiosa na detecção de possíveis falhas).

O conjunto de sensores selecionado foi definido porque eles representam diretamente os fenômenos físicos críticos:

- **Motor:** eficiência, sobrecarga, falhas mecânicas.
- **Bomba:** desempenho hidráulico e estabilidade.
- **Sistema de apoio:** combustível e parte elétrica.

## Exploração dos Dados

### Frequência de Medições

- **ITU-415** → intervalo médio de 12,17s.
- **ITU-693** → intervalo médio de 7,23s.
- Cada sensor registra em intervalos distintos, o que ocasiona uma grande quantidade de valores ausentes (`NaN`).  

O formato *long* e a assincronia entre sensores dificultam comparações diretas, tornando necessário aplicar o processo de **resample**. O **resample** consiste em padronizar a frequência temporal dos dados em um intervalo fixo (neste caso, 15 segundos). Dessa forma, todos os sensores passam a compartilhar o mesmo "relógio", reduzindo ruído e permitindo análises consistentes.  

### Qualidade dos Dados

- **Duplicados:** 55.856 (ITU-415) e 1.673.724 (ITU-693).
- **Nulos:** dezenas em ITU-415 e milhares em ITU-693.
- **Valores Altos:** leituras acima de 2 bilhões.
- **Escalas incorretas:** Bat_V e Char_V 10x acima.

Esses problemas compromotem análises de correlação e modelos. O tratamento foi essencial para evitar vieses.

## Hipóteses

**1. Variações anormais antecipam falhas.**
    - Exemplo: queda repentina de RPM → falha iminente.
    - Justificativa: comportamento esperado é estável; anomalias são exceções críticas.

**2. Agregação em 15s representa melhor o sistema.**
    - Justificativa: reduz ruído sem perder eventos importantes. Intervalo escolhido por ser próximo à média das frequências de medições das máquinas.

**3. Relações hidráulicas indicam desempenho.**
    - Exemplo: `Recalque – Sucção = Carga Hidráulica.`
    - Justificativa: Alterações nessas relações podem indicar desgaste, perda de eficiência ou até falhas mecânicas no sistema hidráulico.

**4. Relações motores refletem eficiência.**
    - Exemplo: `Oil_P / RPM`
    - Justificativa: Desequilíbrio nessas relações pode revelar sobrecarfa, baixa eficiência ou risco de falha.

## Tratamento dos Dados

**Passos aplicados:**

**1. Correção de valores extremos** → > 2bi viraram 0 (+ flag via `running`).

```python
def treat_high_values(df: pd.DataFrame, max_limit: int) -> None:
    df['running'] = np.where(df['value'] > max_limit, 0, 1)
    df['value'] = np.where(df['value'] > max_limit, 0, df['value'])
```

**2. Remoção de dados duplicados e NaN de linha inteira**

```python
def remove_duplicates_and_nan(df: pd.DataFrame) -> pd.DataFrame:
    df_cleaned = df.drop_duplicates().dropna()
    return df_cleaned

df_itu_415 = remove_duplicates_and_nan(df_itu_415)
df_itu_693 = remove_duplicates_and_nan(df_itu_693)
```

**3. Ajuste de escala de bateria/alternador (÷10)**

```python
def fix_battery_and_alternator_values(df: pd.DataFrame) -> None:
    df.loc[df["resource"] == "Bat_V", "value"]  = df.loc[df["resource"] == "Bat_V", "value"] / 10
    df.loc[df["resource"] == "Char_V", "value"] = df.loc[df["resource"] == "Char_V", "value"] / 10

fix_battery_and_alternator_values(df_itu_415)
fix_battery_and_alternator_values(df_itu_693)
```

**4. Conversão de timestamp para `datetime`**

```python
df_itu_415['timestamp'] = pd.to_datetime(df_itu_415['timestamp'])
df_itu_693['timestamp'] = pd.to_datetime(df_itu_693['timestamp'])
```

**5. Transformação `long → wide` (pivot) + Resamples para padronizar medições**

```python
def pivot_df(df: pd.DataFrame, resample_seconds: int = 60) -> pd.DataFrame:
    df_wide = (
        df.pivot_table(
            index=["timestamp", "motor_pump"],
            columns="resource",
            values="value",
            aggfunc="mean"
        )
        .reset_index()
    )

    df_running = df[["timestamp", "motor_pump", "running"]]
    df_wide = df_wide.merge(df_running, on=["timestamp", "motor_pump"], how="left")
    df_wide = df_wide.set_index("timestamp")

    resampled = []
    for pump_id, group in df_wide.groupby("motor_pump"):
        g = (
            group
            .resample(f"{resample_seconds}s")
            .mean(numeric_only=True)
            .ffill()
        )
        g["running"] = g["running"].round().astype(int)
        g["motor_pump"] = pump_id
        resampled.append(g)

    df_wide = pd.concat(resampled).reset_index()
    return df_wide.drop_duplicates().fillna(df.mode().iloc[0])

df_itu_415_wide = pivot_df(df=df_itu_415, resample_seconds=15)
df_itu_693_wide = pivot_df(df=df_itu_693, resample_seconds=15)
```

**6. Tratamentos dos valores ausentes (NaN)**

Os valores ausentes foram tratados de duas principais formas:

    1. Preenchimento com valor mais frequente (moda)
        - Dentro do `RemoveDuplicatesAndNaN` (classe): para cada coluna com `NaN`, preenche com `col.mode().iloc[0]`.

    ```python

    def transform(self, X: pd.DataFrame):
        df = X.copy()
        df_filled = df.apply(lambda col: col.fillna(col.mode().iloc[0]) if col.isnull().any() else col)
        df_cleaned = df_filled.drop_duplicates()
        return df_cleaned
    ```
    2. Forward fill no resample (continuidade temporal)
        - Durante o pivot/resample por bomba: após mean(), aplica ffill() para carregar o último valor válido.

        ```python
        g = (group.resample(f"{self.resample_seconds}s").mean(numeric_only=True).ffill())
        ```
        

**7. Remoção de colunas zeradas (pós-pivot)**

```python
def remove_columns_with_only_zeroes(df: pd.DataFrame) -> pd.DataFrame:
    zero_columns = (df == 0).all()
    columns_to_keep = zero_columns[~zero_columns].index
    df_cleaned = df[columns_to_keep]
    return df_cleaned

df_itu_415_wide = remove_columns_with_only_zeroes(df_itu_415_wide)
df_itu_693_wide = remove_columns_with_only_zeroes(df_itu_693_wide)
```

**8. Normalização (z-score) para padronizar escalas**

```python
scaler = GenericScaler(exclude_columns=['timestamp','motor_pump','running'])
df_itu_415_ready = scaler.fit_transform(df_itu_415_wide)
df_itu_693_ready = scaler.fit_transform(df_itu_693_wide)
```

Cada decisão foi tomada para que os dados fossem consistentes, comparáveis entre bombas e úteis para modelos.

## Engenharia de Features

Durante o processamento, foram criadas novas colunas para enriquecer a análise e capturar relações físicas importantes:


- **Minutes Running (`minutes_running`)**  
  - Representa o tempo contínuo de operação da bomba (em minutos).  
  - Permite avaliar degradação ao longo do tempo e calcular taxas (ex.: consumo por minuto).

- **Variations (`*_variation`, `*_variation_percentage`)**  
  - Calculam a variação absoluta e percentual entre medições consecutivas.  
  - Servem para identificar mudanças bruscas que podem sinalizar anomalias.

- **Hydraulic Columns (`Hydraulic_Head`, `Head_per_RPM`, `Head_trend_per_minutes`)**  
  - Criadas a partir das pressões de sucção (kPa) e recalque (mca), quando disponíveis.  
  - Medem a energia transferida ao fluido e ajudam a identificar perda de eficiência ou cavitação.

- **Motor Columns (`OilP_per_RPM`, `CoolT_per_RPM`, `Fuel_rate`, `Fuel_efficiency`)**  
  - Relacionam parâmetros do motor (pressão de óleo, temperatura, combustível) com RPM e desempenho hidráulico.  
  - Permitem avaliar eficiência e identificar sobrecargas ou falhas de lubrificação/arrefecimento.  
  - Obs.: `Fuel_rate` e `Fuel_efficiency` ficaram inutilizados nesta sprint, pois a coluna `Fuel_Con` veio zerada após tratamento.

- **Target (quando aplicável)**  
  - Criado para uso em modelos supervisionados.  
  - Nesta sprint, a análise foi focada em modelos não supervisionados, mas o target foi deixado preparado para evoluções futuras.

## Pipeline  

Com base na exploração e no tratamento realizados, foi desenvolvido um **pipeline** de pré-processamento.  
Os detalhes completos estão descritos em uma **seção específica desta documentação**.  

## Limitações

- Acesso restrito → trabalhamos apenas com CSVs estáticos.

- Ausência de target robusto → impossibilitou bons resultados para modelos supervisionados.

- Diferenças entre bombas → exigem padronização.

## Próximos Passos

- Conectar ao **broker** para coletar dados em tempo real.  
- Estruturar um **target supervisionado** confiável, a partir de dados mais completos e organizados.  
- Validar as hipóteses levantadas (variações, relações hidráulicas e motoras) com novos dados.  
- Aprimorar os testes de modelos supervisionados em paralelo aos não supervisionados.  

## Conclusão  

A exploração dos dados revelou desafios importantes, como assincronia entre sensores, valores ausentes e outliers, além de diferenças estruturais entre bombas.  
O tratamento e a engenharia de features transformaram dados crus em informações consistentes, capazes de representar de forma mais fiel os fenômenos físicos de operação das bombas.  
A construção da pipeline consolidou essas etapas em um fluxo único, garantindo reprodutibilidade e preparando terreno para análises mais avançadas em modelos de Machine Learning.  
Apesar das limitações do dataset atual, já foi possível levantar hipóteses relevantes e estruturar uma base sólida para evoluir em direção a modelos supervisionados e aplicações práticas de predição de falhas.








