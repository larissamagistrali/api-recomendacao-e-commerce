import os

OP_CONN = {
    "host": os.getenv("OP_DB_HOST", "op-db"),
    "port": int(os.getenv("OP_DB_PORT", 5432)),
    "dbname": os.getenv("OP_DB_NAME", "opdb"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
ELASTIC_URL = os.getenv("ELASTIC_URL", "http://es:9200")
