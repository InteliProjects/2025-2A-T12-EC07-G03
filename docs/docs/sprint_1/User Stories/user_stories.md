---
title: User Stories
sidebar_label: User Stories
sidebar_position: 1
---

## O que é uma User Story?

&emsp;Uma User Story (ou História de Usuário) é uma descrição informal e em linguagem natural de uma funcionalidade de um sistema de software, contada da perspectiva do usuário final. O objetivo é articular como uma funcionalidade específica agregará valor ao cliente. Geralmente, as histórias de usuário seguem um modelo simples:

&emsp;**Como um(a)** ```tipo de usuário```, **eu quero** ```realizar uma ação``` **para que** ```eu possa alcançar um objetivo```.

&emsp;Essa estrutura ajuda a equipe de desenvolvimento a entender o "quem", o "o quê" e o "porquê" de um requisito de forma concisa, mantendo o foco no usuário e em suas necessidades. 

---

## User Stories do Projeto

&emsp;A seguir estão detalhadas as User Stories para a solução de análise preditiva de falhas em motobombas da Itubombas.

### US01: Alerta visual em tela

*   **Como** um usuário do sistema,
*   **quero que**, quando uma determinada máquina esteja operando fora dos seus limites, seja exibido um alerta visual na tela,
*   **a fim de** que eu possa perceber o problema imediatamente sem depender de outros fatores de notificação.

#### Critérios de Aceite:
-   Quando uma ou mais variáveis de operação excederem os limites pré-definidos, um alarme deve ser exibido na interface.
-   O alarme deve ter alto destaque visual (ex: cores fortes como vermelho, tamanho grande, ícones de alerta).
-   O alarme deve conter as seguintes informações:
    -   TAG (identificador da máquina).
    -   Nome da variável fora do limite.
    -   Valor atual da variável.
    -   Valor limite da variável.
    -   Uma indicação do quão fora do limite o valor atual se encontra (percentual ou absoluto).
-   O alarme deve permanecer visível até que o usuário o reconheça ou confirme a resolução.
-   O sistema deve ser capaz de exibir múltiplos alertas simultaneamente caso várias máquinas apresentem problemas.

### US02: Identificação de parte crítica

*   **Como** um usuário do sistema,
*   **quero que**, quando seja exibida a informação de que determinada máquina irá falhar, essa informação também contenha a possível peça/parte da máquina que irá falhar,
*   **a fim de** que a equipe de manutenção possa, no processo de manutenção, avaliar primeiramente essa peça, possivelmente diminuindo o tempo de manutenção.

#### Critérios de Aceite:
-   A predição de falha gerada para uma máquina deve incluir a peça ou componente com maior probabilidade de ser a causa da falha.
-   Caso mais de uma peça seja identificada como crítica, o sistema deve exibir uma lista ordenada por prioridade (da mais provável para a menos provável).
-   Esta informação deve ser apresentada de forma clara e direta junto aos outros dados da predição de falha, sem a necessidade de navegar para outra tela.

### US03: Visualização de histórico de alertas

*   **Como** um usuário do sistema,
*   **quero** poder visualizar uma lista ou relatório de alertas que foram emitidos no passado,
*   **a fim de** analisar eventos históricos.

#### Critérios de Aceite:
-   O sistema deve ter uma seção dedicada à visualização do histórico de alertas.
-   Deve ser possível filtrar o histórico por máquina (TAG).
-   Deve ser possível filtrar o histórico por um período de datas específico (data de início e fim).

### US04: Visualização de dados por máquina específica

*   **Como** um usuário do sistema,
*   **quero** poder visualizar os dados específicos (estado de funcionamento atual, previsão de falha, etc.) para uma máquina em específico,
*   **a fim de** obter um maior detalhamento acerca de tal máquina.

#### Critérios de Aceite:
-   O sistema deve exibir uma lista de todas as máquinas monitoradas.
-   O usuário deve poder selecionar uma máquina da lista para inspecionar.
-   Ao selecionar uma máquina, uma tela ou painel detalhado deve ser exibido, contendo todas as informações relevantes, como:
    -   Dados de operação em tempo real.
    -   Status atual (normal, alerta, etc.).
    -   Predição de falha (se aplicável).
    -   Histórico recente de alertas para aquela máquina.

### US05: Visualização em dashboard

*   **Como** um usuário do sistema,
*   **quero** ver o total de equipamentos em operação normal e os que têm alertas ativos,
*   **a fim de** ter uma visão geral imediata de todas as máquinas em operação.

#### Critérios de Aceite:
-   A tela principal (dashboard) deve exibir, em destaque, dois contadores:
    -   Número total de máquinas em estado "saudável" (operação normal).
    -   Número total de máquinas com alertas ativos.
-   O contador de máquinas saudáveis deve ter um indicador visual positivo (ex: cor verde, ícone de "check").
-   O contador de máquinas com alertas deve ter um indicador visual de atenção (ex: cor vermelha ou amarela, ícone de "alerta").

### US06: Predição de tempo de falha de máquina

*   **Como** um usuário do sistema,
*   **quero** ver a predição de tempo em horas para que uma determinada máquina, funcionando em seu estado atual, entre em estado de falha,
*   **a fim de** poder organizar e gerir melhor as equipes que prestam os serviços de manutenção em campo.

#### Critérios de Aceite:
-   Para uma máquina operando fora das condições ideais, o sistema deve exibir uma estimativa de tempo restante (em horas) para a ocorrência de uma falha, assumindo que as condições de operação permaneçam as mesmas.
-   A estimativa de tempo para falha deve ser exibida junto às outras informações principais da máquina.
-   Se o tempo estimado para a falha for considerado iminente (ex: menor que 340 horas, conforme exemplo), o valor deve ser destacado com um alerta visual (ex: cor vermelha, ícone de atenção) para indicar urgência.

## Conclusão: Guiando o Desenvolvimento com Foco no Usuário

&emsp;A utilização de User Stories, como as detalhadas acima, é fundamental para garantir que o processo de desenvolvimento seja genuinamente centrado no usuário. Ao traduzir requisitos complexos em narrativas simples e focadas na perspectiva de quem utilizará o sistema, as histórias de usuário asseguram que a equipe de desenvolvimento mantenha o foco no valor real a ser entregue.
