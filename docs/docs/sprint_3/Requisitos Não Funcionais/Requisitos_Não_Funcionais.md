---
title: Pipeline
sidebar_label: Pipeline
sidebar_position: 1
---
# Requisitos Não Funcionais

De acordo com o ISO/IEC 25010, que define um modelo de qualidade para produtos de TIC (Tecnologias de Informação e Comunicação) e software, um Requisito Não Funcional refere-se a um atributo de qualidade que descreve como o sistema deve se comportar, em vez de especificar o que o sistema deve fazer. Esses requisitos estão organizados em características e subcaracterísticas de qualidade — como desempenho, segurança, compatibilidade, capacidade de interação, confiabilidade e segurança funcional — que, em conjunto, estabelecem critérios para especificar, medir e avaliar a qualidade do produto ao longo de seu ciclo de vida, assegurando que ele atenda tanto às necessidades explícitas quanto implícitas dos usuários e outras partes interessadas.

Os RNFs foram definidos a partir de uma análise prática das personas, das user stories e de várias técnicas de elicitação — como entrevistas, workshops e revisão de documentos. Usamos critérios de viabilidade técnica, impacto no negócio e mensurabilidade para priorizar requisitos que sejam realizáveis e testáveis.

Segue os RNFs elaborados pelo grupo:

# Requisitos Não Funcionais

RNF 01 – Capacidade de Monitoramento

O sistema deve ser capaz de suportar o monitoramento de até 200 bombas simultaneamente sem degradação perceptível no desempenho. Isso implica que a interface do usuário deve permanecer responsiva e que o sistema deve processar as notificações de alerta de forma eficiente e em tempo hábil.

Para validar este requisito, será configurado um ambiente de simulação com 200 bombas enviando dados em tempo real. A média dos atrasos da resposta do site deve se manter em aproximadamente 5 segundos, assegurando a entrega rápida de informações críticas aos operadores.


RNF 02 – Notificação e Confirmação de Falhas


O sistema deve notificar os usuários proativamente sobre a iminência de falhas em máquinas, enviando alertas em tempo real. Além disso, a plataforma deve exigir uma confirmação de recebimento do usuário dentro de um período máximo de 5 minutos. Se a confirmação não for recebida nesse intervalo, o sistema deve registrar a falta de resposta e iniciar um processo de escalonamento.

Para validar este requisito, serão simuladas falhas em diversas máquinas, e o envio das notificações será monitorado de perto. Durante o teste, algumas notificações serão propositalmente ignoradas, a fim de verificar se o sistema detecta a falta de resposta e realiza o reenvio das notificações dentro do intervalo de tempo esperado, garantindo que o alerta chegue ao responsável.


RNF 03 – Latência do Processamento de Dados

O microsserviço de processamento de dados por lotes (batches) deve ser capaz de processar e armazenar 1000 registros por segundo no banco de dados de séries temporais. A latência média entre a chegada dos dados no broker e o armazenamento final deve ser inferior a 1 segundo, garantindo a atualização quase em tempo real do sistema.

Para validar este requisito, será injetado um volume de 1000 registros por segundo no sistema. A latência será medida desde o momento em que os dados chegam ao Broker MQTT até o seu registro final no Banco de Dados de Séries Temporais. O objetivo é confirmar que o tempo médio de processamento e armazenamento se mantém abaixo de 1 segundo sob carga elevada.


RNF 04 – Confiabilidade do Modelo Preditivo

O modelo de Machine Learning (ML) deve alcançar uma acurácia mínima de 85% em validações com dados históricos antes de ser implantado em produção. Essa alta taxa de acerto é crucial para garantir a confiabilidade das previsões de falhas, permitindo uma tomada de decisão precisa por parte dos operadores e reduzindo alarmes falsos.

Para validar a confiabilidade, o modelo será treinado e validado com um conjunto de dados históricos representativo. A acurácia média será calculada em pelo menos três rodadas de validação cruzada, um método estatístico que divide o conjunto de dados em subconjuntos para treinamento e teste. Será verificado se o valor de acurácia não fica abaixo de 85% em nenhuma das rodadas, confirmando a consistência e a eficácia do modelo.


RNF 05 – Recuperação de Conexão e Dados

O sistema deve ser capaz de recuperar dados automaticamente caso a conexão de uma máquina com o servidor seja perdida. A sincronização de todos os dados gerados offline deve ser realizada em até 24 horas após a conexão ser restabelecida, assegurando que não haja perda de informações críticas.

Para validar este requisito, uma máquina será desconectada do servidor por 10 minutos enquanto continua a gerar dados. Após esse período, a máquina será reconectada para que o sistema inicie o processo de sincronização. Será verificado se todos os dados gerados durante a desconexão foram transmitidos e registrados corretamente, sem qualquer perda ou inconsistência.

RNF 06 – Tempo de Resposta da Interface

Ao acessar um dashboard geral ou os dados de uma bomba específica, o sistema deve exibir as informações em um tempo máximo de 2 minutos. Esse requisito é fundamental para garantir que os usuários recebam feedback visual e dados operacionais de forma ágil, permitindo uma análise e resposta rápidas.

Para validar este requisito, serão realizados diversos registros de tempo de resposta da aplicação, tanto em um ambiente de simulação com múltiplas bombas quanto com os dados do cliente em produção, se disponível. O teste consistirá em medir o tempo que leva para o dashboard ser carregado por completo, desde o clique do usuário até a exibição de todos os dados das bombas. A média dos resultados não deve exceder o limite de 3 minutos.

RNF 07 – Clareza sobre Incertezas do Modelo

O sistema deve apresentar o nível de confiança das previsões do modelo de forma clara, permitindo que o usuário compreenda o que a incerteza representa e suas limitações, sem a necessidade de conhecimento técnico avançado. A interface deve traduzir a complexidade do modelo em informações intuitivas, apoiando a tomada de decisões com segurança.

Para validar este requisito, será conduzido um teste de usabilidade com usuários representativos. A eles, será solicitado que expliquem, com suas próprias palavras, o que entenderam do nível de confiança mostrado pelo sistema. O critério de aceitação é que pelo menos 80% dos usuários demonstrem uma compreensão correta do que a incerteza representa, confirmando que a interface comunica a informação de forma eficaz e acessível.


# Conclusão:

Revisando estes requisitos temos uma ideia mais clara das qualidades necessárias: desempenho e eficiência de recursos, confiabilidade e disponibilidade, segurança, usabilidade, capacidade de manutenção e precisão das previsões. Esses critérios, todos mensuráveis, orientam decisões de arquitetura, projeto e testes para garantir que o sistema entregue valor operacional e suporte decisões confiáveis.

bibliografia: 

(https://olivroqueaprende.com/WDK/Software_Requirements_3rd_Edition.pdf)

(https://cdn.standards.iteh.ai/samples/78176/13ff8ea97048443f99318920757df124/ISO-IEC-25010-2023.pdf?utm_source=chatgpt.com)
