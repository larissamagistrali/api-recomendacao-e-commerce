import sys
import os

# Adicionar o diretório pai ao sys.path para permitir imports absolutos
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Agora podemos importar usando caminhos absolutos
from services.auth_service import AuthService
from services.recommendation_service import RecommendationService
from services.analytics_service import AnalyticsService
from db_service import DatabaseService
from config import config

# Instâncias globais dos serviços (singleton pattern)
print(f"[SERVICES] __init__ - Inicializando serviços...")
print(f"[SERVICES] __init__ - Modo de desenvolvimento: {config.DEVELOPMENT_MODE}")

# Criar instância do banco de dados
db_service = DatabaseService()

# Criar serviços
auth_service = AuthService()
recommendation_service = RecommendationService(db_service)
analytics_service = AnalyticsService(db_service)

print(f"[SERVICES] __init__ - Serviços inicializados com sucesso")

__all__ = ['auth_service', 'recommendation_service', 'analytics_service', 'db_service']