import json
import hashlib
from typing import Any, Optional, Callable
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

# Cache em memória simples (em produção usar Redis)
_cache = {}
_cache_ttl = {}

def setup_cache():
    """Inicializa o sistema de cache"""
    logger.info("Sistema de cache inicializado")

def get_cache_key(func_name: str, *args, **kwargs) -> str:
    """Gera chave única para cache"""
    key_data = {
        'function': func_name,
        'args': args,
        'kwargs': kwargs
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()

def cache_response(ttl: int = 3600):
    """Decorator para cache de respostas"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave do cache
            cache_key = get_cache_key(func.__name__, *args, **kwargs)
            
            # Verificar se existe no cache e não expirou
            if cache_key in _cache:
                cached_time = _cache_ttl.get(cache_key, 0)
                if time.time() - cached_time < ttl:
                    logger.debug(f"Cache hit para {func.__name__}")
                    return _cache[cache_key]
                else:
                    # Remover entrada expirada
                    del _cache[cache_key]
                    del _cache_ttl[cache_key]
            
            # Executar função e cachear resultado
            result = await func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_ttl[cache_key] = time.time()
            
            logger.debug(f"Cache miss para {func.__name__} - resultado cacheado")
            return result
        
        return wrapper
    return decorator

def clear_cache():
    """Limpa todo o cache"""
    global _cache, _cache_ttl
    _cache.clear()
    _cache_ttl.clear()
    logger.info("Cache limpo")

def get_cache_stats() -> dict:
    """Retorna estatísticas do cache"""
    current_time = time.time()
    active_entries = sum(1 for cached_time in _cache_ttl.values() 
                        if current_time - cached_time < 3600)
    
    return {
        "total_entries": len(_cache),
        "active_entries": active_entries,
        "expired_entries": len(_cache) - active_entries,
        "memory_usage_mb": len(str(_cache)) / (1024 * 1024)
    }

def invalidate_cache_pattern(pattern: str):
    """Invalida entradas de cache que correspondem a um padrão"""
    keys_to_remove = [key for key in _cache.keys() if pattern in key]
    for key in keys_to_remove:
        del _cache[key]
        if key in _cache_ttl:
            del _cache_ttl[key]
    
    logger.info(f"Invalidadas {len(keys_to_remove)} entradas de cache com padrão '{pattern}'")