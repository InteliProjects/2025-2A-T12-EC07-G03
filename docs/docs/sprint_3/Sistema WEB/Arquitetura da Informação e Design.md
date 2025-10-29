---
title: Arquitetura da Informação e Design
sidebar_label: Arquitetura da Informação e Design
sidebar_position: 2
---

import useBaseUrl from '@docusaurus/useBaseUrl';

# Arquitetura da Informação e Design

Durante esta sprint, desenvolvemos a primeira versão do design das telas do sistema utilizando a ferramenta Figma, com base em princípios de arquitetura da informação (AI). O objetivo foi estruturar a experiência do usuário de forma clara, intuitiva e organizada, permitindo que o sistema seja construído de forma consistente nas próximas etapas do projeto.

Foram criadas três telas principais:

**Tela de Login** – ponto de entrada do sistema, responsável pela autenticação dos usuários.

**Tela de Gerenciamento de Modelos** – onde será possível visualizar, cadastrar e editar modelos de análise.

**Homepage (Dashboard)** – página inicial com resumo de informações, indicadores de desempenho e alertas.

Essas telas foram pensadas não apenas na estética visual, mas também na funcionalidade e usabilidade, com base em conceitos de design centrado no usuário.

## Arquitetura da Informação

A Arquitetura da Informação é a base que orienta toda a construção do design do sistema, funcionando como uma espécie de mapa que organiza o conteúdo, os fluxos e as interações de forma clara. No nosso projeto, ela foi utilizada para estruturar como as informações seriam apresentadas e como o usuário navegaria entre as funcionalidades, garantindo que cada elemento tivesse um lugar definido e um propósito específico.

O objetivo principal é facilitar a experiência do usuário, tornando o sistema intuitivo, eficiente e simples de usar. Ela ajuda a responder três perguntas: onde estou, para onde posso ir e o que posso fazer aqui. Dessa forma, reduz a complexidade do sistema, organiza os conteúdos em hierarquias bem definidas e estabelece uma navegação fluida, que guia o usuário do login inicial até a execução das tarefas mais complexas.

<div style={{ textAlign: 'center' }}>
  <p><strong>Figura 1 - Arquitetura da Informação</strong></p>
  <img 
    src={useBaseUrl('arquitetura_da_informação.drawio.png')} 
    alt="Arquitetura da Informação" 
    title="Arquitetura da Informação" 
    style={{ maxWidth: '100%', height: 'auto' }}
  />
  <p>Fonte: Elaborado pelos autores (2025)</p>
</div>

Essa organização foi aplicada desde a tela de login, passando pelo gerenciamento de modelos, que utiliza listagens e ações diretas para tornar o trabalho mais ágil, até a homepage (dashboard), que reúne em blocos visuais as informações mais críticas, como número de máquinas operando, alertas ativos, manutenção programada, desempenho por gráficos, mapa geográfico e satisfação do cliente. 

Essa estrutura bem definida garante que, nos próximos processos de desenvolvimento, a equipe de consiga implementar as telas de forma consistente, sem ambiguidades sobre a função de cada elemento. A Arquitetura da Informação, portanto, atua como a ponte entre design e código, permitindo que o sistema seja construído de maneira escalável, padronizada e centrada no usuário.

## Telas Desenvolvidas

### Tela de Login

- Função principal: autenticar usuários e permitir acesso seguro ao sistema.
- Elementos principais: campos de e-mail e senha, botão de login, opção de cadastro e recuperação de senha.

<div style={{ textAlign: 'center' }}>
  <p><strong>Figura 2 - Tela de Login</strong></p>
  <img 
    src={useBaseUrl('login.png')} 
    alt="Tela de Login" 
    title="Tela de Login" 
    style={{ maxWidth: '100%', height: 'auto' }}
  />
  <p>Fonte: Elaborado pelos autores (2025)</p>
</div>
---

### Homepage - Dashboard Geral

Tela principal que reúne as informações mais relevantes sobre todas as máquinas em operação, paradas e em manutenção. Inclui indicadores de performance, alertas ativos, mapa de localização e gráficos comparativos de desempenho, além de mostrar a satisfação e percepção de valor dos clientes.

- **Elementos principais:**
  - **Resumo do dia (cards coloridos no topo):**
    - **Total Operando** - número de máquinas em funcionamento.
    - **Total Paradas** - número de máquinas fora de operação (paradas planejadas ou não).
    - **Alertas Ativos** - alertas em tempo real (ex: temperatura, pressão).
    - **Próximas Manutenções** - quantidade de manutenções programadas.
    - Botão **Exportar** relatório.

  - **Performance das Máquinas (gráfico de linhas):**
    Mostra o desempenho de diferentes máquinas ao longo do tempo.

  - **Status Individual (gráficos de rosca):**

    Cada máquina possui card com:
      - Data da última manutenção.
      - Data da próxima manutenção.
      - Percentual de saúde/funcionamento.
  
  - **Alertas Críticos:**
    Lista de falhas em destaque para a intervenção imediata.

  - **Mapa Geográfico:**
    Localização das máquinas em operação pelo Brasil.

  - **Satisfação dos Clientes (gráfico comparativo):**
    Exibe a percepção do cliente ao longo do tempo, comparando mês passado x mês atual. São dados que dependem do parceiro, podendo vir de integrações de API ou relatórios internos enviados pela área comercial.

<div style={{ textAlign: 'center' }}>
  <p><strong>Figura 3 - Homepage</strong></p>
  <img 
    src={useBaseUrl('dashboard_geral.png')} 
    alt="Homepage" 
    title="Homepage" 
    style={{ maxWidth: '100%', height: 'auto' }}
  />
  <p>Fonte: Elaborado pelos autores (2025)</p>
</div>

Essa tela permite que a Itubombas tenha um ***overview*** imediato da situação de todo o parque de máquinas, sem precisar entrar máquina por máquina, ou acessar diversas telas diferentes. Isso reduz o tempo de análise e resposta, já que os principais indicadores estão visíveis em um só lugar.

Com base nas informações disponibilizadas nessa tela o gestor consegue identificar gargalos em segundos, além de ajudar na priorização de recursos de forma estratégicas e evitar que falhas se tornem problemas críticos, reduzindo paradas inesperadas.


#### Popup de Detalhe da Máquina

Mostra informações específicas de uma máquina selecionada, incluindo cliente, localização, modelo da máquina, histórico de manutenção, curva do motor e índice de sáude. É importante ressaltar que no caso da curva do motor, atualmente é disposto apenas imagens gráficas da curva. As funções matemáticas que modelam essa curva não estão disponíveis neste momento.

- **Elementos principais:**
  - **Identificação da Máquina:**
    - Código (ex: ITU-692).
    - Estado de Saúde (ex: Boa - 89%).

  - **Informações do Cliente:**
    - Nome do cliente responsável.
    - Localização geográfica.
    - Modelo da máquina.

  - **Histórico de Manutenção:**
    - Data da última manutenção.
    - Data da próxima manutenção agendada.
  
  - **Curva do Motor:** Mostra a relação entre a vazão e a pressão para determinar o ponto ideal de RPM do motor. Além disso, demostra o ponto ótimo de eficiência de operação.

  - Botão de `+ Informações`: Revela informações ainda mais detalhadas sobre a máquina (ex: temperatura, RPM, nível de óleo)

<div style={{ textAlign: 'center' }}>
  <p><strong>Figura 4 - Popup: Detalhe da Máquina</strong></p>
  <img 
    src={useBaseUrl('detalhe_maquina.jpg')} 
    alt="Detalhe da Máquina" 
    title="Detalhe da Máquina" 
    style={{ maxWidth: '100%', height: 'auto' }}
  />
  <p>Fonte: Elaborado pelos autores (2025)</p>
</div>

Essa tela foi pensada para fornecer transparência total sobre a condição individual da máquina, fundamental para manutenção preditiva e dar informações mais específicas sobre cada bomba.

#### Popup de Informações Avançadas:

Esse popup de informações avançadas é acessado dentro do popup de uma máquina específica, por meio do botão `+ Informações`.

Esse recurso permite a visualização de dados técnicos mais aprofundados relacionados ao funcionamento da máquina, indo além dos indicadores de saúde e histórico de manutenção.

O objetivo é fornecer aos técnicos e especialistas acesso a métricas operacionais em tempo real, essenciais para diagnósticos e manutenção preditiva.

- Elementos principais:
  - RPM
  - Temperatura
  - Pressão
  - Nível de óleo

<div style={{ textAlign: 'center' }}>
  <p><strong>Figura 5 - Popup: Informações Avançadas</strong></p>
  <img 
    src={useBaseUrl('popup_avancado.jpg')} 
    alt="Informações Avançadas" 
    title="Informações Avançadas" 
    style={{ maxWidth: '100%', height: 'auto' }}
  />
  <p>Fonte: Elaborado pelos autores (2025)</p>
</div>

---

### Tela de Gerenciamento de Modelos

- Função principal: organizar e controlar os modelos disponíveis no sistema.

- Estrutura baseada em listagens e botões de ação (criar, editar, excluir).

<div style={{ textAlign: 'center' }}>
  <p><strong>Figura 6 - Tela de Gerenciamento de Modelos</strong></p>
  <img 
    src={useBaseUrl('gerenciamento_de_modelos.jpg')} 
    alt="Tela de Gerenciamento de Modelos" 
    title="Tela de Gerenciamento de Modelos" 
    style={{ maxWidth: '100%', height: 'auto' }}
  />
  <p>Fonte: Elaborado pelos autores (2025)</p>
</div>

---

## Conclusão

A arquitetura proposta organiza as informações em diferentes níveis de detalhe: a tela de login permite a autenticação de usuários, o dashboard geral oferece uma visão ampla das máquinas, o popup de detalha apresenta informações específicas de cada equipamento, o popup de informações avançadas disponibiliza métricas técnicas para diagnósticos aprofundados e a tela de gerenciamento de modelos exibe e dispõem os modelos disponíveis no sistema. 

O design foi estruturado para equilibrar visão estratégica, monitoramento operacional e satisfação do cliente, mas algumas funcionalidades dependem da disponibilização de dados pela Itubombas. O próximo passo será a validação desse design junto ao parceiro, antes do início do desenvolvimento em código do front-end.

