# API de Produtos Complementares - Olist E-commerce

## 🎯 Visão Geral

Esta API implementa um sistema de recomendações de **produtos complementares** ("Comprados Juntos") usando algoritmos de coocorrência (Lift e NPMI) para identificar produtos que são frequentemente comprados juntos, baseado no histórico de pedidos da Olist.

### Componentes Principais

1. **Camada de Lote (Batch Processing)**

   - Processamento offline de dados históricos (6-12 meses)
   - Cálculo de coocorrência, Lift e NPMI
   - Execução noturna via Airflow/Cron

2. **Armazenamento**

   - **PostgreSQL**: Candidatos complementares, logs de atribuição
   - **Redis**: Cache de recomendações (TTL 1h)
   - **Elasticsearch**: Catálogo de produtos com filtros em tempo real

3. **API de Serviço**
   - Busca rápida com cache Redis
   - Filtros rígidos (estoque, categoria, preço)
   - Rerank inteligente (margem, diversificação)
   - Logging para medição A/B

## 🚀 Início Rápido

### 1. Instalação

```bash
git clone [repository]
cd api-recomendacao-e-commerce
pip install -r requirements.txt
```

### 2. Env

### 3. Dados

Baixe os dados da Olist do Kaggle e coloque na pasta `ds/`:

- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_products_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_order_reviews_dataset.csv`

### 4. Inicialização

```bash
# Executar configuração inicial
python init_system.py

# OU iniciar a API diretamente (modo desenvolvimento)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Documentação da API

### Endpoints Principais

#### 1. Produtos Complementares

```http
GET /recommendations/complementary/{product_id}
```

**Parâmetros:**

- `product_id` (path): ID do produto base
- `context_type` (query): `PDP` ou `CART`
- `user_id` (query, opcional): ID do usuário
- `limit` (query): Número máximo de produtos (1-50)
- `min_stock` (query): Estoque mínimo necessário
- `category` (query): Filtrar por categoria
- `min_price`, `max_price` (query): Faixa de preço
- `min_rating` (query): Avaliação mínima

**Headers:**

- `X-Session-ID`: ID da sessão (para tracking)

**Exemplo de Resposta:**

```json
{
  "product_id": "abc123",
  "context_type": "PDP",
  "session_id": "sess_789",
  "rec_set_id": 12345,
  "recommendations": [
    {
      "product_id": "def456",
      "product_name": "Produto Complementar",
      "category": "eletrônicos",
      "price": 89.9,
      "in_stock": true,
      "lift_score": 2.34,
      "npmi_score": 0.67,
      "cooccurrence_count": 234,
      "recommendation_reason": "Frequentemente comprados juntos (234+ pedidos)"
    }
  ],
  "total": 1,
  "source": "complementary_algorithm"
}
```

#### 2. Log de Conversão

```http
POST /recommendations/outcome/{rec_set_id}
```

**Parâmetros:**

- `rec_set_id` (path): ID do conjunto de recomendações
- `product_id` (query): ID do produto
- `outcome_type` (query): `view`, `add_to_cart`, ou `purchase`
- `outcome_value` (query, opcional): Valor da compra

#### 3. Analytics

```http
GET /recommendations/analytics?days_back=30
```

Retorna métricas de performance das recomendações.

#### 4. Health Check

```http
GET /recommendations/health
```

Verifica status dos serviços (Redis, PostgreSQL, Elasticsearch).

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Modo de desenvolvimento
DEVELOPMENT_MODE=true

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=olist_recommendations
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_CACHE_TTL=3600

# Elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# Algoritmo
BATCH_PROCESSING_MONTHS=12
BATCH_MIN_COOCCURRENCE=5
RECOMMENDATION_DEFAULT_LIMIT=10
```

## 🔄 Processamento Batch

### Execução Manual

```bash
python batch_processor.py
```

### Agendamento (Cron)

```bash
# Executar diariamente às 2h da manhã
0 2 * * * cd /path/to/api && python -c "import asyncio; from batch_processor import BatchProcessor; asyncio.run(BatchProcessor().run_daily_update())"
```

### O que o Batch Faz

1. **Carrega dados** dos últimos 12 meses
2. **Calcula coocorrência** entre produtos
3. **Computa Lift e NPMI** para cada par
4. **Filtra candidatos** com scores mínimos
5. **Armazena no PostgreSQL** (top 50 por produto)
6. **Indexa no Elasticsearch** com catálogo atualizado

## 📊 Métricas e Algoritmos

### Lift Score

```
Lift = P(A,B) / (P(A) × P(B))
```

- **> 1.0**: Produtos têm associação positiva
- **= 1.0**: Independentes
- **< 1.0**: Associação negativa

### NPMI (Normalized Pointwise Mutual Information)

```
NPMI = PMI / -log(P(A,B))
onde PMI = log(P(A,B) / (P(A) × P(B)))
```

- **Faixa**: -1 a +1
- **> 0**: Associação positiva
- **= 0**: Independentes
- **< 0**: Associação negativa

### Rerank

O sistema reordena produtos baseado em:

- **Margem de lucro** (+30% peso)
- **Diversificação de categoria** (-20% penalidade para repetição)
- **Avaliação dos clientes** (+10% para produtos bem avaliados)
- **Contexto** (PDP vs Carrinho)

## 🔍 Monitoramento

### Logs

```bash
# Logs da aplicação
tail -f logs/complementary_api.log

# Logs do batch processing
tail -f logs/batch_processing.log
```

### Métricas de Negócio

- **Taxa de Interação**: Cliques em recomendações
- **Taxa de Adição ao Carrinho**: Produtos adicionados
- **Taxa de Conversão**: Compras realizadas
- **Valor Médio**: Ticket médio das conversões

### Dashboards

Métricas disponíveis via endpoint `/recommendations/analytics`:

- Performance por contexto (PDP vs Carrinho)
- Top produtos recomendados
- Taxas de conversão temporais
- Eficácia por categoria

## ⚙️ Migração de V1 para V2

### Endpoints Mantidos (Compatibilidade)

Os seguintes endpoints legados continuam funcionando:

- `GET /recommendations/user/{user_id}`
- `GET /recommendations/popular`
- `GET /recommendations/related/{product_id}`

**Recomendação**: Migre para `/recommendations/complementary/{product_id}` para melhor performance e recursos.

### Diferenças Principais

| Aspecto         | V1 (Legado)             | V2 (Complementar)        |
| --------------- | ----------------------- | ------------------------ |
| **Algoritmo**   | Collaborative Filtering | Coocorrência (Lift/NPMI) |
| **Cache**       | Simples                 | Redis estruturado        |
| **Filtros**     | Básicos                 | Elasticsearch avançado   |
| **Logs**        | Mínimos                 | Tracking completo        |
| **Performance** | ~500ms                  | ~50ms (com cache)        |
