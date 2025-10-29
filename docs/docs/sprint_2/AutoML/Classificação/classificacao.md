---
title: Modelo de Classificação com AutoML
sidebar_label: Modelo de Classificação com AutoML
sidebar_position: 1
---

# Modelo de Classificação com AutoML

## Introdução e Objetivos

&emsp;Este documento detalha os resultados dos testes de modelos de classificação utilizando a ferramenta AutoML, especificamente a biblioteca PyCaret, como parte do Sprint 2 do projeto. O objetivo principal desta fase não era alcançar um modelo de classificação perfeito ou com alta performance imediatamente, mas sim explorar as capacidades do AutoML para identificar rapidamente modelos candidatos e suas métricas iniciais, mesmo que os resultados fossem subótimos ou inesperados. A intenção era validar a metodologia de uso do AutoML e entender o comportamento dos modelos em um cenário com dados desafiadores.

## Metodologia e Preparação dos Dados

&emsp;Para os testes de classificação, foi utilizada a biblioteca PyCaret, que permite a rápida experimentação com diversos modelos de Machine Learning. A abordagem consistiu em treinar e avaliar múltiplos algoritmos de classificação em um conjunto de dados específico. No entanto, a preparação dos dados para este experimento apresentou um desafio significativo que impactou diretamente os resultados.

### Aprendizado Supervisionado vs. Não Supervisionado

&emsp;É importante distinguir entre dois tipos principais de aprendizado de máquina:

*   **Aprendizado Supervisionado:** Este é o tipo de aprendizado mais comum para problemas de classificação. Nele, o algoritmo é 'supervisionado' por um conjunto de dados de treinamento que já contém os 'rótulos' (as classes corretas) para cada exemplo. O modelo aprende a mapear as características de entrada para as classes de saída com base nesses exemplos rotulados. No caso atual, o modelo foi treinado com dados onde já sabíamos se a máquina estava em 'falha' (target=1) ou 'operação normal' (target=0). A maioria dos modelos de classificação, como Regressão Logística, Árvores de Decisão e Máquinas de Vetores de Suporte (SVM), são algoritmos de aprendizado supervisionado.

*   **Aprendizado Não Supervisionado:** Ao contrário do aprendizado supervisionado, no aprendizado não supervisionado, o algoritmo recebe dados que não possuem rótulos predefinidos. O objetivo é encontrar padrões, estruturas ou agrupamentos inerentes aos dados. Técnicas comuns incluem clustering (agrupamento de dados em categorias) e redução de dimensionalidade. Este tipo de aprendizado é útil para explorar dados, identificar anomalias ou segmentar clientes, mas não é diretamente aplicável para prever uma classe específica sem rótulos de treinamento.

&emsp;No contexto deste projeto, diversos modelos e técnicas diferentes podem ser utilizadas. Neste seção da documentação, será falado sobre uma tentativa de implementar um modelo supervisionado de classificação, porém outras seções demonstram o funcionamento de outros tipos de modelos.

## Modelos de Classificação

&emsp;Modelos de classificação são uma categoria de algoritmos de Machine Learning cujo objetivo é prever a qual categoria (ou classe) um determinado item de dados pertence. Por exemplo, em um contexto médico, um modelo de classificação pode prever se um paciente tem uma doença (classe 'doente') ou não (classe 'saudável') com base em seus sintomas e resultados de exames. No presente projeto, o objetivo é classificar se uma máquina está em estado de 'falha' ou 'operação normal'.

### Desafio na Coleta e Preparação dos Dados

&emsp;A principal limitação encontrada foi a ausência de um conjunto de dados que contivesse tanto dados de operação normal quanto dados de falha para a **mesma máquina**. Para contornar essa limitação, optou-se por uma abordagem alternativa:

*   **Dados de Operação Normal:** Coletados da máquina `itu415`.
*   **Dados de Falha:** Coletados da máquina `itu844`.

É importante notar que, embora ambas as máquinas utilizem o mesmo tipo de motor, elas são entidades físicas distintas. A variável `target` (alvo) para a classificação foi criada artificialmente com base na origem do dataset:

*   Registros da máquina `itu844` foram rotulados com `target = 1` (indicando falha).
*   Registros da máquina `itu415` foram rotulados com `target = 0` (indicando operação normal).

&emsp;Os dois datasets foram então concatenados e utilizados para treinar os modelos. Essa metodologia, embora necessária devido à indisponibilidade de dados ideais, levou a um cenário onde os modelos aprenderam a **diferenciar entre os dois datasets de máquinas distintas** em vez de, de fato, identificar padrões de falha e operação normal dentro de um contexto unificado. Isso resultou em métricas de desempenho enganosamente altas, conforme detalhado na próxima seção.

## Resultados e Métricas

&emsp;Os testes com PyCaret resultaram em métricas de desempenho que, à primeira vista, parecem excelentes, com a maioria dos modelos atingindo 100% de acurácia, AUC, Recall, Precisão e F1-Score. No entanto, como antecipado na seção de metodologia, esses resultados são um artefato da forma como o dataset foi construído e não refletem a capacidade real dos modelos em prever falhas em um cenário prático.

A tabela a seguir apresenta as métricas de desempenho para cada modelo testado:

| Model | Accuracy | AUC | Recall | Prec. | F1 | Kappa | MCC | TT (Sec) |
|---|---|---|---|---|---|---|---|---|
| lr | Logistic Regression | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 11.6400 |
| knn | K Neighbors Classifier | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9999 | 0.9999 | 23.6700 |
| dt | Decision Tree Classifier | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.1520 |
| ridge | Ridge Classifier | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0940 |
| rf | Random Forest Classifier | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9120 |
| ada | Ada Boost Classifier | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.3100 |
| gbc | Gradient Boosting Classifier | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 2.4810 |
| lda | Linear Discriminant Analysis | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.2720 |
| et | Extra Trees Classifier | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0480 |
| lightgbm | Light Gradient Boosting Machine | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.4070 |
| nb | Naive Bayes | 0.9999 | 0.9999 | 0.9997 | 1.0000 | 0.9999 | 0.9998 | 0.9998 | 0.1140 |
| svm | SVM - Linear Kernel | 0.9986 | 0.9979 | 0.9992 | 0.9964 | 0.9978 | 0.9968 | 0.9968 | 0.2690 |
| qda | Quadratic Discriminant Analysis | 0.3192 | 0.0000 | 1.0000 | 0.3192 | 0.4839 | 0.0000 | 0.0000 | 0.4090 |
| dummy | Dummy Classifier | 0.6808 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.1310 |

### Análise dos Resultados

&emsp;A performance quase perfeita da maioria dos modelos (acurácia de 100%) é um indicativo claro de que eles não estão aprendendo a complexidade da falha da máquina, mas sim a distinção entre as duas fontes de dados (`itu415` e `itu844`). O modelo está, essencialmente, atuando como um classificador de origem de dados, o que é trivial dado que as características de cada máquina, mesmo que sutis, são inerentemente diferentes e facilmente distinguíveis pelos algoritmos.

&emsp;Os modelos `QDA` (Quadratic Discriminant Analysis) e `Dummy Classifier` apresentaram métricas significativamente mais baixas, o que é esperado. O `Dummy Classifier` serve como uma linha de base, mostrando o desempenho de um classificador que não aprende nada (ou aprende estratégias muito simples, como prever a classe majoritária). O `QDA` pode ter tido dificuldades em modelar a distribuição dos dados de forma a diferenciar as classes de maneira eficaz, ou pode ser mais sensível à forma como os dados foram artificialmente separados.

&emsp;Este cenário reforça a importância da qualidade e representatividade dos dados de treinamento. Quando o objetivo é prever falhas em uma máquina específica, é fundamental que o dataset contenha exemplos de operação normal e de falha da **mesma máquina**, ou de máquinas com características e comportamentos de falha idênticos, para que o modelo possa aprender os padrões relevantes e generalizar para novas situações.

## Conclusão

&emsp;Os testes iniciais com AutoML, embora tenham gerado métricas aparentemente perfeitas, serviram para validar a metodologia de experimentação rápida e, mais importante, para destacar a **crítica dependência da qualidade e representatividade dos dados** para o sucesso de modelos de Machine Learning. A principal lição aprendida é que a criação de uma variável `target` artificial a partir de máquinas distintas, mesmo que com motores semelhantes, leva a modelos que aprendem a diferenciar as fontes de dados em vez de padrões de falha reais.
