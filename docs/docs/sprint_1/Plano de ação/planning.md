---
title: Plano de ação
sidebar_label: Plano de ação
sidebar_position: 0
---

# Plano de ação

Um plano de ação consiste em uma série de etapas, visando o planejamento de como desenvolver um produto a partir dos materiais, dados e ferramentas disponíveis.
Este plano de ação visa o desenvolvimento de um modelo preditivo para as motobombas da Itubombas, seguindo uma abordagem estruturada em dois níveis, conforme proposto e validado nos artigos.

## Preparação dos dados

A princípio, como parte inicial do desenvolvimento de um modelo de machine learning, é essencial entender com quais dados você está lidando, logo, os dados devem ser analisados, procurando features importantes para alcançar seu objetivo, além disso, essa análise inicial é importante para tomar nota de alguns pontos, como, se a quantidade de valores é suficiente, quais são as features mais importantes, se os tipos de dados de cada feature estão corretos, etc.

Após a pesquisa e entendimento dos dados, se torna necessária a preparação dos dados, passando pelos processos de limpeza, pré-processamento, extração e seleção de features:

- **Implementar processos de limpeza e pré-processamento de dados ruidosos:** Isso inclui preenchimento de valores ausentes, remoção de falhas de sensor e normalização
- **Realizar a extração de features significativas a partir das medições brutas dos sensores:** Isso pode envolver agregações em domínios de tempo ou frequência (média, máximo, mínimo, desvio padrão, etc) sobre janelas de tempo, como a média móvel de 12 horas utilizada no estudo de caso
- **Aplicar seleção de features para identificar as features mais preditivas e reduzir a dimensionalidade:** De forma a simplificar o modelo e melhorar a eficiência computacional, permitindo que, mesmo um modelo simples possa ser eficaz, através da escolha das melhores features para o contexto.

## Nível 1 - Indicador de saúde

O Indicador de Saúde é uma métrica contínua construída a partir dos dados de sensores das motobombas, com o objetivo de monitorar e prever o estado operacional. Ele consolida múltiplas variáveis em um índice único, permitindo identificar condições saudáveis ou próximas da falha, apoiando a manutenção preventiva, reduzindo custos e aumentando a confiabilidade.

#### Metodologia e interpretação

O indicador utiliza onze variáveis principais, como pressão e nível de óleo, temperatura da água, RPM e histórico de operação. Após limpeza e extração de características estatísticas, aplica-se o algoritmo Random Forest para classificar o estado da máquina como saudável ou próximo da falha. A definição da janela de falha é ajustada como hiperparâmetro para definir o horizonte de risco.

Valores altos indicam operação estável, enquanto valores próximos ao limite sinalizam maior risco de falha. O sistema também destaca quais variáveis, como RPM ou pressão de óleo, mais contribuíram para o risco.

#### Validação e Métricas

* Estratégia de validação por máquina completa, garantindo robustez em cenários reais.
* Métricas de desempenho: Recall e F1-Score para falhas, além de Business Score (Bscore) para avaliar a antecipação dos alarmes.

#### Benefícios

* Antecipação de falhas com base em dados reais de operação.
* Redução de custos com paradas inesperadas e manutenção reativa.
* Aumento da satisfação do cliente, pela continuidade operacional.

## Nível 2 – Tomada de Decisão

O modelo de tomada de decisão é responsável por transformar o indicador de saúde em uma ferramenta prática de suporte à decisão. Enquanto o Nível 1 concentra-se em traduzir os dados brutos de sensores em um índice contínuo que representa o estado da máquina, o Nível 2 interpreta esse índice e gera alarmes ou recomendações acionáveis para as equipes de operação e manutenção.

#### Metodologia e interpretação

O processo do modelo de tomada de decisão é baseado na definição de limiares otimizados sobre o indicador de saúde. Quando o valor ultrapassa esse limite, um alarme é disparado. Para melhorar a robustez, são aplicadas funções de agregação ao longo do tempo, como médias móveis exponenciais, que suavizam variações momentâneas e destacam tendências reais de degradação. Essa abordagem reduz alarmes falsos e garante que apenas situações consistentes de risco acionem o sistema de alerta. O Nível 2 fornece respostas diretas às perguntas de negócio: se a operação atual está saudável ou não, qual a probabilidade de falha caso a operação continue no mesmo padrão e, em alguns casos, qual componente (motor, bomba ou outro subsistema) está mais suscetível à falha. Isso permite transformar o indicador em ações concretas, como programar uma parada de manutenção ou reforçar o monitoramento de determinada variável.

#### Validação e Métricas

A validação do Nível 2 envolve medir a efetividade dos alarmes gerados. Para isso, são utilizadas métricas como Recall, que avalia se o sistema realmente detecta falhas reais, e F1-Score, que equilibra precisão e recall em cenários de dados desbalanceados. O Business Score (Bscore) também é aplicado para medir a pontualidade das previsões, verificando se os alarmes são emitidos dentro do intervalo ótimo de antecedência (por exemplo, até 7 dias antes da falha).

#### Benefícios

Com o Nível 2, o indicador de saúde deixa de ser apenas uma métrica técnica e passa a ser um mecanismo de decisão operacional. Isso garante maior confiabilidade nos alarmes, reduz paradas inesperadas e possibilita uma manutenção proativa mais eficiente. Além disso, a integração com os times de operações e serviços permite alinhar tecnologia e prática de campo, aumentando a eficácia das ações e a satisfação do cliente.

---

## Referências

Este plano de ação foi desenvolvido com base no kick-off com a empresa parceira ItuBombas, além dos artigos recomendados pelo professor orientador, sendo eles:

- [A two-level machine learning framework for predictive maintenance: comparison of learning formulations](https://arxiv.org/pdf/2204.10083)
- [On the use of Machine Learning for predictive maintenance of power transformers](https://sbic.org.br/wp-content/uploads/2023/10/pdf/CBIC_2023_paper031.pdf)

Esses dois artigos são utilizados como referência teórica, você pode entender melhor sobre cada um deles e o aprendizado utilizado para construir o plano de ação nesta página (colocar link para página de referência teórica)
