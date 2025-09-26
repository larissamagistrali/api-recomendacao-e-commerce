import pandas as pd
from sqlalchemy import create_engine
import os

OP_CONN = {
    "host": os.getenv("OP_DB_HOST", "localhost"),
    "port": int(os.getenv("OP_DB_PORT", 5434)),
    "dbname": os.getenv("OP_DB_NAME", "opdb"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}

engine = create_engine(
    f"postgresql+psycopg2://{OP_CONN['user']}:{OP_CONN['password']}@{OP_CONN['host']}:{OP_CONN['port']}/{OP_CONN['dbname']}"
)
df = pd.read_sql_table("item_similarity", engine)
print( f"postgresql+psycopg2://{OP_CONN['user']}:{OP_CONN['password']}@{OP_CONN['host']}:{OP_CONN['port']}/{OP_CONN['dbname']}")
print(df.head())