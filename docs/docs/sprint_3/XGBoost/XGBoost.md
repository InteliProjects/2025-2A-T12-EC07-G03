# Modelo XGBoost

## 1. Objetivo do Projeto

&emsp;O principal objetivo deste projeto é desenvolver um modelo de *machine learning* capaz de prever a ocorrência de **pré-falhas** em equipamentos, com base em dados operacionais, especialmente a **variação de RPM**. A detecção precoce de pré-falhas é importante para implementar estratégias de manutenção preditiva, minimizando o tempo de inatividade não planejado, reduzindo custos de reparo e aumentando a vida útil dos ativos. Levando isso em consideração e também tudo o que foi desenvolvido nas outras sprints, foi feito um experimento utilizando o modelo XGBoost. Tal modelo foi escolhido devido à sua robustez, eficiência e capacidade de lidar com dados complexos, características essenciais para um problema de classificação em um contexto industrial.

### 1.1. Criação de labels
&emsp;Como iremos utilizar um modelo XGBoost, que é um modelo de classificação, é necessário que os dados possuam labels (classificações). De acordo com dados fornecidos pelo parceiro, uma falha pode ser identificada com, por exemplo, uma queda brusca de RPM. Assim, criamos e utilizamos uma coluna chamada `Eng_RPM_variation_percentage`, que mede a variação percentual do RPM da máquina de uma linha para a outra. Assim, podemos ver as linhas em que essa coluna é menor ou igual a -70%. Considerando que cada linha tem um espaçamento temporal de 12 segundos, uma queda de 70% da velocidade de rotação da máquina em 12 segundos pode ser considerado como falha. Após isso, os dados de 30 minutos antes dessa queda crítica são classificados como "pré-falha". Assim, criamos duas labels, uma para "pré-falha" e outra para "normal", e é justamente essa a variável que o nosso modelo irá prever.

## 2. Implementação do Modelo XGBoost

&emsp;O modelo de classificação foi implementado utilizando a biblioteca `xgboost` em Python. A otimização dos hiperparâmetros foi realizada através de `GridSearchCV` para encontrar a melhor combinação que maximizasse o desempenho do modelo. Abaixo, segue o trecho de código que representa a estrutura do modelo e a busca pelos melhores parâmetros:

```python
import xgboost as xgb
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score


# Definindo o modelo XGBoost
model = xgb.XGBClassifier(
    objective='binary:logistic', # Para classificação binária
    eval_metric='logloss',       # Métrica de avaliação
    use_label_encoder=False      # Para evitar warning futuro
)

# Definindo o grid de hiperparâmetros para busca
param_grid = {
    'n_estimators': [100, 200, 300], # Número de árvores
    'learning_rate': [0.01, 0.1, 0.2], # Taxa de aprendizado
    'max_depth': [3, 5, 7],          # Profundidade máxima da árvore
    'subsample': [0.7, 0.8, 0.9],    # Proporção de amostras para treinar cada árvore
    'colsample_bytree': [0.7, 0.8, 0.9] # Proporção de features para treinar cada árvore
}

# Configurando o GridSearchCV
grid_search = GridSearchCV(
    estimator=model,
    param_grid=param_grid,
    scoring='f1',      # Métrica para otimização
    cv=3,              # Cross-validation com 3 folds
    verbose=1,         # Detalhes do processo
    n_jobs=-1          # Usar todos os cores disponíveis
)

# Executando a busca pelos melhores parâmetros
grid_search.fit(X_train, y_train)

# Melhores parâmetros encontrados
print(f"Melhores parâmetros: {grid_search.best_params_}")

# Melhor modelo
best_model = grid_search.best_estimator_

# Previsões no conjunto de teste
y_pred = best_model.predict(X_test)
y_proba = best_model.predict_proba(X_test)[:, 1]

# Avaliação do modelo (será detalhada na próxima seção)
# print(confusion_matrix(y_test, y_pred))
# print(classification_report(y_test, y_pred))
# print(roc_auc_score(y_test, y_proba))
```

&emsp;Este código demonstra a configuração de um modelo XGBoost para classificação binária, a definição de um espaço de busca para os hiperparâmetros e a utilização do `GridSearchCV` para encontrar a combinação ideal que otimiza a métrica F1 score. Após a identificação dos melhores parâmetros, o modelo é treinado e utilizado para fazer previsões no conjunto de teste.

## 3. Métricas de Avaliação do Modelo

&emsp;Após o treinamento e a otimização do modelo XGBoost, a avaliação de seu desempenho foi realizada utilizando um conjunto de dados de teste. As métricas de avaliação são cruciais para entender a eficácia do modelo na identificação de pré-falhas e na minimização de falsos positivos e falsos negativos.

### Matriz de Confusão

&emsp;A matriz de confusão fornece uma visão detalhada do desempenho do classificador, mostrando o número de previsões corretas e incorretas para cada classe.

```
[[73527  6005]
 [ 7537 14116]]
```

Interpretando a matriz:
*   **Verdadeiros Positivos (TP):** 14116 (Pré-Falha corretamente identificada)
*   **Verdadeiros Negativos (TN):** 73527 (Normal corretamente identificada)
*   **Falsos Positivos (FP):** 6005 (Normal classificado como Pré-Falha)
*   **Falsos Negativos (FN):** 7537 (Pré-Falha classificada como Normal)

### Relatório de Classificação

O relatório de classificação sumariza as métricas de precisão, recall e F1-score para cada classe, além da acurácia geral e médias ponderadas.

```
               precision    recall  f1-score   support

   Normal (0)       0.91      0.92      0.92     79532
Pré-Falha (1)       0.70      0.65      0.68     21653

     accuracy                           0.87    101185
    macro avg       0.80      0.79      0.80    101185
 weighted avg       0.86      0.87      0.86    101185
```

&emsp;Análise das métricas:
*   **Acurácia (Accuracy):** 0.87 (87%). Indica a proporção de previsões corretas sobre o total de previsões. Embora seja uma boa métrica geral, para problemas de classes desbalanceadas (como a detecção de pré-falhas, onde a classe 'Pré-Falha' é minoritária), outras métricas são mais relevantes.
*   **Precisão (Precision) para Pré-Falha (1):** 0.70. Dos casos que o modelo previu como 'Pré-Falha', 70% realmente eram pré-falhas. Um valor alto de precisão é importante para evitar alarmes falsos, que podem levar a intervenções desnecessárias e custos.
*   **Recall para Pré-Falha (1):** 0.65. Das pré-falhas reais, 65% foram corretamente identificadas pelo modelo. Um recall alto é importante para garantir que a maioria das pré-falhas seja detectada, minimizando o risco de falhas inesperadas.
*   **F1-Score para Pré-Falha (1):** 0.68. É a média harmônica da precisão e do recall, oferecendo um equilíbrio entre as duas métricas. Um F1-score razoável indica um bom balanço entre a capacidade de identificar pré-falhas e a de evitar falsos positivos.

### ROC AUC Score

&emsp;O ROC AUC (Receiver Operating Characteristic - Area Under the Curve) é uma métrica que avalia a capacidade do modelo de distinguir entre as classes. Um valor mais próximo de 1 indica um melhor desempenho.

```
ROC AUC Score: 0.9385
```

&emsp;Um ROC AUC de 0.9385 é um resultado bom, sugerindo que o modelo tem uma alta capacidade de separar as classes 'Normal' e 'Pré-Falha'. Isso é particularmente importante em cenários de manutenção preditiva, onde a capacidade de discriminar entre o estado normal e o estado de pré-falha é fundamental para a tomada de decisões eficazes.


## 4. Conclusão

&emsp;O modelo XGBoost desenvolvido neste projeto demonstra uma capacidade promissora na detecção de pré-falhas em equipamentos, com base em dados operacionais, notadamente a variação de RPM. As métricas de avaliação, especialmente o ROC AUC de 0.9385, indicam um alto poder discriminatório do modelo, o que é fundamental para a aplicação em manutenção preditiva.

&emsp;Apesar de um recall de 65% para a classe de pré-falha, que pode ser aprimorado em futuras iterações, a precisão de 70% para esta classe é um bom indicativo de que o modelo não gera um número excessivo de falsos positivos, o que é importante para evitar intervenções desnecessárias e otimizar os recursos de manutenção. A matriz de confusão e o relatório de classificação fornecem uma base sólida para entender os *trade-offs* do modelo e direcionar otimizações futuras, como o ajuste de *thresholds* de classificação ou a exploração de técnicas de rebalanceamento de classes.
