# 🚀 Tutorial Completo: Setup Dremio + MinIO + Nessie para Apache Iceberg

Este guia completo explica como configurar um ambiente de data lakehouse usando Dremio, MinIO e Nessie com suporte ao formato Apache Iceberg. É importante destacar que este tutorial foi escrito por **Inteligência Artificial**.

## 📋 Índice

1. [Visão Geral da Arquitetura](#-visão-geral-da-arquitetura)
2. [Componentes da Stack](#-componentes-da-stack)
3. [Pré-requisitos](#-pré-requisitos)
4. [Tutorial Passo a Passo](#-tutorial-passo-a-passo)
5. [FAQ - Problemas Comuns](#-faq---problemas-comuns)
6. [Verificação e Testes](#-verificação-e-testes)

## 🏗️ Visão Geral da Arquitetura

### Como Funciona

1. **Dados CSV** são processados pelo pipeline Python
2. **Conversão para Parquet** e upload para MinIO (S3-compatible)
3. **Dremio** acessa os dados via S3 e permite queries SQL
4. **Nessie** gerencia versionamento e catalogo das tabelas
5. **Tabelas Iceberg** são criadas com ACID transactions e time travel

## 🧩 Componentes da Stack

### 🗄️ **MinIO**
- **Função**: Object Storage compatível com S3
- **Porta**: 9000 (API), 9001 (Console)
- **Uso**: Armazenar arquivos Parquet e metadados Iceberg

### 🔍 **Dremio**
- **Função**: Query Engine e Data Virtualization
- **Porta**: 9047
- **Uso**: Interface SQL para consultar dados, criar tabelas Iceberg

### 🌊 **Nessie**
- **Função**: Git-like Data Catalog
- **Porta**: 19120
- **Uso**: Versionamento de tabelas, metadados Iceberg, branches de dados

## ✅ Pré-requisitos

- Docker e Docker Compose instalados
- 8GB RAM disponível (mínimo)
- Portas 9000, 9001, 9047, 19120, 31010, 32010 disponíveis
- Navegador web moderno
- Terminal com curl disponível

## 🎯 Tutorial Passo a Passo

### Passo 1: Iniciar os Serviços

1. **Salve o docker-compose.yml** em uma pasta do projeto:

```yaml
version: "3.9"

services:

  dremio:
    platform: linux/x86_64
    image: dremio/dremio-oss:latest
    ports:
      - 9047:9047
      - 31010:31010
      - 32010:32010
    container_name: dremio
    volumes:
      - ./dremio_data:/opt/dremio/data
      - ./dremio_conf:/opt/dremio/conf
    user: "0:0" 

  minioserver:
    image: minio/minio
    ports:
      - 9000:9000
      - 9001:9001
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    container_name: minioserver
    command: server /data --console-address ":9001"
    volumes:
      # Persistência dos objetos
      - ./minio_data:/data

  nessie:
    image: projectnessie/nessie
    container_name: nessie
    ports:
      - "19120:19120"
    volumes:
      # Persistência do banco interno do Nessie (H2 DB por padrão)
      - ./nessie_data:/var/nessie

networks:
  default:
    name: iceberg_env
    driver: bridge
```

2. **Execute o Docker Compose**:

```bash
docker-compose up -d
```

3. **Verifique se todos os serviços estão rodando**:

```bash
docker-compose ps
```

### Passo 2: Acessar as Interfaces Web

1. **MinIO Console**: http://localhost:9001
   - Usuário: `minioadmin`
   - Senha: `minioadmin`

2. **Dremio**: http://localhost:9047
   - Primeira vez: criar conta de administrador

3. **Nessie API**: http://localhost:19120/api/v2
   - Endpoint REST para verificação

### Passo 3: Configurar MinIO

#### 3.1 Criar Buckets

1. Acesse o MinIO Console (http://localhost:9001)
2. Faça login com `minioadmin` / `minioadmin`
3. Vá em **Buckets** → **Create Bucket**
4. Crie dois buckets:
   - `datalake` (para dados raw/processados)
   - `warehouse` (para tabelas Iceberg)

#### 3.2 Gerar Credenciais de Acesso

Execute os seguintes comandos no terminal:

```bash
# Passo 1: Instalar mc (Linux)
curl https://dl.min.io/client/mc/release/linux-amd64/mc \
  --create-dirs -o ~/mc
chmod +x ~/mc
export PATH=$PATH:~/

# Passo 2: Configurar alias
bash +o history
mc alias set myminio http://localhost:9000 minioadmin minioadmin
bash -o history
mc admin info myminio

# Passo 3: Criar service account
mc admin user svcacct add myminio minioadmin --name acesso_temp --expiry 2025-12-31
```

**⚠️ IMPORTANTE**: Salve o `Access Key` e `Secret Key` gerados - você precisará deles no próximo passo!

### Passo 4: Configurar Sources no Dremio

#### 4.1 Acessar Dremio

1. Acesse http://localhost:9047
2. Na primeira vez, crie uma conta de administrador
3. Vá em **Settings** → **Sources** → **Add Source**

#### 4.2 Configurar Source S3 (Datalake)

1. **Selecione**: Amazon S3
2. **Configurações**:
   - **Name**: `datalake`
   - **AWS Access Key**: [Access Key gerado no MinIO]
   - **AWS Secret Key**: [Secret Key gerado no MinIO]
   - **Desmarque**: ✗ Encrypt connection
   - **Desmarque**: ✗ Enable asynchronous access when possible

3. **Connection Properties** (clique em "Add Property"):
   ```
   fs.s3a.path.style.access = true
   fs.s3a.endpoint = minioserver:9000
   dremio.s3.compat = true
   ```

4. **Advanced Options**:
   - **Allowlisted Buckets**: `datalake`
   - **Desmarque**: ✗ Enable local caching when possible
   - **Marque**: ✓ Automatically format files into physical datasets when users issue queries

5. **Clique em**: Save

#### 4.3 Configurar Source Nessie (Iceberg)

1. **Selecione**: Nessie
2. **Configurações**:
   - **Name**: `Iceberg`
   - **Nessie Endpoint**: `http://nessie:19120/api/v2`
   - **Authentication**: None

3. **Storage Settings**:
   - **AWS Root Path**: `warehouse`
   - **AWS Access Key**: [Access Key gerado no MinIO]
   - **AWS Secret Key**: [Secret Key gerado no MinIO]
   - **Desmarque**: ✗ Encrypt connection

4. **Connection Properties** (clique em "Add Property"):
   ```
   fs.s3a.path.style.access = true
   fs.s3a.endpoint = minioserver:9000
   dremio.s3.compat = true
   ```

5. **Advanced Options**:
   - **Desmarque**: ✗ Enable asynchronous access when possible
   - **Desmarque**: ✗ Enable local caching when possible

6. **Clique em**: Save

### Passo 5: Verificar Configuração

1. **No Dremio**, vá para a aba **Datasets**
2. Você deve ver:
   - **datalake** (source S3)
   - **Iceberg** (source Nessie)

3. **Teste a conexão**:
   ```sql
   -- No SQL Runner do Dremio
   SHOW SCHEMAS IN Iceberg;
   ```

## 🔧 Verificação e Testes

### Teste 1: Upload de Arquivo no MinIO

1. No MinIO Console, vá no bucket `datalake`
2. Faça upload de um arquivo CSV de teste
3. No Dremio, navegue até `datalake` → [seu arquivo]
4. Execute: `SELECT * FROM datalake."seu_arquivo.csv" LIMIT 10`

### Teste 2: Criar Tabela Iceberg

```sql
-- No SQL Runner do Dremio
CREATE TABLE Iceberg.test_schema.sample_table (
    id INT,
    name VARCHAR,
    created_at TIMESTAMP
);

INSERT INTO Iceberg.test_schema.sample_table 
VALUES (1, 'Test', CURRENT_TIMESTAMP);

SELECT * FROM Iceberg.test_schema.sample_table;
```

## ❓ FAQ - Problemas Comuns

### Q1: Erro "Connection refused" no Dremio
**A**: Verifique se todos os containers estão rodando:
```bash
docker-compose ps
docker-compose logs dremio
```

### Q2: MinIO não aceita credenciais
**A**: Verifique se está usando `minioadmin` / `minioadmin` e se o container está rodando na porta 9001.

### Q3: Erro "Endpoint not found" no Nessie
**A**: Certifique-se de usar `http://nessie:19120/api/v2` (não localhost) pois é a comunicação interna entre containers.

### Q4: Source S3 não conecta
**A**: Verifique:
- Access Key e Secret Key estão corretos
- Connection Properties estão configuradas
- Bucket `datalake` existe no MinIO

### Q5: Erro "fs.s3a.endpoint" não reconhecido
**A**: Certifique-se de adicionar todas as Connection Properties:
```
fs.s3a.path.style.access = true
fs.s3a.endpoint = minioserver:9000
dremio.s3.compat = true
```

### Q6: Tabelas Iceberg não aparecem
**A**: Verifique:
- Source Nessie está configurado corretamente
- Bucket `warehouse` existe no MinIO
- Endpoint Nessie está acessível: http://localhost:19120/api/v2

### Q7: Performance lenta
**A**: Para ambiente de desenvolvimento:
- Aumente memória do Docker (mínimo 8GB)
- Desabilite caching desnecessário
- Use SSD se possível

### Q8: Erro de permissão no Dremio
**A**: O docker-compose usa `user: "0:0"` para evitar problemas de permissão. Se ainda houver problemas:
```bash
sudo chown -R 999:999 ./dremio_data
sudo chown -R 999:999 ./dremio_conf
```

### Q9: Como resetar tudo?
**A**: Para limpar e recomeçar:
```bash
docker-compose down -v
sudo rm -rf dremio_data dremio_conf minio_data nessie_data
docker-compose up -d
```

### Q10: Como verificar logs?
**A**: Para debugar problemas:
```bash
# Logs de todos os serviços
docker-compose logs

# Logs específicos
docker-compose logs dremio
docker-compose logs minioserver
docker-compose logs nessie
```

## 🎉 Próximos Passos

Após completar este tutorial, você terá:

✅ Ambiente de data lakehouse funcionando  
✅ MinIO configurado com buckets  
✅ Dremio conectado ao MinIO e Nessie  
✅ Capacidade de criar tabelas Iceberg  
✅ Interface SQL para consultas  

**Agora você pode**:
- Executar o pipeline Python para processar CSVs
- Criar tabelas Iceberg com versionamento
- Fazer queries SQL complexas
- Implementar time travel e branching de dados

---

**📝 Nota**: Este tutorial configura um ambiente de desenvolvimento. Para produção, considere:
- Configurações de segurança adicionais
- Backup e recuperação
- Monitoramento e alertas
- Escalabilidade horizontal