---
title: Datalake
sidebar_label: Datalake
sidebar_position: 3
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Datalake

&emsp;Um Datalake é um repositório centralizado que permite armazenar todos os seus dados em qualquer escala. Você pode armazenar seus dados como eles são, sem precisar estruturá-los primeiro, e executar diferentes tipos de análises para obter insights. Ele pode armazenar dados estruturados, semi-estruturados e não estruturados. A principal vantagem de um Datalake é a sua flexibilidade e a capacidade de armazenar grandes volumes de dados brutos, o que permite análises futuras que talvez não tenham sido previstas no momento da ingestão dos dados.

&emsp;Por outro lado, um Datalakehouse é uma arquitetura de dados híbrida que combina os benefícios de um Datalake (flexibilidade, baixo custo de armazenamento, capacidade de lidar com dados não estruturados) com os recursos de gerenciamento de dados e desempenho de um Data Warehouse (esquema on-write, transações ACID, governança de dados, desempenho de consulta). Ele busca resolver os desafios de confiabilidade e desempenho que podem surgir em Datalakes puros, especialmente quando se trata de dados estruturados e semi-estruturados que precisam ser consultados de forma eficiente e consistente. O Apache Iceberg, que será utilizado com o Nessie neste projeto, é um exemplo de formato de tabela que permite a construção de um Datalakehouse, adicionando capacidades de Data Warehouse sobre o armazenamento de objetos em um Datalake.

## Qual a finalidade de ter um Datalake no presente projeto?

&emsp;Neste projeto, a implementação de um Datalake com a arquitetura Datalakehouse é fundamental para estabelecer uma infraestrutura de dados robusta e flexível. A principal finalidade é armazenar de forma centralizada e escalável todos os dados provenientes do broker que recebe e transporta os dados gerados pelos sensores posicionados nas motobomas. Isso inclui dados brutos, semi-estruturados e estruturados, permitindo que sejam armazenados em seu formato original, sem a necessidade de pré-processamento complexo. Isso faz parte da implementação de uma arquitetura de engenharia de dados que busca melhorar a qualidade dos dados que a Itubombas pode disponibilizar para análised. Essa abordagem oferece diversas vantagens:

* Flexibilidade para Análises Futuras: Ao armazenar dados brutos, o Datalake permite que novas análises e casos de uso sejam explorados no futuro, sem a necessidade de reengenharia de dados. Dados que hoje podem não parecer relevantes, amanhã podem ser cruciais para novos insights.
* Fonte Única da Verdade: Centraliza todos os dados do broker em um único local, eliminando silos de dados e garantindo que todas as equipes acessem a mesma versão dos dados, promovendo consistência e confiabilidade.
* Escalabilidade: A arquitetura baseada em armazenamento de objetos (MinIO localmente, S3 na AWS) permite escalar o armazenamento de dados de forma praticamente ilimitada e a um custo muito mais baixo em comparação com bancos de dados tradicionais.
* Suporte a Diversos Tipos de Dados: Capacidade de ingerir e armazenar dados em diferentes formatos e estruturas, desde logs e eventos do broker até dados transacionais e de referência.
* Governança e Controle de Versão (via Nessie): A integração com o Nessie adiciona capacidades de controle de versão aos dados, permitindo gerenciar o histórico de alterações, criar branches para experimentação e garantir a rastreabilidade dos dados, o que é vital para auditorias e conformidade.
* Otimização para Consultas (via Dremio e Iceberg): Embora armazene dados brutos, a camada Datalakehouse (Iceberg e Dremio) permite que esses dados sejam consultados de forma otimizada, com desempenho similar ao de um Data Warehouse, facilitando o acesso para análises de BI e data science.

&emsp;Em resumo, o Datalake serve como a espinha dorsal da nossa estratégia de dados, garantindo que tenhamos uma base sólida para coletar, armazenar, processar e analisar os dados gerados pelo broker, suportando tanto as necessidades atuais quanto as futuras do projeto.

## Função de cada componente

* PostgreSQL (Backend para persistência do Nessie):

&emsp;O PostgreSQL é um sistema de gerenciamento de banco de dados relacional de código aberto, robusto e altamente extensível. Neste projeto, ele serve como o backend de persistência para o Nessie. Isso significa que todas as informações de metadados do catálogo do Nessie, como as referências de tabelas Iceberg, histórico de commits e branches, são armazenadas no PostgreSQL. A escolha do PostgreSQL garante a durabilidade, consistência e integridade desses metadados críticos. A configuração no docker-compose.yml expõe a porta 5433 do host para a porta 5432 do contêiner, evitando conflitos com outras instâncias de PostgreSQL que possam estar rodando localmente. Além disso, um volume persistente (./postgres_data) é montado para garantir que os dados do banco de dados não sejam perdidos quando o contêiner for reiniciado ou removido.

* Nessie (Catalog para Iceberg)

&emsp;O Nessie é um catálogo de dados de código aberto, compatível com a API do Apache Iceberg, que adiciona capacidades de controle de versão (git-like) para tabelas de Datalake. Ele permite que os usuários gerenciem seus dados como código, com funcionalidades como branches, merges, commits e rollbacks. Isso é importante para a governança de dados, experimentação e garantia de qualidade em um ambiente de Datalakehouse. No contexto deste projeto, o Nessie atua como o ponto central para a definição e gerenciamento das tabelas Iceberg, permitindo que diferentes ferramentas (como o Dremio) acessem e manipulem os dados de forma consistente e transacional. O Nessie utiliza o PostgreSQL como seu backend para armazenar os metadados do catálogo, garantindo a persistência e a integridade das informações de controle de versão. A porta 19120 é exposta para acesso externo.

* MinIO (Object Storage S3-compatible)

&emsp;O MinIO é um servidor de armazenamento de objetos de código aberto, compatível com a API do Amazon S3. Ele é ideal para armazenar grandes volumes de dados não estruturados, como arquivos de log, imagens, vídeos e, no contexto de um Datalake, os próprios arquivos de dados das tabelas Iceberg. No nosso setup, o MinIO atua como a camada de armazenamento subjacente para o Datalake, onde os dados brutos e processados serão persistidos. A compatibilidade com S3 é importante, pois permite que ferramentas que interagem com o S3 (como o Dremio e o Nessie, através do Iceberg) se conectem facilmente ao MinIO, seja em um ambiente local ou na nuvem. As portas 9000 (API) e 9001 (console) são expostas, e um volume (./minio_data) garante a persistência dos objetos armazenados.

<div style={{textAlign:'center'}}>
    <p><strong>Figura 1 - Minio</strong></p>
        <img
        src={useBaseUrl('/img/minio.png')}
        alt="Minio"
        title="Minio"
        style={{maxWidth:'80%', height:'auto'}}
        />
    <p>Fonte: Elaborado pelo grupo Flow Solutions (2025).</p>
</div>

* Dremio (Query Engine)

&emsp;O Dremio é um query engine de código aberto que permite aos usuários consultar dados diretamente em seus Datalakes, sem a necessidade de ETL (Extract, Transform, Load) complexo. Ele atua como uma camada de virtualização de dados, otimizando consultas e fornecendo uma interface SQL para diversas fontes de dados, incluindo o armazenamento de objetos (MinIO, S3) e catálogos como o Nessie. No nosso setup, o Dremio é a ferramenta que permitirá aos usuários finais e aplicações consultarem as tabelas Iceberg armazenadas no MinIO e gerenciadas pelo Nessie. Ele oferece recursos de aceleração de consulta, como reflections, que pré-computam e armazenam dados em formatos otimizados para desempenho. As portas 9047 (UI), 31010 (client) e 32010 (engine) são expostas, permitindo a interação com a interface web e a conexão de ferramentas de BI ou SQL clients. Volumes persistentes (./dremio_data e ./dremio_conf) são utilizados para garantir que as configurações e os dados de metadados do Dremio sejam preservados.

<div style={{textAlign:'center'}}>
    <p><strong>Figura 2 - Dremio</strong></p>
        <img
        src={useBaseUrl('/img/dremio.png')}
        alt="Dremio"
        title="Dremio"
        style={{maxWidth:'80%', height:'auto'}}
        />
    <p>Fonte: Elaborado pelo grupo Flow Solutions (2025).</p>
</div>

## Como isso pode ser facilmente migrado para AWS?

&emsp;A arquitetura do Datalake implementada localmente com Docker Compose foi projetada com a portabilidade em mente, utilizando tecnologias de código aberto e padrões amplamente adotados na indústria. Isso facilita enormemente a migração para um ambiente de nuvem, como a Amazon Web Services (AWS), sem a necessidade de reescrever grande parte da lógica ou da configuração. A seguir, detalhamos como cada componente pode ser facilmente migrado para seus equivalentes na AWS:


## Conclusão

&emsp;A implementação deste Datalake com a arquitetura Datalakehouse, utilizando PostgreSQL, Nessie, MinIO e Dremio, representa um passo estratégico na gestão de dados do projeto. Esta abordagem não só oferece a flexibilidade e a escalabilidade de um Datalake tradicional, mas também incorpora as capacidades de governança, transacionalidade e desempenho de um Data Warehouse, graças ao uso do Apache Iceberg e do Nessie para controle de versão.

&emsp;Ao centralizar os dados provenientes do broker, garantimos uma fonte única da verdade, essencial para análises consistentes e tomadas de decisão informadas. A escolha de componentes de código aberto e a conteinerização via Docker Compose asseguram que a solução seja robusta, replicável e, mais importante, altamente portátil. A facilidade de migração para a Amazon Web Services (AWS), utilizando serviços equivalentes como Amazon RDS, S3, ECS/EKS e Athena/Redshift Spectrum, demonstra a visão de longo prazo da arquitetura, permitindo que a solução evolua de um ambiente local para uma infraestrutura de nuvem escalável e gerenciada, conforme as necessidades do projeto cresçam.

&emsp;Em suma, este Datalakehouse é uma fundação sólida para a estratégia de dados, capacitando o projeto a extrair valor máximo de seus dados, com agilidade, governança e preparo para o futuro.

