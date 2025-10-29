# Algoritmos e abordagens testadas para as predições

## 1. Modelos Testados

### Previsão de RUL (Remaining Useful Life)

* **Abordagem**: Redes Neurais Recorrentes (RNN, LSTM, GRU)
* **Objetivo**: Estimar o tempo restante até a falha da bomba (em horas ou ciclos)
* **Resultado**:

  * Baixa precisão prática
  * Curvas de predição instáveis
  * Decisão: **não seguir adiante**


### Classificação por Clusters

* **Abordagem**: Clusterização a partir do Fuzzy C-Means (FCM) e modelo de classificação com base na coluna target criada a partir do primeiro.
* **Objetivo**: Separar o funcionamento em três estados:

  * Funcionamento normal
  * Oscilação
  * Falha iminente
* **Resultado**:

  * Clusters bem definidos
  * Redundância de modelos


### Classificação Multirrótulo

* **Abordagem**: GRU multissaída (rede neural recorrente)
* **Objetivo**: Prever índices de saúde independentes (Lubrificação, Hidráulico, etc.)
* **Resultado**:

  * Melhor desempenho geral
  * Métricas de erro baixas
  * Interpretação direta para manutenção preditiva


## 2. Modelo Escolhido: GRU Multirrótulo

* **Arquitetura**:

  * 2 camadas GRU (64 unidades cada)
  * Dropout para regularização
  * Saída densa com 2 neurônios (Lubrificação e Hidráulico)

* **Justificativa**:

  * Melhor equilíbrio entre performance e interpretabilidade
  * Captura padrões temporais sem overfitting evidente
  * Saídas diretamente interpretáveis como índices de saúde


## 3. Como os Índices de Saúde São Calculados

Cada subsistema recebe um índice de 0 a 100. Quanto mais perto de 100, melhor o funcionamento.

#### Lubrificação

* Sensores usados: pressão do óleo (Oil_P) e nível do óleo (Oil_L).

* Cálculo:

    * Normalizamos cada sensor para variar de 0 a 1 (valores baixos = ruins, altos = bons).

    * Fazemos uma média ponderada: 60% pressão + 40% nível.

    * Multiplicamos por 100 para dar o índice final.

*  Se a pressão e o nível estão dentro do esperado → índice perto de 100.
*  Se caem muito → índice cai para perto de 0.

#### Hidráulico

* Sensores usados: pressão de recalque (Recalque) e pressão de sucção (Succao).

* Cálculo:

    * Normalizamos cada sensor.

    * Fazemos uma média ponderada: 70% recalque + 30% sucção.

    * Escalamos para 0–100.

* Pressões dentro da faixa → índice alto.
* Pressões anormais → índice baixo.

#### Térmico (testado, mas não usado no modelo final)

* Sensor usado: temperatura do líquido (Cool_T).

* Cálculo: quanto mais próximo do limite máximo, menor o índice.

#### Elétrico (testado, mas não usado no modelo final)

* Sensores usados: tensão da bateria (Bat_V) e do alternador (Char_V).

* Cálculo: cada tensão tem uma faixa considerada ideal. Se fica fora dela, o índice cai.


## 4. Métricas Finais (GRU Multirrótulo)

### Teste (dados nunca vistos)

* **Lubrificação**

  * MAE ≈ 0.67
  * RMSE ≈ 2.00
  * R² ≈ 0.987

* **Hidráulico**

  * MAE ≈ 0.67
  * RMSE ≈ 1.39
  * R² ≈ 0.988

**Interpretação**:

* Erro médio < 1 ponto numa escala 0–100
* Mais de 98% da variância explicada
* Modelo generaliza bem sem sinais de overfitting crítico


## 5. Conclusão

* O **GRU multirrótulo** foi o melhor modelo, unindo **boa precisão, interpretabilidade e robustez temporal**
* Os índices de saúde calculados permitem **monitoramento contínuo** e análise granular por subsistema
* Subsistemas elétrico e térmico não tiveram boa performance devido à uniformidade excessiva de dados
* **Próximos passos**:
    * Calibrar os índices para que o regime saudável fique entre **80–90 pontos**, alinhando com a semântica esperada de “saúde alta”
    * Tentar criar mais instâncias sintéticas (através de técnicas parecidas com o SMOTE) para melhorar os subsistemas
    * Utilizar os novos dados coletados pelo broker e datasets externos para cruzar dados e garantir maior diversidade de dados
