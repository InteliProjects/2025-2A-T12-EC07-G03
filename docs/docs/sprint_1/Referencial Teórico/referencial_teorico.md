---
title: Referencial Teórico
sidebar_label: Referencial Teórico
sidebar_position: 3
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Referencial Teórico

## Introdução

&emsp;Para fundamentar o desenvolvimento da solução de manutenção preditiva para as motobombas da Itubombas, foi realizada uma análise de artigos científicos. O principal objetivo deste estudo é compreender como dados de máquinas são tipicamente utilizados em projetos de *Machine Learning* para predição de falhas, identificar as melhores práticas do setor e absorver conhecimentos técnicos que possam ser aplicados diretamente ao nosso desafio.

&emsp;A análise foca em como a comunidade científica aborda problemas semelhantes, desde a extração e seleção de características (features) dos dados de sensores até a formulação dos modelos preditivos e sua validação. A seguir, apresentamos os principais aprendizados obtidos a partir de dois artigos relevantes na área.

---

## Análise dos Artigos

### Artigo 1: "A two-level machine learning framework for predictive maintenance: comparison of learning formulations"

&emsp;Este artigo, de autoria de Hamaide et al. (2022), foi fundamental para a estruturação da nossa abordagem. Ele propõe um *framework* de manutenção preditiva em dois níveis, o que se alinha perfeitamente com os objetivos do projeto Itubombas.

*   **Fonte:** Hamaide, V., Joassin, D., Castin, L., & Glineur, F. (2022). *A two-level machine learning framework for predictive maintenance: comparison of learning formulations*. arXiv preprint arXiv:2204.10083. Disponível no [link](https://arxiv.org/pdf/2204.10083)

#### Principais Aprendizados:
&emsp;O artigo compara diferentes formulações de aprendizado de máquina (univariada, detecção de anomalia e supervisionada) para um caso de uso com dados de uma máquina rotativa real. Os principais insights para o nosso projeto foram:

1.  **Framework em Dois Níveis:** A abordagem proposta pelos autores valida nossa arquitetura de solução. O primeiro nível transforma dados brutos de sensores em um "indicador de saúde" único e contínuo. O segundo nível utiliza esse indicador para tomar uma decisão, como disparar um alarme. Isso simplifica o monitoramento e a tomada de decisão para a equipe de Operações e Serviços.
2.  **Formulação do Problema:** O estudo mostra que modelos de **classificação binária** (dividindo o tempo de operação em "saudável" e "próximo da falha") apresentaram os melhores resultados. Isso nos fornece um ponto de partida sólido para a modelagem, em vez de tentarmos prever o "tempo de vida útil restante" (RUL), que o artigo aponta como sendo mais complexo e menos eficaz em cenários reais.
3.  **Importância da Janela de Falha:** A definição do horizonte de tempo que é considerado como "próximo da falha" (por exemplo, os últimos 10 dias de operação) é um hiperparâmetro muito importante. O artigo demonstra que uma janela bem escolhida melhora significativamente a performance do modelo, um aprendizado que aplicaremos no ajuste fino do nosso sistema.
4.  **Simplicidade é Eficaz:** Surpreendentemente, um modelo univariado simples, baseado na característica mais preditiva, já apresentou um bom desempenho. Isso reforça a importância da etapa de **seleção de features**, mostrando que nem sempre o modelo mais complexo é o melhor.

### Artigo 2: "On the use of Machine Learning for predictive maintenance of power transformers"

&emsp;Este artigo, de autoria de Pacheco et al. (2023), aborda a manutenção preditiva em um contexto de ativos de alto valor no setor elétrico brasileiro (transformadores de potência), um cenário análogo ao da Itubombas, onde a falha de um equipamento gera custos elevados e impacto operacional.

*   **Fonte:** Pacheco, C., Paes, V., de Carvalho, M., Lopes, F., Machado, G., Garcia, A., ... & Marotti, A. (2023). *On the use of Machine Learning for predictive maintenance of power transformers*. Anais do XVI Brazilian Conference on Computational Intelligence (CBIC). Disponível no [link](https://sbic.org.br/wp-content/uploads/2023/10/pdf/CBIC_2023_paper031.pdf)

#### Principais Aprendizados:
&emsp;O trabalho descreve a criação de dois indicadores de risco de falha (CAI e EFRI) baseados em dados distintos (cromatográficos e de sensores SCADA). As lições mais valiosas para o projeto Itubombas são:

1.  **Validação com Dados do Mundo Real:** O artigo detalha um fluxo de trabalho completo, desde a limpeza e pré-processamento de dados ruidosos até a validação do modelo. A metodologia para lidar com dados desbalanceados (poucas falhas e muitas operações normais), utilizando técnicas como SMOTE, é diretamente aplicável ao nosso conjunto de dados.
2.  **Uso do Algoritmo Random Forest:** Os autores obtiveram excelentes resultados com o algoritmo *Random Forest*, que superou métodos clássicos de análise. Isso nos dá confiança para priorizar este algoritmo em nossos experimentos, pois ele é robusto, lida bem com interações complexas entre variáveis e fornece a importância de cada *feature* (ex: RPM, pressão do óleo), o que ajuda a responder à pergunta "Qual a parte da máquina sob risco?".
3.  **Métricas de Avaliação:** O artigo enfatiza a importância de usar métricas de avaliação adequadas para problemas de classificação desbalanceados, como **Recall** e **F1-Score** para a classe de falha, em vez de apenas acurácia. Adotaremos essa prática para garantir que nosso modelo seja verdadeiramente eficaz em detectar falhas, que é o evento de maior interesse.

---

## Conclusão

&emsp;A análise do referencial teórico foi extremamente valiosa para guiar as decisões técnicas do projeto. O primeiro artigo nos forneceu um *framework* conceitual sólido e uma direção clara sobre qual tipo de modelo de *Machine Learning* (classificação binária) tem maior probabilidade de sucesso. O segundo artigo nos ofereceu um roteiro prático, validado no contexto industrial brasileiro, sobre como tratar os dados, qual algoritmo utilizar (*Random Forest*) e como avaliar a performance do nosso modelo de forma rigorosa.

&emsp;Com base nesses aprendizados, o projeto está bem posicionado para desenvolver uma solução de manutenção preditiva que seja não apenas tecnicamente robusta, mas também diretamente alinhada com as necessidades operacionais da Itubombas, transformando dados em ações proativas para reduzir custos e aumentar a satisfação dos clientes.
