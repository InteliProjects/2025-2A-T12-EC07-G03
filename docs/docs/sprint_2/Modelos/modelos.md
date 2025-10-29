---
title: Modelos
sidebar_label: Modelos
sidebar_position: 1
---

# Modelos desenvolvidos

O principal objetivo da Sprint 2 foi a etapa de desenvolvimento e teste de diferentes modelos de Machine Learning. Durante esta fase, nosso foco esteve na experimentação com diversas abordagens e algoritmos para determinar a solução mais eficaz para o problema em questão, pensando sempre em escalabilidade.

## Visão Geral dos Modelos

Durante o período de desenvolvimento, a equipe trabalhou com duas categorias principais de modelos: **Modelos Supervisionados** e **Modelos Não Supervisionados**

- **Modelos Supervisionados**: São utilizados quando há dados de entrada e seus respectivos rótulos (ou saídas) conhecidos. A ideia baseia-se em treinar um modelo a partir desses dados rotulados para que ele consiga prever a saida para novos dados ainda não vistos.

Nessa categoria, um modelo de classificação foi implementado e testado, usado para categorizar a saúde da máquina analisada.

- **Modelos Não Supervisionados**: São aplicados em cenários onde os dados não possuem rótulos. A intenção é permitir que o próprio modelo descubra padrões, estruturas e relações ocultas nos dados por conta própria. 

Nessa categoria, foram implementados e testados dois modelos: um algoritmo de Agrupamento (Clustering) e um algoritmo de Associação.

### Uso de AutoML

Em complemento à abordagem manual de desenvolvimento, ferramentas de AutoML foram utilizadas em alguns modelos, permitindo automatizar o processo de seleção de algoritmos, o pré-processamento de dados e o ajuste de hiperparâmetros, otimizando o processo e acelerando a fase de experimentação.

## Considerações Finais

Com o teste de diferentes modelos e ferramentas, observa-se um grande avanço no desenvolvimento com a validação das abordagens de modelagem, gerando valiosos insights que irão orientar a próxima fase do projeto. Assim, foi possível explorar e testar com sucesso modelos complexos e estratégicos, como o Isolation Forest para detecção de anomalias, o Fuzzy C-Means que se mostrou promissor na clusterização dos dados, e também um modelo de classificação supervisionado para teste dos rótulos.

Além dos modelos mencionados, vale ressaltar que modelos de séries temporais multivariadas foram estudados e analisados para futuros testes. 

Com base nisso, o refinamento dos modelos e os novos experimentos buscam fornecer não somente uma identificação precisa de saúde ou anomalias, mas também de entregar uma previsão de tempo de falha que seja fiel e eficiente para o parceiro.