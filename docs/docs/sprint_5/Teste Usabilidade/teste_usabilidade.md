---
title: Teste de Usabilidade
sidebar_label: Teste Usabilidade
sidebar_position: 1
---

# Introdução

Esta seção apresenta o planejamento do teste de usabilidade desenvolvido para a aplicação **SyncTelemetry**, para o projeto em 
parceria com a Itubombas, que tem como objetivo monitorar o desempenho de motobombas industriais e prever falhas com base em indicadores de telemetria. O teste busca avaliar se a interface é **intuitiva**, **eficiente** e **compreensível**, mesmo para usuários sem experiência prévia no contexto industrial.

O foco do teste está em observar como os usuários interagem com o sistema, identificando pontos de confusão, barreiras de navegação e oportunidades de melhoria na apresentação das informações, especialmente nas telas de dashboard, detalhe da bomba e gestão de modelos preditivos. Mais do que testar o conhecimento técnico, o objetivo é verificar se a aplicação comunica claramente o estado das máquinas, níveis de risco e funções disponíveis.

---

## Metodologia

Os testes de usabilidade foram realizados com o objetivo de validar os requisitos funcionais e não funcionais definidos para o sistema, bem como verificar se a arquitetura proposta atende às necessidades esperadas de desempenho, clareza e navegabilidade.

Os testes foram realizados dentro da faculdade, com usuários não-especialistas, uma vez que não foi possível aplicar o teste com os usuários reais do parceiro industrial durante o período de desenvolvimento. Mesmo assim, essa etapa permitiu avaliar a intuitividade e clareza geral da interface, verificando se o sistema é compreensível e fácil de usar.

As tarefas foram organizadas em cenários de uso práticos, simulando situações típicas de operação e análise no sistema SyncTelemetry como identificar alertas, visualizar e compreender indicadores de saúde e realizar previsões. Cada cenário buscou avaliar a facilidade de navegação, a clareza dos elementos visuais e a capacidade do usuário em interpretar os dados apresentados.

#### Critérios de avaliação:

- Conclusão da tarefa sem auxílio;

- Clareza na interpretação das informações;

- Desempenho e tempo de resposta;

- Erros ou dúvidas recorrentes;

- Grau de confiança e satisfação do usuário.

Dessa forma, a documentação dos testes foi elaborada de modo a comprovar a aderência entre o sistema desenvolvido e os requisitos definidos, garantindo a rastreabilidade entre o planejamento, a execução e os resultados observados.

---

### Cenário 1 – Acesso ao sistema e visualização inicial

- **Pré-condição:** Sistema aberto na tela de login.
- **Tarefa:** Realizar cadastro, fazer login e identificar as principais informações exibidas na tela inicial.
- **Pós-condição:** Usuário acessa o dashboard e compreende o estado geral das máquinas.
- **Requisitos avaliados:** RF08, RNF06.
- **Observações:** Avaliar se consegue acessar o sistema, clareza dos indicadores, tempo de resposta e facilidade de navegação inicial.

---

### Cenário 2 – Identificação de máquina com risco elevado

- **Pré-condição:** Usuário logado e visualizando a tela inicial.
- **Tarefa:** Localizar a máquina que apresenta o maior nível de risco ou alerta ativo.
- **Pós-condição:** Usuário identifica corretamente a máquina crítica.
- **Requisitos avaliados:** RF01, RF08, RNF07.
- **Observações:** Avaliar clareza das cores e ícones de alerta, visibilidade das informações e facilidade de localizar o equipamento crítico.

---

### Cenário 3 – Encontrar lista de máquinas e buscar por uma específica

- **Pré-condição:** Usuário logado e visualizando o dashboard inicial.
- **Tarefa:** Localizar as máquinas disponíveis no sistema, buscar e acessar uma máquina em específico.
- **Pós-condição:** Usuário localiza sem dificuldade a lista e consegue acessar o modal (janela que aparece sobre a página principal) de uma máquina.
- **Requisitos avaliados:** RF01, RF08, RNF04, RNF07.
- **Observações:** Avaliar se o usuário reconhece rapidamente onde estão listadas as máquinas e se a busca é percebida como funcional.

---

### Cenário 4 – Interpretação do estado da máquina

- **Pré-condição:** Usuário no dashboard, com o modal de detalhe da máquina aberto.
- **Tarefa:** Analisar os indicadores apresentados e determinar se a máquina está em condição normal ou de risco.
- **Pós-condição:** Usuário compreende corretamente o estado da máquina e identifica os principais indicadores de desempenho.
- **Requisitos avaliados:** RF01, RF08, RNF04, RNF07.
- **Observações:** Avaliar clareza dos gráficos e rótulos, entendimento dos status "OK", "Alerta", "Atenção" e percepção sobre a confiabilidade das informações exibidas.

---

### Cenário 5 – Realização de previsão de indicadores

- **Pré-condição:** Usuário com o modal da máquina aberto.
- **Tarefa:** Selecionar quantidade de timesteps e um modelo disponível e realizar a previsão de saúde da máquina.
- **Pós-condição:** O sistema exibe o resultado da previsão e o usuário compreende o significado do valor apresentado.
- **Requisitos avaliados:** RF01, RF02, RF09, RNF03, RNF06.
- **Observações:** Avaliar clareza do processo de seleção, tempo de resposta do sistema e entendimento da informação gerada pelo modelo preditivo.

---

### Cenário 6 – Retreinamento de modelo e verificação de logs

- **Pré-condição:** Usuário na tela de modelos, com acesso às opções de treinamento.
- **Tarefa:** Selecionar uma máquina e um indicador, definir o intervalo de datas e realizar o retreinamento do modelo. Em seguida, verificar o registro do treinamento nos logs.
- **Pós-condição:** Novo modelo é treinado e aparece registrado corretamente na lista de logs.
- **Requisitos avaliados:** RF09, RNF01, RNF02, RNF06.
- **Observações:** Avaliar clareza dos campos de seleção, mensagens de sucesso/erro e facilidade para localizar os registros de treinamento.

---

## Resultado dos Testes de Usabilidade

**Cenário 1: Acesso ao sistema e visualização inicial**

**Descrição da tarefa:** Suponha que você é gestor da Itubombas, está no seu escritório e precisa acessar informações das bombas; utilize o sistema para autenticar-se com suas credenciais (usuário + senha) e identifique as principais informações exibidas na tela inicial.

| # | Nome    | Perfil/Persona | Resultado da tarefa | Etapa 1: **Cadastro no sistema**                 | Etapa 2: Acessou o dashboard               | Etapa 3: Compreender as informações gerais do dashboard                    | Obs                |
|---|---------|-----------------|---------------------|-------------------------|-----------------------|----------------------------|------------------------|
| **1** | Davi    | Usuário não técnico          | **sucesso**             | Fez o cadastro e realizou o login sem dificuldades | Acessou a página principal sem dificuldades | Entendeu o que as informações da dashboard sem dificuldades | - |
| **2** | Kauan   | Usuário não técnico          | **sucesso**             | Fez o cadastro e realizou o login sem dificuldades | Acessou a página principal sem dificuldades | Entendeu o que as informações da dashboard sem dificuldades | - |
| **3** | Fernando| Usuário não técnico          | **sucesso**             | Fez o cadastro e realizou o login sem dificuldades | Acessou a página principal sem dificuldades | Entendeu o que as informações da dashboard sem dificuldades | - |

**Cenário 2: Identificação de máquina com risco elevado**

**Descrição da tarefa:** Suponha que você é gestor da Itubombas e quer verificar quais máquinas estão em estado de alerta; utilize o sistema para localizar essas máquinas.

| # | Nome    | Perfil/Persona | Resultado da tarefa | Etapa 1: Localizar a área de Alertas Críticos                 | Etapa 2: Entender qual máquina está em alerta               | Obs                |
|---|---------|-----------------|---------------------|-------------------------|-----------------------|------------------------|
| **1** | Davi    | Usuário não técnico          | **não conseguiu**             | Não conseguiu localizar a área de Alertas Críticos na tela | - | Acredita que a divisão da tela não está intuitiva para identificar o que é a lista de máquinas e o que é Alertas Críticos |
| **2** | Kauan   | Usuário não técnico          | **sucesso**             | Conseguiu localizar a área de Alertas Críticos na tela sem dificuldades | Entendeu qual máquina está em alerta sem dificuldades | - |
| **3** | Fernando| Usuário não técnico          | **conseguiu com dificuldade**             | Conseguiu localizar a área de Alertas Críticos na tela com dificuldades | Acessou a página principal sem dificuldades | Apesar de ter localizado a área correta, teve certa dificuldade em encontrar. A divisão da tela pode ser um dos motivos|


> **Nota:**  
> Por questões de espaço e objetividade, esta documentação apresenta detalhadamente apenas os resultados dos dois primeiros cenários de teste.  
> No entanto, os **demais cenários (3 a 6)** foram **aplicados e documentados seguindo o mesmo formato e metodologia**, utilizando a mesma estrutura de coleta e registro de resultados apresentada nesta seção.  

---

## Resultados Observados

### Impressão geral 

- Todos os participantes conseguiram navegar no sistema com facilidade e completaram a maioria das tarefas sem ajuda.

- O fluxo principal (login → dashboard → modal → previsão → retreinamento) foi compreendido e executado corretamente.

- As principais dificuldades estiveram relacionadas à organização visual e à terminologia técnica (como “timesteps”, “data inicial/final” e nomes de modelos).

### Principais problemas identificados

| Cenário | Dificuldade observada | Sugestão de melhoria |
|----------|-----------------------|----------------------|
| **1** | Representação limitada apenas à saúde geral | Incluir gráficos individuais de subsistemas (lubrificação, hidráulico). |
| **2** | Falta de separação visual clara entre área de alertas e lista de máquinas | Inserir divisão mais evidente (borda, cor de fundo ou título fixo “Alertas críticos”). |
| **3** | Barra de busca pouco destacada / falta de filtros | Destacar o campo de busca e adicionar filtros (por status: parada, manutenção etc.). |
| **4** | Ausência de legendas de faixas (“OK”, “Atenção”, “Crítico”) | Adicionar label explicativo ou cores padronizadas com legenda. |
| **5** | Dúvidas sobre o modelo ideal e sobre “timesteps” | Criar tooltip explicativo e modelo recomendado automático. |
| **6** | Dificuldade de entender campos de data e ausência de logs visíveis | Adicionar ícone de ajuda (popup com explicação) e exibir mensagens de sucesso/erro mais claras. |

### Pontos positivos

- Interface intuitiva e fluida.

- Baixo tempo de execução das tarefas.

- Layout coerente com a lógica do sistema.

- Curva de aprendizado rápida, mesmo para usuários sem familiaridade com manutenção industrial.

### Limitações técnicas 

Uma das principais limitações encontradas durante os testes foi o fato de que o grupo possuía dados completos apenas das bombas 415 e 693. Assim, foi possível desenvolver modelos preditivos apenas para essas máquinas, enquanto as demais ficaram sem modelo associado.

Além disso, houve um problema na conexão do broker MQTT justamente para essas bombas: as máquinas conectadas em tempo real não possuíam dados históricos suficientes para o treinamento, enquanto as que tinham dados adequados não estavam ativas no broker. Essa inconsistência afetou a experiência dos participantes, que inicialmente não entenderam a limitação até que fosse explicada pela equipe.

Essa situação reforça a importância de alinhar o ambiente de teste com as condições reais de uso do sistema, garantindo que todas as funcionalidades previstas possam ser plenamente demonstradas.

### Conclusão

Os testes confirmaram que o sistema é funcional, compreensível e bem estruturado, cumprindo seus requisitos principais. As melhorias identificadas concentram-se em ajustes de interface, explicabilidade dos modelos e comunicação visual. As limitações técnicas observadas serão tratadas como próximos passos, visando aprimorar a consistência da experiência do usuário e a integração entre dados históricos e em tempo real.
