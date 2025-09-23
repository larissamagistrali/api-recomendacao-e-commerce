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
    
    # Modo de desenvolvimento (usa CSV em vez de SQL Server)
    DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "true").lower() == "true"
    
    # Configurações do banco de dados (para produção)
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
    API_TITLE = "Olist Recommendation API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "API de recomendações para e-commerce Olist"
    
    # Configurações de cache
    CACHE_TTL = 3600  # 1 hora
    
    @property
    def database_url(self):
        """Retorna a URL de conexão do banco de dados"""
        if self.DEVELOPMENT_MODE:
            return "sqlite:///:memory:"  # SQLite em memória para desenvolvimento
        else:
            return f"mssql+pyodbc://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_SERVER}/{self.DB_DATABASE}?driver={self.DB_DRIVER}"

# Instância global da configuração
config = Config()