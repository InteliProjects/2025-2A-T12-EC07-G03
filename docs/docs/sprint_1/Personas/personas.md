---
title: Personas
sidebar_label: Personas
sidebar_position: 2
---

import useBaseUrl from '@docusaurus/useBaseUrl';

## O que é uma Persona?

Persona é a representação fictícia de um cliente ou consumidor ideal para um produto ou serviço (https://www.rdstation.com/glossario/persona/). Essa ferramenta ajuda as empresas a enxergarem o público de forma mais humanizada e direcionada, permitindo entender melhor seus objetivos, desafios e motivações. Com isso, é possível criar estratégias mais eficazes e personalizadas, além de desenvolver soluções que realmente atendam às necessidades e expectativas dos clientes e usuários.

A partir de encontros e pesquisas com a Itubombas, foi possível traçar quatro perfis que refletem as áreas e profissionais que terão contato com o sistema em desenvolvimento. Para definir essas personas, foram utilizadas ferramentas como o Canvas de Proposta de Valor, direcionando os próximos passos do grupo e do produto.

As personas criadas para este projeto são:

- **Vendedora:** profissional que compreende tecnicamente as falhas e mantém o relacionamento com o cliente.
- **Operador de logística:** responsável pela organização e execução da logística nas manutenções das bombas e substituições de bombas.
- **Engenheiro de produção:** encarregado de definir qual é a melhor bomba para cada cliente.
- **Manutentor:** profissional que troca as peças e cuida de reparos físicos da máquina.

### Persona 1 - Marina Prado (Vendedora)

#### Quem é e por que criamos:
Marina Prado, 31 anos, é Engenheira Mecânica e atua como vendedora técnica, responsável pelo relacionamento integral com o cliente. Ela foi idealizada porque representa o elo de comunicação entre Itubombas e o cliente, precisando de informações técnicas precisas para gerar confiança, resolver problemas e apoiar negociações. O sistema em desenvolvimento será uma de suas principais ferramentas para transformar dados operacionais em argumentos claros e estratégicos.

<div style={{ textAlign: 'center' }}>
  <p><strong>Figura 1 - Persona 1: Marina Prado</strong></p>
  <img 
    src={useBaseUrl('/img/MarinaPrado.png')} 
    alt="Persona 1: Marina Prado" 
    tile="Persona 1: Marina Prado" 
    style={{ maxWidth: '100%', height: 'auto' }}
  />
  <p>Fonte: Elaborado pelos autores (2025)</p>
</div> 

#### Atuação profissional e desafios:
Marina conduz negociações iniciais, apresenta soluções técnicas, acompanha a operação e intervém sempre que surgem problemas durante o contrato. Sem dados claros sobre o uso real das bombas,  enfrenta dificuldades para identificar mau uso, comprovar sobrecarga ou agir preventivamente antes que falhas impactem o cliente.

#### Expectativas e preocupações:
Espera contar com dados objetivos e organizados sobre padrões de operação, permitindo agir preventivamente e manter um relacionamento de confiança. Preocupa-se em receber informações claras, visualmente compreensíveis e facilmente comunicáveis para explicar ao cliente com segurança.

#### Casos de uso:
- Monitorar diariamente o uso de bombas de clientes ativos.
- Receber alertas automáticos de risco de falha para agir preventivamente.
- Consultar histórico de manutenção e desempenho para preparar reuniões.
- Usar dados para justificar ajustes de operação ou troca de equipamento.
- Apoiar renovações de contrato com base em indicadores de performance. 

#### Cenário de interação:
Um cliente relata falha prematura na bomba. Marina acessa o sistema e identifica que, em dois dias consecutivos, o equipamento operou acima do tempo diário contratado. Com essa informação, ela explica ao cliente o impacto do uso incorreto e propõe uma solução, como uma troca de equipamento ou ajuste contratual, evitando um conflito e preservando a relação comercial.

#### Relevância para o projeto:
Marina é essencial para validar como os dados preditivos podem ser aplicados no contexto comercial e como esse sistema pode ser útil para a gestão comercial. Sua atuação garante que informações técnicas se transformem em argumentos estratégicos, fortalecendo o relacionamento com o cliente e aumentando a competitividade da Itubombas.

### Persona 2 - David Ferreira (Operador de Logística)

#### Quem é e por que criamos:
David Ferreira, 39 anos, é Técnico em Mecânica Industrial e atua como operador de logística responsável por coordenar a entrega, recolhimento e manutenção das bombas. Foi criado porque representa o perfil que lida diretamente com o fluxo físico dos equipamentos e depende de dados técnicos para otimizar a operação, evitar sobrecargas e reduzir custos logísticos.

<div style={{ textAlign: 'center' }}>
  <p><strong>Figura 2 - Persona 2: David Ferreira</strong></p>
  <img 
    src={useBaseUrl('/img/DavidFerreira.png')} 
    alt="Persona 2: David Ferreira" 
    tile="Persona 2: David Ferreira" 
    style={{ maxWidth: '100%', height: 'auto' }}
  />
  <p>Fonte: Elaborado pelos autores (2025)</p>
</div> 

#### Atuação profissional e desafios:
David organiza rotas, acompanha o envio e recolhimento de bombas e garante que o equipamento certo chegue ao cliente no momento certo. Sem dados sobre o uso real, pode não identificar padrões de sobrecarga ou falhas iminentes, o que gera viagens desnecessárias, atrasos e aumento de custos operacionais.

#### Expectativas e preocupações:
Espera contar com um sistema que mostre, de forma centralizada, o status e o histórico de uso de cada bomba, facilitando a priorização de atendimentos e a prevenção de deslocamentos desnecessários. Preocupa-se em ter dados confiáveis para justificar decisões operacionais e otimizar a utilização da frota.

#### Casos de uso:
- Consultar diariamente o status das bombas em operação.
- Visualizar quais bombas apresentam uso fora do padrão.
- Receber alertas de risco de falha e estimativas de tempo até quebra para priorizar visitas.
- Planejar rotas de manutenção preventiva junto com outras entregas/recolhimentos.
- Identificar equipamentos que estão próximos do fim da vida útil para substituição programada.
- Reduzir deslocamentos desnecessários por meio de diagnóstico remoto.

#### Cenário de interação:
Ao iniciar o dia, David acessa o sistema e vê que uma bomba em um cliente distante apresenta 80% de risco de falha e previsão de quebra em 3 dias. Ele reorganiza a rota de manutenção para atender esse cliente no dia seguinte, aproveitando para recolher uma bomba de outro cliente no caminho. Isso evita que a bomba quebre durante a operação e poupa um deslocamento emergencial.

#### Relevância para o projeto:
David é essencial para mostrar como os dados coletados se transformam em ações logísticas eficientes. Ao utilizar o sistema, ele consegue antecipar manutenções, reduzir custos operacionais e evitar que falhas impactem a operação do cliente. Sua interação com a ferramenta comprova o valor da análise preditiva na otimiazação da logística.


### Persona 3 – Pedro Silva (Técnico de Vendas Itubombas)

#### Quem é e por que criamos:

Pedro é um profissional de 35 anos, com formação técnica em mecânica industrial e experiência consolidada no segmento de equipamentos para bombeamento. Atua na Itubombas como especialista em aplicação, sendo responsável por analisar dados operacionais e indicar qual bomba é mais adequada para cada situação. Reconhecido por seu conhecimento técnico e pela capacidade de transformar informações complexas em decisões precisas, Pedro garante que cada cliente receba uma solução alinhada ao seu cenário operacional, priorizando eficiência, confiabilidade e durabilidade dos equipamentos.

<div style={{textAlign:'center'}}>
    <p><strong>Figura 3 - Persona 3: Pedro Silva</strong></p>
        <img
        src={useBaseUrl('/img/PedroSilva.png')}
        alt="Persona Pedro Silva"
        title="Persona Pedro Silva"
        style={{maxWidth:'80%', height:'auto'}}
        />
    <p>Fonte: Elaborado pelo grupo Flow Solutions (2025).</p>
</div>

#### Atuação Profissional e Desafios:

Na rotina de trabalho, Pedro utiliza informações coletadas por sensores instalados em bombas e outros equipamentos para analisar padrões de uso e identificar demandas do cliente. Seu papel envolve interpretar relatórios e dados técnicos para recomendar modelos de bomba que atendam aos requisitos de eficiência, durabilidade e custo-benefício. No entanto, enfrenta desafios recorrentes, como a dificuldade em reunir rapidamente dados suficientes e confiáveis para embasar suas indicações.
O processo atual exige que Pedro acesse múltiplas fontes de informação, o que pode resultar em atrasos e aumentar o risco de recomendações menos precisas. Além disso, a ausência de uma ferramenta que consolide os dados em uma visão clara e objetiva dificulta a tomada de decisão, especialmente em casos de clientes que demandam respostas rápidas para evitar falhas operacionais.

#### Expectativas e Preocupações

Diante deste cenário, Pedro espera contar com uma solução que integre e organize automaticamente os dados coletados pelos sensores, permitindo que ele visualize rapidamente o desempenho e o histórico de uso de cada equipamento. Uma ferramenta preditiva, capaz de sugerir o modelo ideal de bomba com base em dados históricos e condições de operação, seria um diferencial para agilizar o atendimento e aumentar a confiança do cliente nas recomendações fornecidas.
Apesar de reconhecer o valor da automação e da análise preditiva, Pedro se preocupa com a clareza e a transparência dos critérios utilizados pela ferramenta. Para ele, é fundamental que o sistema apresente justificativas compreensíveis para cada sugestão, de modo que possa explicar com segurança as recomendações ao cliente e preservar sua credibilidade profissional.

#### Relevância da Persona para o Projeto

A persona de Pedro Silva é estratégica para o direcionamento do desenvolvimento da solução, pois representa o elo entre dados técnicos e decisão de compra. Compreender suas dores, expectativas e responsabilidades permite à equipe criar uma ferramenta que não apenas acelere o processo de recomendação, mas também mantenha o alto padrão de confiabilidade exigido pela Itubombas. Assim, o projeto avança no sentido de oferecer uma solução que transforma dados em decisões assertivas, fortalecendo a relação de confiança entre empresa e cliente.

### Persona 4 – Isac Santos (Técnico de Manutenção de Campo Itubombas)

#### Quem é e por que criamos:

Isac tem 42 anos e formação técnica em mecânica industrial, com ampla experiência em manutenção eletromecânica em ambientes industriais e comerciais. Atua no Itubombas como técnico de manutenção de campo, realizando atendimentos em plantas de clientes e sendo frequentemente o primeiro ponto de contato para resolução de falhas. Reconhecido pela postura prática e pelo rigor na execução dos reparos, Isac valoriza procedimentos claros, dados objetivos e ferramentas que aumentem a previsibilidade do seu trabalho.

<div style={{textAlign:'center'}}>
    <p><strong>Figura 4 - Persona 4: Isac Santos</strong></p>
        <img
        src={useBaseUrl('/img/IsacSantos.png')}
        alt="Persona Isac Santos"
        title="Persona Isac Santos"
        style={{maxWidth:'80%', height:'auto'}}
        />
    <p>Fonte: Elaborado pelo grupo Flow Solutions (2025).</p>
</div>

#### Atuação Profissional e Desafios

No dia a dia, Isac avalia chamados e desloca-se até o local para inspecionar máquinas que apresentaram falha. Seu trabalho inclui diagnosticar a causa, efetuar o reparo e documentar o serviço. Um dos principais desafios é a ausência de informações organizadas e contextualizadas antes do deslocamento: com dados incompletos, Isac muitas vezes chega sem a peça correta ou sem entender plenamente o histórico da máquina, o que aumenta a probabilidade de retorno e elevação dos custos operacionais.
Além disso, a análise in loco demanda tempo considerável — verificar sensores, interpretar sinais e correlacionar com o histórico exige investigações que poderiam ser antecipadas se houvesse uma visão consolidada e preditiva do estado da máquina. A falta de uma fonte única e confiável de dados prejudica seu planejamento e reduz a eficiência das visitas.

#### Expectativas e Preocupações

Isac espera uma solução que antecipe qual componente tem maior probabilidade de falhar, entregue histórico organizado do equipamento e forneça instruções ou evidências que o auxiliem na preparação do atendimento. Uma ferramenta preditiva que indique a peça provável e priorize chamados permitiria a ele montar o kit de peças correto, otimizar rotas e aumentar a taxa de reparo na primeira visita.
Por outro lado, Isac manifesta preocupação quanto à confiabilidade das previsões: precisa entender por que uma determinada peça foi indicada (justificativa baseada em dados) para confiar na sugestão e agir com segurança. Transparência nas bases da predição e a possibilidade de consultar o histórico detalhado são requisitos importantes para que ele adote a ferramenta no fluxo diário.

#### Relevância da Persona para o Projeto
A persona Isac Santos representa o usuário que consome previsões em campo e transforma insights em ação operacional. Entender suas necessidades permite projetar recursos que reduzam deslocamentos desnecessários, aumentem a eficiência dos atendimentos e proporcionem economia de tempo e custo para a empresa e para o cliente. Ao atender às expectativas de Isac — previsões confiáveis, histórico organizado e justificativas claras — o sistema contribui diretamente para melhores indicadores de serviço e satisfação do cliente.

### Conclusões Gerais

A criação e definição dessas personas permitiu ao grupo compreender de forma mais clara para quem o produto em desenvolvimento será destinado. Esse entendimento orienta a construção de funcionalidades relevantes para os profissionais que irão utilizá-lo, ao mesmo tempo em que assegura que a solução gere valor estratégico e operacional para a empresa, potencialmente aumentando sua competitividade no mercado. A idealização das personas serve como um guia sólido para alinhar o produto às expectativas e desafios dos seus futuros usuários, bem como de todos que irão se beneficiar da solução.