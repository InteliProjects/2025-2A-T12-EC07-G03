---
title: Arquitetura de Solução
sidebar_label: Arquitetura de Solução
sidebar_position: 1
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Arquitetura de Solução

Nesta seção buscamos apresentar a arquitetura formulada para o projeto, explorando as decisões tomadas para cada seção e as tecnologias escolhidas para tornar o projeto uma realidade.

## Diagrama Atualizado da Arquitetura

A seguir estão os componentes da arquitetura:

<div style={{textAlign:'center'}}>
    <p><strong>Figura 1 - Diagrama de arquitetura da solução</strong></p>
        <img
        src={useBaseUrl('/img/arquitetura_solucao.png')}
        alt="Persona Isac Santos"
        title="Persona Isac Santos"
        style={{maxWidth:'100%', height:'auto'}}
        />
    <p>Fonte: Elaborado pelo grupo Flow Solutions (2025).</p>
</div>

## Camadas e Componentes

### 1. Ingestão de Dados
- **Broker MQTT**  
  Sistema de mensageria publish/subscribe que recebe dados tanto históricos (arquivos CSV/XLSX) quanto dados em tempo real das bombas. O broker unifica a entrada de dados no sistema.
- **Datalake**  
  Inserção contínua de dados provenientes do broker MQTT em um datalake, separados por máquinas.
- **Banco de Série Temporal**  
  Repositório unificado que armazena todos os dados brutos provenientes do broker.  

---

### 2. Processamento e Preparação
- **Transformação e Limpeza**  
  Padronização, validação e enriquecimento dos dados.  
- **Banco de Dados Preparados**  
  Armazena os dados tratados e prontos para consumo por modelos e aplicações.  

---

### 3. Treinamento de Modelo
- **Treinamento do Modelo**  
  Execução de pipelines de treino sobre os dados preparados.  
- **Métricas de Treinamento**  
  Registro de indicadores de qualidade do modelo (acurácia, precisão etc.).  
- **Modelo Treinado → Armazenamento em Nuvem**  
  Persistência de modelos aprovados e prontos para uso em produção.  

---

### 4. Utilização do Modelo (Inferência)
- **Usuário → Início Web App → Web App → Backend**  
  Interface de interação do usuário com o sistema.  
- **API do Modelo → Script de Previsão**  
  Componente de inferência que processa entradas e retorna resultados.  
- **JSON de Previsão**  
  Saída estruturada em formato padrão para integração.  
- **Logs e Métricas**  
  Registro de chamadas, desempenho e monitoramento do uso do modelo.  

---

### 5. Retreinamento e Manutenção
- **Feedback do Usuário + Novos Dados**  
  Fonte de dados adicionais e de supervisão contínua.  
- **Decisão de Retreinamento**  
  Avalia degradação do modelo e define se é necessário novo treino.  

---

### Fluxo de Dados
1. **Ingestão**: Dados chegam via broker MQTT (tanto históricos quanto em tempo real).  
2. **Carga**: Dados são processados pela carga inicial ou carga em tempo real e armazenados no banco de séries temporais.  
3. **Processamento**: Passam por transformação e limpeza, sendo movidos para o banco de dados preparados.  
4. **Treinamento**: Modelos são treinados, avaliados por métricas e armazenados na nuvem.  
5. **Disponibilização**: O modelo é disponibilizado via API para uso por aplicações.  
6. **Consumo**: Usuários consomem previsões via Web App/Backend, recebendo saídas em JSON.  
7. **Monitoramento**: Logs e métricas monitoram o uso e alimentam o processo de manutenção.  
8. **Evolução**: Com base em feedback e novos dados, decide-se sobre o retreinamento.  


## Tecnologias Utilizadas

| Tecnologia                      | Função                                         | Uso                                                                                  |
|----------------------------------|------------------------------------------------|--------------------------------------------------------------------------------------|
| **PostgreSQL**                   | Banco de dados relacional                      | Armazenar dados estruturados, logs, métricas e séries temporais                      |
| **Flask**                        | Microframework web                             | Criar APIs e aplicações web para inferência e entrada de dados                       |
| **MinIO**                        | Object Storage compatível com S3               | Armazenar arquivos, datasets e modelos de machine learning                           |
| **Dremio**                       | Motor de query distribuído e virtualização de dados | Consultar dados em múltiplas fontes sem mover ou duplicar arquivos               |
| **Nessie**                       | Catálogo de dados com versionamento tipo git   | Gerenciar metadados, tabelas versionadas e branches de datasets                      |
| **Broker MQTT**                  | Sistema de mensageria publish/subscribe        | Ingestão de dados em tempo real (streaming)                                          |
| **XGBoost**                      | Algoritmo de machine learning baseado em boosting | Treinar modelos preditivos para dados estruturados                               |
| **GRU (Gated Recurrent Unit)**   | Rede neural recorrente                         | Treinar modelos de séries temporais ou dados sequenciais                             |
| **Serviços Python (scripts/containerizados)** | Processos de execução em Python                | Processamento, treinamento e inferência de modelos, podendo rodar isoladamente ou em containers |


Com as tecnologias definidas, vamos ver como elas estão relacionadas aos componentes da arquitetura:


### 1. Ingestão de Dados
| Componente                                   | Tecnologia Associada      |
|----------------------------------------------|---------------------------|
| Broker MQTT (dados históricos e tempo real) | Broker MQTT |
| Carga Inicial e Carga em Tempo Real         | MinIO, Dremio e Nessie |
| Banco de Série Temporal                      | PostgreSQL (TimescaleDB)  |

---

### 2. Processamento e Preparação
| Componente                                   | Tecnologia Associada      |
|----------------------------------------------|---------------------------|
| Transformação e Limpeza                      | Python (Scripts)  |
| Banco de Dados Preparados                    | PostgreSQL |

---

### 3. Treinamento de Modelo
| Componente                                   | Tecnologia Associada      |
|----------------------------------------------|---------------------------|
| Treinamento do Modelo                        | Python (Scripts) + XGBoost / GRU  |
| Métricas de Treinamento                      | Python (Scripts) / Minio, Dremio e Nessie   |
| Modelo Treinado → Armazenamento em Nuvem     | Minio, Dremio e Nessie |

---

### 4. Utilização do Modelo (Inferência)
| Componente                                   | Tecnologia Associada      |
|----------------------------------------------|---------------------------|
| Web App + Backend                            | Flask                     |
| API do Modelo / Script de Previsão           | Flask + Modelo (XGBoost/GRU) |
| JSON de Previsão                             | Flask (output da API)     |
| Logs e Métricas                              | PostgreSQL |

---

### 5. Retreinamento e Manutenção
| Componente                                   | Tecnologia Associada      |
|----------------------------------------------|---------------------------|
| Feedback do Usuário + Novos Dados            | Flask (entrada) |


### Por que essas tecnologias?


**PostgreSQL**
A escolha do PostgreSQL foi orientada pelos requisitos de latência baixa no processamento de dados (RNF 03) e de tempo de resposta ágil da interface (RNF 06).
Ele é um banco de dados relacional maduro, altamente confiável e com forte suporte a consistência transacional (ACID), garantindo que nenhum dado crítico seja perdido ou corrompido.
O PostgreSQL também possui extensões como TimescaleDB, que o tornam extremamente eficiente para lidar com séries temporais, permitindo ingestão de milhares de registros por segundo e consultas rápidas para dashboards em tempo real.
Diferente de outra alternativa como NoSQL, ele oferece flexibilidade sem perder estrutura e integridade dos dados, o que é essencial em sistemas de monitoramento industrial.

**Flask**
A escolha do Flask foi guiada pela necessidade de notificações responsivas (RNF 02), baixa latência na interface (RNF 06) e clareza na comunicação das previsões (RNF 07).
Flask é um microframework web em Python, extremamente leve, rápido e modular, ideal para construir APIs REST e serviços de backend sem overhead desnecessário.
Sua simplicidade permite desenvolver endpoints específicos para notificações, confirmação de alertas e exibição dos níveis de confiança do modelo de forma intuitiva para o usuário.
Diferente de frameworks mais pesados (como Django), o Flask favorece agilidade, controle granular e menor tempo de resposta.

**MinIO, Dremio e Nessie**
O trio foi escolhido para atender aos requisitos de capacidade de monitoramento em escala (RNF 01), baixa latência de dados (RNF 03) e recuperação de conexão/dados (RNF 05).

**MinIO:** fornece object storage escalável e compatível com S3, simplificando o armazenamento de arquivos brutos, datasets e modelos. Sua arquitetura distribuída garante tolerância a falhas, essencial para não perder dados críticos.

**Dremio:** atua como motor de query e virtualização de dados, permitindo consultas rápidas em múltiplas fontes sem duplicação. Isso reduz a complexidade de ETLs pesados e garante que os dados estejam acessíveis quase em tempo real.

**Nessie:** traz o conceito de git para dados, com versionamento de metadados e tabelas. Essa capacidade é crucial para consistência e rastreabilidade, especialmente em cenários de reconexão e sincronização de dados.

Juntos, esses componentes criam uma camada de dados resiliente, performática e confiável, que dificilmente seria obtida usando apenas um banco de dados tradicional ou storage simples.

**Broker MQTT**
O broker MQTT foi escolhido com base nos requisitos de capacidade de monitoramento simultâneo (RNF 01) e de baixa latência no processamento de dados (RNF 03).
O MQTT é um protocolo de mensageria leve, otimizado para IoT e comunicação máquina-a-máquina, suportando milhares de conexões concorrentes com uso mínimo de banda e recursos.
Ele segue o padrão publish/subscribe, que desacopla produtores (bombas) e consumidores (sistema), garantindo escalabilidade, tolerância a falhas e confiabilidade na entrega de mensagens.
O broker unifica tanto a ingestão de dados históricos (arquivos CSV/XLSX) quanto dados em tempo real das bombas, simplificando a arquitetura e eliminando a necessidade de múltiplos pontos de entrada de dados.
Diferente de alternativas como HTTP ou AMQP, o MQTT é projetado para ambientes com restrições de rede e necessidade de tempo real, exatamente o caso de monitoramento de máquinas industriais.

**Modelos XGBoost / GRU**
A escolha dos algoritmos de machine learning foi orientada pelo requisito de alta confiabilidade preditiva (RNF 04) e clareza sobre incertezas (RNF 07).

**XGBoost** é um dos algoritmos de boosting mais eficientes para dados estruturados. Ele combina alto desempenho, interpretabilidade parcial e capacidade de lidar com grandes volumes de dados, sendo ideal para prever falhas com base em variáveis tabulares.

**GRU (Gated Recurrent Unit)** é uma rede neural recorrente simplificada em relação ao LSTM, mas igualmente eficaz para séries temporais e dados sequenciais, com menor custo computacional. Isso permite manter previsões acuradas sem comprometer o tempo de resposta.


**Serviços Python (scripts containerizados)**
Essa escolha foi orientada pelos requisitos de latência no processamento (RNF 03) e recuperação de dados (RNF 05).
Python foi adotado por seu vasto ecossistema de bibliotecas para machine learning, processamento de dados e integração (pandas, scikit-learn, TensorFlow, PyTorch, etc.).
Ao containerizar os scripts, obtemos portabilidade, escalabilidade horizontal e isolamento de falhas, assegurando que o sistema continue funcionando mesmo em cenários de alta carga ou falhas pontuais.
Diferente de soluções monolíticas, os serviços Python permitem flexibilidade para evoluir componentes específicos (ex.: processamento batch, inferência, métricas) sem impactar o restante do sistema.