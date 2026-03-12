# 🛍️ Sistema de Recomendação para E-Commerce

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![Airflow](https://img.shields.io/badge/Airflow-2.9.2-orange.svg)](https://airflow.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)

Sistema de recomendação pronto para produção utilizando filtragem colaborativa e APIs em tempo real. Construído com stack moderna incluindo FastAPI, Apache Airflow, PostgreSQL, Redis e Elasticsearch.

---

## 📑 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Tecnologias](#-tecnologias)
- [Primeiros Passos](#-primeiros-passos)
- [Documentação da API](#-documentação-da-api)
- [Pipeline de Dados](#-pipeline-de-dados)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Configuração](#-configuração)
- [Monitoramento](#-monitoramento)
- [Solução de Problemas](#-solução-de-problemas)
- [Contato](#-contato)

---

## 🎯 Visão Geral

Este projeto implementa um motor de recomendação escalável projetado para plataformas de e-commerce. Utilizando o **dataset Olist Brazilian E-Commerce**, demonstra um pipeline completo de dados desde a ingestão até o fornecimento de recomendações de produtos em tempo real via REST API.

### Destaques Principais

- **Filtragem Colaborativa Baseada em Itens**: Calcula similaridade entre produtos usando cosseno de similaridade em matrizes usuário-item
- **Processamento em Lote**: Recálculo diário de recomendações usando Apache Airflow
- **API em Tempo Real**: Fornecimento rápido de recomendações com FastAPI
- **Arquitetura Dual Database**: Bancos de dados OLTP e operacional separados para desempenho otimizado
- **Pronto para Produção**: Stack Docker completa com health checks, monitoramento e tratamento de erros

---

## ✨ Funcionalidades

- 🔄 **Pipeline de Dados Automatizado**: DAG do Airflow orquestra ingestão de CSVs e cálculo de similaridade
- ⚡ **Respostas Rápidas da API**: Cache Redis e consultas otimizadas ao banco de dados
- 🔍 **Integração com Elasticsearch**: Capacidades de busca full-text para produtos
- 📊 **Arquitetura Escalável**: Lida com grandes catálogos de produtos com otimização de matriz esparsa
- 🐳 **Stack Docker Compose**: Deploy de toda infraestrutura com um comando
- 📈 **Pronto para Monitoramento**: Health checks e UI do Airflow para monitoramento de pipeline
- 🔐 **Configuração por Ambiente**: Gerenciamento seguro de credenciais via arquivos `.env`

---

## 🏗️ Arquitetura

```
┌─────────────┐
│  Dados CSV  │
│   (Olist)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│           Apache Airflow (DAG)              │
│  ┌────────────────┐    ┌─────────────────┐ │
│  │  Ingest CSVs   │───▶│   Calculate     │ │
│  │  to Postgres   │    │   Similarity    │ │
│  └────────────────┘    └─────────────────┘ │
└──────────────┬──────────────────────────────┘
               │
               ▼
    ┌──────────────────┐
    │  PostgreSQL (OP) │
    │  item_similarity │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐      ┌──────────────┐
    │   FastAPI (API)  │◀────▶│    Redis     │
    │  /recommend/*    │      │   (Cache)    │
    └──────────────────┘      └──────────────┘
             │
             ▼
    ┌──────────────────┐
    │  Elasticsearch   │
    │  (Busca/Índice)  │
    └──────────────────┘
```

### Fluxo de Dados

1. **Ingestão**: Airflow lê arquivos CSV (clientes, pedidos, produtos) e carrega no PostgreSQL
2. **Processamento**: Constrói matriz usuário-item de compras e calcula similaridade item-item usando distância de cosseno
3. **Armazenamento**: Armazena scores de similaridade no banco operacional
4. **Disponibilização**: FastAPI consulta similaridades pré-computadas e retorna recomendações em tempo real
5. **Cache**: Redis faz cache de consultas frequentes para respostas em sub-milissegundos

---

## 🛠️ Tecnologias

| Componente          | Tecnologia              | Propósito                                       |
| ------------------- | ----------------------- | ----------------------------------------------- |
| **API**             | FastAPI                 | API REST para recomendações                     |
| **Orquestração**    | Apache Airflow 2.9.2    | Agendamento e monitoramento de jobs em lote     |
| **Bancos de Dados** | PostgreSQL 15 (x2)      | Armazenamento de dados OLTP e operacional       |
| **Cache**           | Redis 7                 | Cache de respostas da API                       |
| **Busca**           | Elasticsearch 8.14      | Busca e indexação de produtos                   |
| **Biblioteca ML**   | scikit-learn            | Cálculo de similaridade por cosseno             |
| **Proc. de Dados**  | Pandas, NumPy           | Transformação de dados e operações com matrizes |
| **Containerização** | Docker + Docker Compose | Orquestração de infraestrutura                  |

---

## 🚀 Primeiros Passos

### Pré-requisitos

- **Docker** 20.10+ & **Docker Compose** 2.0+
- **4 GB RAM** mínimo (Elasticsearch requer 2+ GB)
- **10 GB** de espaço em disco

### Instalação

1. **Clone o repositório**

   ```bash
   git clone https://github.com/larissamagistrali/api-recomendacao-e-commerce.git
   cd api-recomendacao-e-commerce
   ```

2. **Crie o arquivo de ambiente**

   ```bash
   cp .env.example .env
   ```

   Ou crie o `.env` manualmente:

   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   OLTP_DB=oltpdb
   OP_DB=opdb
   ES_JAVA_OPTS=-Xms512m -Xmx512m
   AIRFLOW_UID=50000
   API_PORT=8000
   ```

   **Usuários Linux**: Configure o UID correto para permissões do Airflow

   ```bash
   echo "AIRFLOW_UID=$(id -u)" >> .env
   ```

3. **Inicie a stack**

   ```bash
   docker compose up -d --build
   ```

4. **Aguarde os serviços ficarem saudáveis** (pode levar 2-3 minutos)

   ```bash
   docker compose ps
   ```

### Endpoints dos Serviços

| Serviço             | URL                        | Credenciais         |
| ------------------- | -------------------------- | ------------------- |
| **API**             | http://localhost:8000      | -                   |
| **Docs da API**     | http://localhost:8000/docs | -                   |
| **Airflow UI**      | http://localhost:8081      | admin / admin       |
| **Elasticsearch**   | http://localhost:9200      | -                   |
| **PostgreSQL OLTP** | localhost:5433             | postgres / postgres |
| **PostgreSQL OP**   | localhost:5434             | postgres / postgres |
| **Redis**           | localhost:6379             | -                   |

---

## 📚 Documentação da API

### Health Check

```bash
curl http://localhost:8000/health
```

**Resposta:**

```json
{
  "ok": true
}
```

### Obter Produtos Similares

```bash
curl "http://localhost:8000/recommend/similar/{product_id}?limit=5"
```

**Parâmetros:**

- `product_id` (path): ID do produto para encontrar itens similares
- `limit` (query, opcional): Número de recomendações (padrão: 5)

**Exemplo:**

```bash
curl "http://localhost:8000/recommend/similar/abc123?limit=10"
```

**Resposta:**

```json
{
  "product_id": "abc123",
  "recommendations": ["def456", "ghi789", "jkl012", "mno345", "pqr678"]
}
```

### Documentação Interativa

Visite **http://localhost:8000/docs** para acessar o Swagger UI com testes interativos da API.

---

## 🔄 Pipeline de Dados

### Airflow DAG: `recom_batch`

**Agendamento**: Diariamente à meia-noite**Tarefas**:

1. **ingest_csvs**: Carrega arquivos CSV de `/data` nas tabelas PostgreSQL
2. **create_item_similarity**: Calcula matriz de similaridade entre produtos

### Acionamento Manual

```bash
# Via Airflow UI
# Acesse http://localhost:8081 → DAGs → recom_batch → Trigger

# Via CLI
docker compose exec airflow bash -lc "airflow dags trigger recom_batch"
```

### Detalhes do Algoritmo

1. **Filtragem de Dados**: Seleciona top 1000 produtos com mínimo de 5 compras
2. **Construção da Matriz**: Constrói matriz esparsa usuário-item (clientes × produtos)
3. **Cálculo de Similaridade**: Calcula similaridade de cosseno entre vetores de produtos
4. **Filtragem por Threshold**: Armazena apenas similaridades ≥ 0.1 para reduzir armazenamento
5. **Persistência no Banco**: Grava na tabela `item_similarity`

---

## 📂 Estrutura do Projeto

```
.
├── api/                          # Aplicação FastAPI
│   ├── __init__.py
│   ├── config.py                 # Configurações de banco e serviços
│   ├── main.py                   # Endpoints da API
│   ├── requirements.txt          # Dependências Python
│   └── Dockerfile                # Build do container da API
├── airflow/                      # Orquestração Airflow
│   ├── dags/
│   │   └── recom_batch.py        # DAG do pipeline de recomendação
│   └── requirements.txt          # Dependências do Airflow
├── data/                         # Arquivos CSV do dataset Olist
│   ├── olist_customers_dataset.csv
│   ├── olist_orders_dataset.csv
│   ├── olist_order_items_dataset.csv
│   ├── olist_products_dataset.csv
│   └── ...
├── init/                         # Scripts de inicialização do banco
│   ├── oltp.sql                  # Schema do banco OLTP
│   └── op.sql                    # Schema do banco operacional
├── docker-compose.yml            # Orquestração da infraestrutura
├── Dockerfile                    # Container principal da aplicação
└── README.md                     # Este arquivo
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável            | Padrão            | Descrição                                     |
| ------------------- | ----------------- | --------------------------------------------- |
| `POSTGRES_USER`     | postgres          | Nome de usuário PostgreSQL                    |
| `POSTGRES_PASSWORD` | postgres          | Senha PostgreSQL                              |
| `OLTP_DB`           | oltpdb            | Nome do banco OLTP                            |
| `OP_DB`             | opdb              | Nome do banco operacional                     |
| `ES_JAVA_OPTS`      | -Xms512m -Xmx512m | Opções da JVM do Elasticsearch                |
| `AIRFLOW_UID`       | 50000             | ID do usuário Airflow (Linux: use `$(id -u)`) |
| `API_PORT`          | 8000              | Mapeamento de porta da API                    |

### Conflitos de Portas

Se as portas padrão estiverem em uso, modifique o `docker-compose.yml`:

```yaml
services:
  api:
    ports:
      - "8001:8000" # Usa porta 8001 ao invés de 8000
```

---

## 📊 Monitoramento

### Interface do Airflow

Acesse **http://localhost:8081** para monitorar:

- Histórico e status de execução das DAGs
- Logs e duração das tarefas
- Saúde do scheduler
- Performance dos workers

### Logs

```bash
# Logs da API
docker compose logs -f api

# Logs do Airflow
docker compose logs -f airflow

# Todos os serviços
docker compose logs -f
```

### Consultas ao Banco

```bash
# Conectar ao banco operacional
docker compose exec op-db psql -U postgres -d opdb

# Verificar tabela de similaridade
SELECT COUNT(*) FROM item_similarity;
SELECT * FROM item_similarity LIMIT 10;
```

---

## 🐛 Solução de Problemas

### Serviços não iniciam

```bash
# Verificar status dos serviços
docker compose ps

# Ver logs detalhados
docker compose logs [nome-do-servico]

# Reiniciar serviço específico
docker compose restart [nome-do-servico]
```

### Elasticsearch falha ao iniciar

**Problema**: Memória insuficiente
**Solução**: Aumente o limite de memória do Docker para 4+ GB nas configurações do Docker Desktop

### Erros de permissão no Airflow (Linux)

**Problema**: Permission denied em logs/dags
**Solução**: Configure o UID correto no `.env`

```bash
echo "AIRFLOW_UID=$(id -u)" >> .env
docker compose down
docker compose up -d
```

### Recomendações vazias

**Problema**: DAG ainda não foi executada
**Solução**: Acione a DAG manualmente ou aguarde a execução agendada

```bash
docker compose exec airflow bash -lc "airflow dags trigger recom_batch"
```

### Porta já em uso

**Solução**: Altere os mapeamentos de porta no `docker-compose.yml` ou pare serviços conflitantes

### macOS (Apple Silicon)

**Problema**: Incompatibilidade de arquitetura
**Solução**: Adicione no serviço `elasticsearch` do `docker-compose.yml`:

```yaml
platform: linux/arm64/v8
```
