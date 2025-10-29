---
title: Exploração de dados para Séries Temporais
sidebar_label: Exploração para Séries Temporais
sidebar_position: 2
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Exploração dos dados

A exploração dos dados consiste no processo de explorar, visualizar e comparar as principais variáveis operacionais de bombas hidráulicas, utilizando gráficos e análises de correlação.
As bombas hidráulicas escolhidas para análise foram as bombas ITU-415 e ITU-693, pois eram os modelos com dados mais completos.

---

## Modelos das máquinas utilizadas

- **ITU-415**

Motobomba Diesel ITU-108S17 Cabinada
Sucção 10"x8" Descarga
Rotor 17,5" SCANIA DC13

Período de operação: 01/06/2025 a 17/07/2025

- **ITU-693**

Motobomba Diesel ITU-63C17
Sucção 6" X 4" Descarga
Rotor 17" CUMMINS PU-240 POLIETILENO

Período de operação: 13/05/2025 17:35 à 22/07/2025 23:59

---

## Carregamento e Preparação dos Dados

- Os arquivos CSV processados de ambas as bombas são carregados.
- Os arquivos CSV utilizados passam pelo processamento de dados da Pipeline, onde os dados são limpos, convertidos para os tipos corretos, etc.
- As colunas principais são convertidas para tipos numéricos, garantindo que os dados estejam prontos para análise.
- As features selecionadas são filtradas e os valores zerados são removidos, mantendo apenas dados relevantes para análise.
- Todos os valores que compreendem os momentos que a máquina esteve desligada foram removidos do dataframe para essa análise

---

## Seleção das Features

Algumas features específicas do dataframe foram selecionadas e utilizadas na análise de correlação e séries temporais das bombas. Todas fazem parte da curva de operação da bomba e são essenciais para monitorar o funcionamento e a saúde do sistema.

<div style={{ display: 'flex', justifyContent: 'center' }}>
    <table>
        <thead>
            <tr>
                <th>Feature</th>
                <th>Descrição</th>
                <th>Unidade</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Eng_RPM</td>
                <td>Rotação do motor</td>
                <td>RPM</td>
            </tr>
            <tr>
                <td>Bat_V</td>
                <td>Tensão na bateria</td>
                <td>V</td>
            </tr>
            <tr>
                <td>Char_V</td>
                <td>Tensão no alternador</td>
                <td>V</td>
            </tr>
            <tr>
                <td>Oil_P</td>
                <td>Pressão de óleo no motor</td>
                <td>mca</td>
            </tr>
            <tr>
                <td>Cool_T</td>
                <td>Temperatura do líquido de arrefecimento</td>
                <td>°C</td>
            </tr>
            <tr>
                <td>Fuel_L</td>
                <td>Nível de combustível no tanque do motor</td>
                <td>%</td>
            </tr>
            <tr>
                <td>Oil_L</td>
                <td>Nível de óleo do motor</td>
                <td>%</td>
            </tr>
        </tbody>
    </table>
</div>

- **Eng_RPM**: Mede a rotação do motor em rotações por minuto (RPM). É um dos principais indicadores de funcionamento e desempenho da bomba.
- **Bat_V**: Indica a voltagem da bateria do sistema. Quedas ou variações podem sinalizar problemas elétricos ou de partida.
- **Char_V**: Refere-se à voltagem do alternador, responsável pelo sistema de carga da bateria.
- **Oil_P**: Mede a pressão do óleo no motor, fundamental para garantir a lubrificação adequada e evitar falhas mecânicas.
- **Cool_T**: Temperatura do líquido de arrefecimento, importante para monitorar o risco de superaquecimento.
- **Fuel_L**: Nível de combustível disponível no tanque do motor, útil para prever paradas por falta de combustível.
- **Oil_L**: Nível de óleo do motor, essencial para manutenção preventiva e evitar danos por falta de lubrificação.

Essas variáveis são monitoradas continuamente e permitem identificar padrões, eventos críticos e possíveis correlações entre diferentes aspectos do funcionamento das bombas.

---

## Visualização das Séries Temporais

- **Gráfico 1:** Séries temporais das features da ITU-415, com marcação dos valores máximos e mínimos.

<div style={{textAlign:'center'}}>
    <p><strong>Imagem 1 - Séries temporais das features da ITU-415</strong></p>
        <img
        src={useBaseUrl('/img/Features_ITU415.png')}
        alt="Série temporal das features - ITU-415"
        title="Série temporal das features - ITU-415"
        style={{maxWidth:'100%', height:'auto'}}
        />
    <p>Fonte: Elaborado pelo grupo Flow Solutions (2025).</p>
</div>

- **Gráfico 2:** Séries temporais das features da ITU-693, também com marcação dos extremos.

<div style={{textAlign:'center'}}>
    <p><strong>Imagem 2 - Séries temporais das features da ITU-693</strong></p>
        <img
        src={useBaseUrl('/img/Features_ITU693.png')}
        alt="Série temporal das features - ITU-693"
        title="Série temporal das features - ITU-693"
        style={{maxWidth:'100%', height:'auto'}}
        />
    <p>Fonte: Elaborado pelo grupo Flow Solutions (2025).</p>
</div>

- **Gráfico 3:** Gráficos de barras comparando as médias das features entre ITU-415 e ITU-693, alinhados horizontalmente, com limites de escala ajustados para facilitar a visualização.

<div style={{textAlign:'center'}}>
    <p><strong>Imagem 3 - Comparação das médias de cada feature das bombas ITU-415 e ITU-693</strong></p>
        <img
        src={useBaseUrl('/img/Medias_Features.png')}
        alt="Comparação das médias de cada feature das bombas ITU-415 e ITU-693"
        title="Comparação das médias de cada feature das bombas ITU-415 e ITU-693"
        style={{maxWidth:'100%', height:'auto'}}
        />
    <p>Fonte: Elaborado pelo grupo Flow Solutions (2025).</p>
</div>

---

## Valores mínimos e máximos

Com base nos dados de operação normal das bombas, após analisar os gráficos, é possível inferir valores mínimos e máximos aceitáveis para cada feature escolhida. Sendo assim, foi criada esta tabela com definição dos valores máximos e mínimos de cada feature, considerando uma margem de erro específica para cada uma delas.

| Features escolhidas                              | Valor Mínimo Aceitável | Valor Máximo Aceitável | Margem de Erro |
| ------------------------------------------------ | ---------------------- | ---------------------- | -------------- |
| Eng_RPM (Rotação do Motor)                       | 1000 RPM*              | 2000 RPM               | 5%             |
| Bat_V (Tensão na Bateria)                        | 28 V                   | 29 V                   | 1%             |
| Char_V (Tensão no Alternador)                    | 27 V                   | 28 V                   | 1%             |
| Oil_P (Pressão do Óleo)                          | 430 mca                | 800 mca                | 2%             |
| Cool_T (Temperatura do Líquido de Arrefecimento) | 50 °C                  | 80 °C                  | 5%             |
| Fuel_L (Nível de Combustível)                    | 10%                    | 100%                   | 10%            |
| Oil_L (Nível de Óleo)                            | 40%                    | 80%                    | 10%            |

> * O valor  mínimo aceitável do Eng_RPM é 1000RPM, porém deve ser feita uma limpeza dos dados para desconsiderar períodos de desaceleração da máquina, evitando que o sistema detecte o momento de desligamento/desaceleração do motor da máquina como um erro de operação incorreta ou falha.

A partir dessa análise, é possível apontar que, os valores definidos como máximos e mínimos, compõem o intervalo de valores considerados como operação normal e saudável da máquina. Ou seja, todos os valores fora desse intervalo serão considerados como fora do normal, e poderão ser considerados fatores determinantes para possível falhas.
