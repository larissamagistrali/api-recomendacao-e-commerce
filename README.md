# PoC Recomendação On-Prem

Stack Docker com Postgres (OLTP e Operacional), Redis, Elasticsearch, Airflow e API FastAPI.

## Requisitos

- Docker + Docker Compose
- 4 GB RAM livres (Elasticsearch recomenda 2+ GB)

## Configuração

1. Crie um arquivo `.env` na raiz do projeto (ajuste conforme necessário):

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
OLTP_DB=oltpdb
OP_DB=opdb
ES_JAVA_OPTS=-Xms512m -Xmx512m
AIRFLOW_UID=50000
API_PORT=8000
```

- Linux: use seu UID local para evitar problemas de permissão no Airflow:
  - `echo "AIRFLOW_UID=$(id -u)" >> .env`
- macOS/Windows: manter `AIRFLOW_UID=50000` costuma funcionar.

## Subir a stack

```
docker compose up -d --build
```

Serviços e portas padrão:

- API: http://localhost:8000
- Airflow: http://localhost:8081 (admin/admin)
- Elasticsearch: http://localhost:9200
- Postgres OLTP: localhost:5433
- Postgres Operacional: localhost:5434
- Redis: localhost:6379

Se alguma porta estiver em uso, ajuste `docker-compose.yml` ou variáveis no `.env`.

## Fluxo de dados

- `init/oltp.sql` carrega eventos de exemplo em `oltp-db`.
- A DAG `recom_batch` (Airflow) lê os eventos via DuckDB, computa scores, grava em `op-db.public.item_scores` e indexa no Elasticsearch (`item_scores`).

## Operações comuns

- Verificar saúde da API:

```
curl -s http://localhost:8000/health
```

- Recomendações de produtos similares:

```
curl -s "http://localhost:8000/recommend/similar/{product_id}?limit=5"
```

Substitua `{product_id}` pelo ID do produto desejado.

- Airflow UI: `http://localhost:8081` (user: admin, pass: admin)
- Ver a senha gerada automaticamente pelo `airflow standalone` (dentro do contêiner):

```
docker compose exec airflow bash -lc "cat $AIRFLOW_HOME/standalone_admin_password.txt"
```

- Acionar manualmente a DAG pelo CLI (opcional):

```
docker compose exec airflow bash -lc "airflow dags trigger recom_batch"
```

## Estrutura dos diretórios

```
api/
  Dockerfile
  main.py
  requirements.txt
airflow/
  dags/
    recom_batch.py
  requirements.txt
  __pycache__/
init/
  oltp.sql
  op.sql
data/
  olist_customers_dataset.csv
  olist_geolocation_dataset.csv
  olist_order_items_dataset.csv
  olist_order_payments_dataset.csv
  olist_order_reviews_dataset.csv
  olist_orders_dataset.csv
  olist_products_dataset.csv
  olist_sellers_dataset.csv
```

## macOS (Apple Silicon)

- As imagens são multi-arch. Se o Elasticsearch reclamar de arquitetura, adicione em `docker-compose.yml` no serviço `elasticsearch`:

```
platform: linux/arm64/v8
```

- Ajuste de memória no Docker Desktop pode ser necessário (4+ GB).

## Troubleshooting

- Airflow não sobe: verifique `AIRFLOW_UID` e rode init dentro do contêiner se necessário:

```
docker compose exec airflow bash -lc "airflow db init && airflow users create --username admin --firstname a --lastname b --role Admin --email admin@example.com --password admin || true && airflow webserver -D && airflow scheduler -D"
```

- Elasticsearch sem saúde: aguarde alguns segundos, verifique memória e logs: `docker compose logs elasticsearch`.
- Conflito de portas: altere mapeamentos em `docker-compose.yml`.

## Licença

Uso interno/PoC.
