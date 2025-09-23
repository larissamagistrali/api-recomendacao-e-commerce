"""
Configuração e inicialização dos serviços da aplicação
"""
import sys
import os

# Garantir que todos os módulos possam ser importados
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importar módulos diretamente
from db_service import DatabaseService
from config import config
from services.auth_service import AuthService
from services.recommendation_service import RecommendationService
from services.analytics_service import AnalyticsService

# Instâncias globais dos serviços (singleton pattern)
print("[APP_SETUP] Inicializando serviços...")
print(f"[APP_SETUP] Modo de desenvolvimento: {config.DEVELOPMENT_MODE}")

# Criar instância do banco de dados
try:
    db_service = DatabaseService()
    print("[APP_SETUP] DatabaseService criado com sucesso")
except Exception as e:
    print(f"[APP_SETUP] ERRO ao criar DatabaseService: {e}")
    raise

# Criar serviços
try:
    auth_service = AuthService()
    print("[APP_SETUP] AuthService criado com sucesso")
    
    recommendation_service = RecommendationService(db_service)
    print("[APP_SETUP] RecommendationService criado com sucesso")
    
    analytics_service = AnalyticsService(db_service)
    print("[APP_SETUP] AnalyticsService criado com sucesso")
    
except Exception as e:
    print(f"[APP_SETUP] ERRO ao criar serviços: {e}")
    raise

print("[APP_SETUP] Todos os serviços inicializados com sucesso")

# Exportar para uso em outros módulos
__all__ = ['auth_service', 'recommendation_service', 'analytics_service', 'db_service']