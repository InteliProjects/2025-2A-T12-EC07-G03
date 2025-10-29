---
title: Banco de dados Relacional
sidebar_label: Banco de dados Relacional
sidebar_position: 3
---
import useBaseUrl from '@docusaurus/useBaseUrl';

# Banco de dados Relacional

Considerando a arquitetura do projeto, o banco de dados relacional compõe a parte do projeto responsável pelo armazenamento estruturado das informações, após processamento pelo script e separação dos arquivos Parquet armazenados no Datalake.
O banco de dados utilizado é o PostgreSQL, executado em um contêiner Docker para facilitar o gerenciamento, a escalabilidade e a integração com outros componentes do projeto.

## Schema do banco de dados

<div style={{textAlign:'center'}}>
    <p><strong>Imagem 1 - Schema do Banco de dados</strong></p>
        <img
        src={useBaseUrl('/img/db_schema.png')}
        alt="Schema do Banco de dados"
        title="Schema do Banco de dados"
        style={{maxWidth:'100%', height:'auto'}}
        />
    <p>Fonte: Elaborado pelo grupo Flow Solutions (2025).</p>
</div>

### **1. machine\_model**

Armazena os modelos de máquinas disponíveis.

* **id** (UUID, PK): Identificador único do modelo da máquina.
* **name** (VARCHAR): Nome do modelo da máquina.
* **has\_model** (BOOLEAN): Indica se existe um modelo preditivo associado (`TRUE` ou `FALSE`).
* **description** (VARCHAR): Descrição opcional do modelo da máquina.

### **2. machine**

Contém informações sobre as máquinas cadastradas.

* **id** (UUID, PK): Identificador único da máquina.
* **model\_id** (UUID, FK → machine\_model.id): Modelo da máquina.
* **name** (VARCHAR): Nome da máquina.
* **location** (geometry(Point, 4326)): Localização geográfica da máquina no formato ponto (latitude/longitude).

### **3. feature**

Define os tipos de variáveis coletadas pelas máquinas.

* **id** (UUID, PK): Identificador único da feature.
* **name** (VARCHAR): Nome da feature (ex.: temperatura, pressão).
* **unit** (REAL): Unidade de medida associada à feature.
* **description** (VARCHAR): Descrição detalhada da feature.

### **4. value**

Armazena os valores medidos pelas máquinas em relação às features.

* **id** (UUID, PK): Identificador único da medição.
* **machine\_id** (UUID, FK → machine.id): Máquina responsável pelo dado.
* **feature\_id** (UUID, FK → feature.id): Feature medida.
* **value** (REAL): Valor medido.
* **log\_time** (TIMESTAMP): Momento em que a medição foi realizada.

### **5. dataframe**

Armazena arquivos de dados (dataframes) relacionados às máquinas.

* **id** (UUID, PK): Identificador único do dataframe.
* **machine\_id** (UUID, FK → machine.id): Máquina associada ao arquivo.
* **file\_path** (VARCHAR): Caminho do arquivo no bucket.

### **6. logs**

Contém os logs do sistema e mensagens recebidas.

* **id** (UUID, PK): Identificador único do log.
* **log\_time** (TIMESTAMP): Momento em que o log foi registrado.
* **topic** (VARCHAR): Tópico ou categoria do log.
* **payload** (VARCHAR): Conteúdo do log ou mensagem recebida.

### **7. models**

Armazena informações sobre os modelos preditivos utilizados.

* **id** (UUID, PK): Identificador único do modelo preditivo.
* **machine\_id** (UUID, FK → machine.id): Máquina associada ao modelo.
* **bucket\_address** (VARCHAR): Endereço do bucket onde o modelo está armazenado.
* **start\_date** (TIMESTAMP): Data de início do treinamento ou uso do modelo.
* **end\_date** (TIMESTAMP): Data de término ou validade do modelo.

### **8. metrics**

Armazena as métricas individuais dos modelos preditivos.

* **id** (UUID, PK): Identificador único da métrica.
* **model\_id** (UUID, FK → models.id): Modelo ao qual a métrica pertence.
* **title** (VARCHAR): Nome da métrica (ex.: Accuracy, Precision).
* **value** (VARCHAR): Valor da métrica.
