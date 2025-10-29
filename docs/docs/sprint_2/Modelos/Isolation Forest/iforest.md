---
title: Isolation Forest
sidebar_label: Isolation Forest
sidebar_position: 1
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Isolation Forest - Modelo não supervisionado

O Isolation Forest (ou iForest) é um modelo de Machine Learning não supervisionado, usado para detecção de anomalias (outliers). Ele é considerado "não supervisionado" porque não precisa de dados previamente rotulados como "normais" ou "anômalos" para funcionar. Seu princípio é simples e intuitivo: ele se baseia na ideia de que anomalias são raras e diferentes da maioria dos dados. Por isso, é muito mais fácil isolar uma anomalia em uma árvore de decisão do que isolar um ponto de dado "normal".

### Funcionamento do Modelo

O Isolation Forest funciona de forma similar a uma floresta de árvores de decisão. Para cada ponto de dado, ele faz o seguinte:
- **Construção das Árvores**: O modelo constrói várias árvores de decisão e, para cada árvore, ele seleciona uma amostra aleatória dos dados e divide os dados em subgrupos.
- **Isolamento de Pontos**: A divisão é feita através da escolha aleatória de uma variável e de um ponto de corte aleatório para essa variável. O processo continua até que cada ponto de dado seja isolado em seu próprio nó da árvore.
- **Avaliação**: O modelo mede o caminho que cada ponto de dado percorreu para ser isolado. Anomalias são isoladas com poucos passos (caminho curto), pois são pontos atípicos. Pontos normais precisam de muitos passos (caminho longo) para serem isolados.
- **Atribuição de Score**: Com base no caminho percorrido, o modelo atribui um "score de anomalia" para cada ponto. Quanto menor o caminho, maior o score, indicando uma maior probabilidade de ser uma anomalia.

## Análise dos Resultados

A visualização bidimensional gerada pelo PCA confirmou a teoria do iForest: os dados normais se concentraram no centro, enquanto as anomalias se espalharam, principalmente nas regiões periféricas. Essa distribuição sugere que as falhas podem ter diferentes origens, formando pequenos grupos isolados que podem representar modos específicos de falha.

<div style={{ textAlign: 'center' }}>
  <p><strong>Figura 1 - Gráficos</strong></p>
  <img 
    src={useBaseUrl('resultados.png')} 
    alt="Resultados analisados" 
    title="Resultados analisados" 
    style={{ maxWidth: '100%', height: 'auto' }}
  />
  <p>Fonte: Elaborado pelos autores (2025)</p>
</div>

A análise da variância das features (variáveis) mostrou que:

- A variável relacionada ao consumo de combustível domina a explicação da variância, reforçando sua importância como um indicador-chave.

- As variações térmicas (temperatura) e a rotação do motor também apresentaram alta relevância, indicando que um monitoramento contínuo dessas métricas é crucial.

O modelo detectou 25.295 anomalias, representando cerca de 5,0% do total de amostras analisadas. A análise dos scores de anomalia revelou uma clara separação entre os dados normais e os anômalos:
- **Comportamento Normal**: Score médio de aproximadamente -0,304 ± 0,014.
- **Comportamento Anômalo**: Score médio significativamente mais baixo, -0,620 ± 0,104.

A variabilidade dos scores também foi analisada. Os dados normais apresentaram baixa dispersão, indicando consistência no comportamento esperado, enquanto os anômalos exibiram maior variabilidade. Isso sugere a existência de diferentes intensidades e possivelmente diferentes tipos de anomalias dentro do conjunto de dados.

## Considerações Finais

O modelo Isolation Forest demonstrou um potencial excepcional para a detecção de anomalias nos dados analisados. Sua robustez estatística e eficiência em identificar padrões atípicos o tornam uma base sólida para a nossa estratégia.

A capacidade do iForest de detectar precocemente desvios no comportamento dos ativos, validada pelas métricas de desempenho e pela clara separação entre dados normais e anômalos, é um avanço significativo. Essa detecção em tempo real nos permite ir além do diagnóstico reativo e entrar na era da manutenção preditiva.

Ao avançarmos, nosso objetivo é entregar não apenas um sistema de detecção, mas uma solução completa que forneça à equipe de manutenção os insights necessários para agir proativamente, minimizando o tempo de inatividade e otimizando a operação dos ativos.