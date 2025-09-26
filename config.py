import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Configurações do banco de dados"""
    server: str = "localhost"
    database: str = "OlistRecommendations" 
    username: str = None
    password: str = None
    trusted_connection: bool = True
    data_path: str = "ds/"

# Configuração padrão
DEFAULT_DB_CONFIG = DatabaseConfig(
    server=os.getenv("SQL_SERVER", "localhost"),
    database=os.getenv("SQL_DATABASE", "OlistRecommendations"),
    username=os.getenv("SQL_USERNAME"),
    password=os.getenv("SQL_PASSWORD"),
    trusted_connection=os.getenv("SQL_TRUSTED_CONNECTION", "True").lower() == "true",
    data_path=os.getenv("DATA_PATH", "ds/")
)

class Config:
    """Configurações da aplicação"""
    
    # Modo de desenvolvimento (usa CSV em vez de bancos externos)
    DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "true").lower() == "true"
    
    # Configurações PostgreSQL
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "olist_recommendations")
    POSTGRES_USERNAME = os.getenv("POSTGRES_USERNAME", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    
    # Configurações Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))  # 1 hora
    
    # Configurações Elasticsearch
    ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
    ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
    ELASTICSEARCH_USERNAME = os.getenv("ELASTICSEARCH_USERNAME", None)
    ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD", None)
    ELASTICSEARCH_USE_SSL = os.getenv("ELASTICSEARCH_USE_SSL", "false").lower() == "true"
    ELASTICSEARCH_INDEX_PRODUCTS = "products"
    
    # Configurações do banco de dados (para compatibilidade com código legado)
    DB_SERVER = os.getenv("DB_SERVER", "localhost")
    DB_DATABASE = os.getenv("DB_DATABASE", "olist_db")
    DB_USERNAME = os.getenv("DB_USERNAME", "sa")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "YourPassword123!")
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    
    # Configurações JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Configurações da API
    API_TITLE = "Olist Complementary Products API"
    API_VERSION = "2.0.0"
    API_DESCRIPTION = "API de produtos complementares e recomendações para e-commerce Olist"
    
    # Configurações de cache
    CACHE_TTL = 3600  # 1 hora
    
    # Configurações do sistema de recomendação
    RECOMMENDATION_DEFAULT_LIMIT = 10
    RECOMMENDATION_MAX_LIMIT = 50
    COMPLEMENTARY_PRODUCTS_LIMIT = 50
    
    # Configurações de processamento batch
    BATCH_PROCESSING_MONTHS = 12  # Últimos 12 meses de dados
    BATCH_MIN_COOCCURRENCE = 5    # Mínimo de coocorrências para considerar
    
    # Configurações de rerank
    RERANK_MARGIN_WEIGHT = 0.3    # Peso da margem de lucro no rerank
    RERANK_DIVERSITY_PENALTY = 0.2 # Penalidade por falta de diversidade
    
    @property
    def database_url(self):
        """Retorna a URL de conexão do banco de dados"""
        if self.DEVELOPMENT_MODE:
            return "sqlite:///:memory:"  # SQLite em memória para desenvolvimento
        else:
            return f"mssql+pyodbc://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_SERVER}/{self.DB_DATABASE}?driver={self.DB_DRIVER}"

# Instância global da configuração
config = Config()