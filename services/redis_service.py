import redis
import json
import pickle
from typing import List, Dict, Any, Optional, Union
from config import Config

class RedisService:
    """Serviço Redis para cache de recomendações"""
    
    def __init__(self):
        try:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                password=Config.REDIS_PASSWORD,
                db=Config.REDIS_DB,
                decode_responses=False,  # Para permitir pickle
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Testar conexão
            self.redis_client.ping()
            print(f"[REDIS] Conectado ao Redis em {Config.REDIS_HOST}:{Config.REDIS_PORT}")
        except Exception as e:
            print(f"[REDIS] AVISO: Não foi possível conectar ao Redis: {e}")
            print("[REDIS] Cache desabilitado - usando fallback em memória")
            self.redis_client = None
            self._memory_cache = {}
        
    def _generate_cache_key(self, prefix: str, identifier: str, **kwargs) -> str:
        """Gera uma chave de cache consistente"""
        key_parts = [prefix, identifier]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)
        
    def set_complementary_products(
        self, 
        product_id: str, 
        products: List[Dict[str, Any]], 
        ttl: int = None
    ):
        """Armazena produtos complementares no cache"""
        key = self._generate_cache_key("complementary", product_id)
        ttl = ttl or Config.REDIS_CACHE_TTL
        
        if not self.redis_client:
            # Fallback para cache em memória
            self._memory_cache[key] = products
            return
        
        try:
            # Serializar com pickle para preservar tipos de dados
            serialized_data = pickle.dumps(products)
            self.redis_client.setex(key, ttl, serialized_data)
        except Exception as e:
            print(f"[REDIS] Erro ao armazenar produtos complementares: {e}")
            # Fallback para cache em memória
            self._memory_cache[key] = products
            
    def get_complementary_products(self, product_id: str) -> Optional[List[Dict[str, Any]]]:
        """Busca produtos complementares do cache"""
        key = self._generate_cache_key("complementary", product_id)
        
        if not self.redis_client:
            # Fallback para cache em memória
            return self._memory_cache.get(key)
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
        except Exception as e:
            print(f"[REDIS] Erro ao buscar produtos complementares: {e}")
            # Tentar fallback em memória
            return self._memory_cache.get(key)
            
        return None
        
    def set_user_recommendations(
        self, 
        user_id: str, 
        recommendations: List[Dict[str, Any]], 
        strategy: str = "default",
        ttl: int = None
    ):
        """Armazena recomendações de usuário no cache"""
        key = self._generate_cache_key("user_rec", user_id, strategy=strategy)
        ttl = ttl or Config.REDIS_CACHE_TTL
        
        try:
            serialized_data = pickle.dumps(recommendations)
            self.redis_client.setex(key, ttl, serialized_data)
        except Exception as e:
            print(f"[REDIS] Erro ao armazenar recomendações de usuário: {e}")
            
    def get_user_recommendations(
        self, 
        user_id: str, 
        strategy: str = "default"
    ) -> Optional[List[Dict[str, Any]]]:
        """Busca recomendações de usuário do cache"""
        key = self._generate_cache_key("user_rec", user_id, strategy=strategy)
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
        except Exception as e:
            print(f"[REDIS] Erro ao buscar recomendações de usuário: {e}")
            
        return None
        
    def set_popular_products(
        self, 
        products: List[Dict[str, Any]], 
        category: str = "all",
        ttl: int = None
    ):
        """Armazena produtos populares no cache"""
        key = self._generate_cache_key("popular", category)
        ttl = ttl or Config.REDIS_CACHE_TTL * 2  # Cache mais longo para produtos populares
        
        try:
            serialized_data = pickle.dumps(products)
            self.redis_client.setex(key, ttl, serialized_data)
        except Exception as e:
            print(f"[REDIS] Erro ao armazenar produtos populares: {e}")
            
    def get_popular_products(self, category: str = "all") -> Optional[List[Dict[str, Any]]]:
        """Busca produtos populares do cache"""
        key = self._generate_cache_key("popular", category)
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
        except Exception as e:
            print(f"[REDIS] Erro ao buscar produtos populares: {e}")
            
        return None
        
    def invalidate_product_cache(self, product_id: str):
        """Invalida todo o cache relacionado a um produto específico"""
        try:
            # Buscar todas as chaves relacionadas ao produto
            patterns = [
                f"complementary:{product_id}:*",
                f"*:{product_id}:*",  # Para casos onde product_id está no meio
            ]
            
            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    
        except Exception as e:
            print(f"[REDIS] Erro ao invalidar cache do produto {product_id}: {e}")
            
    def invalidate_user_cache(self, user_id: str):
        """Invalida todo o cache relacionado a um usuário específico"""
        try:
            pattern = f"user_rec:{user_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            print(f"[REDIS] Erro ao invalidar cache do usuário {user_id}: {e}")
            
    def clear_all_cache(self):
        """Limpa todo o cache (usar com cuidado!)"""
        try:
            self.redis_client.flushdb()
        except Exception as e:
            print(f"[REDIS] Erro ao limpar todo o cache: {e}")
            
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        try:
            info = self.redis_client.info()
            
            # Contar chaves por tipo
            key_counts = {}
            for key_type in ["complementary", "user_rec", "popular"]:
                pattern = f"{key_type}:*"
                keys = self.redis_client.keys(pattern)
                key_counts[key_type] = len(keys)
                
            return {
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_keys": info.get("db0", {}).get("keys", 0),
                "key_counts": key_counts,
                "hit_rate": self._calculate_hit_rate()
            }
        except Exception as e:
            print(f"[REDIS] Erro ao obter estatísticas: {e}")
            return {}
            
    def _calculate_hit_rate(self) -> float:
        """Calcula a taxa de acerto do cache"""
        try:
            info = self.redis_client.info()
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            total = hits + misses
            
            if total > 0:
                return hits / total
            return 0.0
        except:
            return 0.0
            
    def ping(self) -> bool:
        """Testa a conexão com o Redis"""
        if not self.redis_client:
            return False
            
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False