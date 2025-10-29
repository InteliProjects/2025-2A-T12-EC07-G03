---
sidebar_position: 1
custom_edit_url: null
---

# Requisitos Funcionais

&emsp;Os requisitos funcionais definem as funcionalidades essenciais que o sistema deve oferecer para atender às necessidades dos usuários e alcançar os objetivos do projeto. Eles servem como alicerce para a visão geral do software, descrevendo de forma objetiva e direta o que o sistema precisa executar.

&emsp;Esses requisitos orientam todo o processo de desenvolvimento e ajudam a garantir que as entregas correspondam às expectativas. Para contextualizar melhor as interações previstas, cada funcionalidade apresentada a seguir está associada ao seu propósito e ao perfil de usuário que irá utilizá-la, conforme descrito na Documentação de Personas.

## RF01 - Diagnóstico Antecipado de Falha
**Descrição**:O sistema deve identificar comportamentos anormais nas variáveis monitoradas e indicar a probabilidade de falha iminente, com destaque para a parte da motobomba potencialmente afetada. 

**Tipo de usuário**: Manutentor (time de serviços / engenheiros de manutenção).

**Propósito**: Permitir que a manutenção seja planejada com antecedência, reduzindo paradas inesperadas e custos emergenciais.

## RF02 - Geração de Alertas
**Descrição**: O sistema deve gerar alertas graduais (baixa, média e alta prioridade) com base em padrões operacionais que historicamente antecedem falhas, mesmo que ainda não estejam em condição crítica.

**Tipo de usuário**: Manutentor (time de serviços / engenheiros de manutenção).

**Propósito**: Possibilitar inspeções direcionadas antes que o problema se agrave.

## RF03 - Monitoramento de cumprimento de contrato
**Descrição**: O sistema deve registrar e disponibilizar relatórios sobre horas de operação, número de partidas e modo de operação (manual ou automático), cruzando com limites contratuais.

**Tipo de usuário**: Vendedor

**Propósito**: Identificar clientes que estão utilizando as máquinas fora dos parâmetros acordados, possibilitando ações comerciais ou de renegociação.

## RF04 - Identificação de uso indevido
**Descrição**: O sistema deve detectar e notificar sobre operação fora do BEP (Best Efficiency Point) ou em ranges não saudáveis, incluindo excesso de horas contínuas ou funcionamento sem carga adequada.

**Tipo de usuário**: Vendedor

**Propósito**: Ter evidências objetivas de má utilização do equipamento para fins de cobrança, treinamento ou renegociação.

## RF05 - Sugestão de realocação de máquinas
**Descrição**: O sistema deve indicar quais equipamentos estão operando com risco elevado e sugerir troca por outros disponíveis em estoque ou locação interna.

**Tipo de usuário**: Time de operações / operador de logística.

**Propósito**: Garantir continuidade de operação no cliente com mínima interrupção.

## RF06 - Ajuste fino de parâmetros operacionais
**Descrição**: O sistema deve apresentar ajustes recomendados (como faixa de RPM, pressão de sucção e recalque) para manter o equipamento próximo ao ponto de melhor eficiência (BEP).

**Tipo de usuário**: Engenheiro de aplicação.

**Propósito**: Garantir operação estável e eficiente, aumentando a vida útil do equipamento.

## RF07 - Histórico detalhado de operação
**Descrição**: O sistema deve permitir a consulta de histórico de dados operacionais (sensores, alarmes, eventos) por equipamento e período, com possibilidade de exportação.

**Tipo de usuário**: Todos (Manutentor, Vendedor, Operações, Engenheiro de aplicação).

**Propósito**: Fornecer base para análise de falhas, auditoria e acompanhamento de desempenho.

## RF08 - Painel de status em tempo real
**Descrição**: O sistema deve exibir um painel com a condição atual de todos os equipamentos monitorados, destacando os que apresentam risco elevado.

**Tipo de usuário**: Operações, Manutentor.

**Propósito**: Permitir resposta rápida e priorização de recursos.

## RF09 – Retreinamento do Modelo de IA
**Descrição:** O sistema deve permitir o retreinamento periódico do modelo preditivo utilizando novos dados coletados, com possibilidade de ajustes automáticos ou manuais nos parâmetros para melhorar a acurácia. Deve manter histórico de versões para possibilitar rollback seguro.

**Tipo de usuário:** Engenheiro de aplicação e time de serviços/engenheiros de manutenção.

**Propósito:** Garantir que o modelo permaneça atualizado e com alto desempenho, acompanhando mudanças nas condições reais de operação.

## RF10 – Interface de Comunicação Externa (API)

**Descrição:** O sistema deve disponibilizar uma API segura para integração com sistemas externos, permitindo consulta de status, alertas e previsões. A API deve ter autenticação, controle de acesso e respostas em formato padronizado (ex.: JSON).

**Tipo de usuário:** Vendedor, time de operações/operador de logística e engenheiro de aplicação

**Propósito:** Possibilitar que dados e predições sejam utilizados por outras plataformas e aplicações, ampliando a utilidade e integração do sistema no ecossistema da empresa.

## Conclusão
&emsp;Definir requisitos funcionais de forma clara é essencial para garantir que o sistema atenda plenamente às necessidades dos usuários. As funcionalidades descritas foram elaboradas para tornar a identificação e a classificação de fissuras mais ágil, precisa e confiável. Com essas diretrizes, o sistema terá uma base robusta para gerar valor real e consistente no dia a dia de seus usuários.