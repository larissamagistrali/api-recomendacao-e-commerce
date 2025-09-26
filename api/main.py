from fastapi import FastAPI
from sqlalchemy import create_engine, text
import pandas as pd
import redis
from elasticsearch import Elasticsearch
from api.config import OP_CONN, REDIS_URL, ELASTIC_URL

app = FastAPI(title="API de Recomendação (PoC)")

engine = create_engine(
    f"postgresql+psycopg2://{OP_CONN['user']}:{OP_CONN['password']}@{OP_CONN['host']}:{OP_CONN['port']}/{OP_CONN['dbname']}"
)

r = redis.from_url(REDIS_URL)
es = Elasticsearch(ELASTIC_URL)

@app.get("/health")
def health():
    with engine.connect() as con:
        con.execute(text("SELECT 1"))
    return {"ok": True}

def get_recommendations(product_id, n=5):
    query = f"SELECT * FROM item_similarity WHERE product_id_1 = '{product_id}' OR product_id_2 = '{product_id}' ORDER BY similarity DESC LIMIT {n}"
    df = pd.read_sql_query(query, engine)
    if df.empty:
        return []
    recommendations = []
    for _, row in df.iterrows():
        if row['product_id_1'] == product_id:
            recommendations.append(row['product_id_2'])
        elif row['product_id_2'] == product_id:
            recommendations.append(row['product_id_1'])
    return recommendations


@app.get("/recommend/similar/{product_id}")
def recommend_similar(product_id: str, limit: int = 5):
    recs = get_recommendations(product_id, n=limit)
    return {"product_id": product_id, "recommendations": recs}
