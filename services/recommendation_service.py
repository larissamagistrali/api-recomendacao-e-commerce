from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório pai ao path para importar db_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_service import DatabaseService
from models.collaborative import CollaborativeFilteringModel
from models.content_based import ContentBasedModel
from models.hybrid import HybridModel

class RecommendationService:
    """Serviço de recomendações"""
    
    def __init__(self, db_service: DatabaseService):
        print(f"[RECOMMENDATION_SERVICE] __init__ - Inicializando RecommendationService")
        self.db_service = db_service
        
        # Inicializar modelos de ML
        self.collaborative_model = CollaborativeFilteringModel()
        self.content_model = ContentBasedModel()
        self.hybrid_model = HybridModel()
        
        print(f"[RECOMMENDATION_SERVICE] __init__ - RecommendationService inicializado")
    
    async def get_user_recommendations(
        self, 
        user_id: str, 
        limit: int = 10, 
        strategy: str = "collaborative"
    ) -> List[Dict[str, Any]]:
        """Obter recomendações para um usuário"""
        print(f"[RECOMMENDATION_SERVICE] get_user_recommendations - User: {user_id}, Strategy: {strategy}, Limit: {limit}")
        
        try:
            if strategy == "collaborative":
                product_ids = await self._get_collaborative_recommendations(user_id, limit)
            elif strategy == "content":
                product_ids = await self._get_content_recommendations(user_id, limit)
            elif strategy == "hybrid":
                product_ids = await self._get_hybrid_recommendations(user_id, limit)
            else:
                print(f"[RECOMMENDATION_SERVICE] get_user_recommendations - Estratégia inválida: {strategy}")
                raise ValueError(f"Estratégia não suportada: {strategy}")
            
            # Buscar detalhes dos produtos
            recommendations = []
            for product_id in product_ids:
                product_details = self.db_service.get_product_details(product_id)
                if product_details:
                    recommendations.append({
                        "product_id": product_id,
                        "score": 0.8,  # Score fictício para desenvolvimento
                        "reason": f"Recomendado via {strategy}",
                        **product_details
                    })
            
            print(f"[RECOMMENDATION_SERVICE] get_user_recommendations - Retornando {len(recommendations)} recomendações")
            return recommendations
            
        except Exception as e:
            print(f"[RECOMMENDATION_SERVICE] get_user_recommendations - ERRO: {str(e)}")
            # Em caso de erro, retornar produtos populares como fallback
            popular_products = self.db_service.get_popular_products(limit)
            recommendations = []
            for product in popular_products:
                recommendations.append({
                    "product_id": product["product_id"],
                    "score": 0.5,
                    "reason": "Produto popular (fallback)",
                    **product
                })
            return recommendations
    
    async def get_popular_products(
        self, 
        limit: int = 10, 
        state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obter produtos populares"""
        print(f"[RECOMMENDATION_SERVICE] get_popular_products - Limit: {limit}, State: {state}")
        
        try:
            products = self.db_service.get_popular_products(limit, state)
            print(f"[RECOMMENDATION_SERVICE] get_popular_products - Retornando {len(products)} produtos")
            return products
        except Exception as e:
            print(f"[RECOMMENDATION_SERVICE] get_popular_products - ERRO: {str(e)}")
            return []
    
    async def get_related_products(
        self, 
        product_id: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Obter produtos relacionados"""
        print(f"[RECOMMENDATION_SERVICE] get_related_products - Product: {product_id}, Limit: {limit}")
        
        try:
            # Buscar produto base
            base_product = self.db_service.get_product_details(product_id)
            if not base_product:
                print(f"[RECOMMENDATION_SERVICE] get_related_products - Produto não encontrado: {product_id}")
                return []
            
            # Buscar produtos da mesma categoria
            category = base_product.get('category', '')
            related_products = self.db_service.get_products_by_category(category, limit + 1)
            
            # Remover o produto original da lista
            related_products = [p for p in related_products if p['product_id'] != product_id][:limit]
            
            print(f"[RECOMMENDATION_SERVICE] get_related_products - Retornando {len(related_products)} produtos relacionados")
            return related_products
            
        except Exception as e:
            print(f"[RECOMMENDATION_SERVICE] get_related_products - ERRO: {str(e)}")
            return []
    
    async def get_seasonal_recommendations(
        self, 
        month: int, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obter recomendações sazonais"""
        print(f"[RECOMMENDATION_SERVICE] get_seasonal_recommendations - Month: {month}, Limit: {limit}")
        
        try:
            # Para desenvolvimento, retornar produtos populares
            # Em produção, isso seria baseado em dados históricos sazonais
            products = self.db_service.get_popular_products(limit)
            
            # Adicionar contexto sazonal
            for product in products:
                product['seasonal_relevance'] = f"Popular no mês {month}"
            
            print(f"[RECOMMENDATION_SERVICE] get_seasonal_recommendations - Retornando {len(products)} produtos sazonais")
            return products
            
        except Exception as e:
            print(f"[RECOMMENDATION_SERVICE] get_seasonal_recommendations - ERRO: {str(e)}")
            return []
    
    async def get_top_rated_products(
        self, 
        min_reviews: int = 10, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Obter produtos mais bem avaliados"""
        print(f"[RECOMMENDATION_SERVICE] get_top_rated_products - Min reviews: {min_reviews}, Limit: {limit}")
        
        try:
            products = self.db_service.get_top_rated_products(min_reviews, limit)
            print(f"[RECOMMENDATION_SERVICE] get_top_rated_products - Retornando {len(products)} produtos")
            return products
        except Exception as e:
            print(f"[RECOMMENDATION_SERVICE] get_top_rated_products - ERRO: {str(e)}")
            return []
    
    async def _get_collaborative_recommendations(self, user_id: str, limit: int) -> List[str]:
        """Recomendações colaborativas"""
        print(f"[RECOMMENDATION_SERVICE] _get_collaborative_recommendations - User: {user_id}")
        
        try:
            # Buscar histórico do usuário
            user_history = self.db_service.get_user_purchase_history(user_id)
            
            if not user_history:
                print(f"[RECOMMENDATION_SERVICE] _get_collaborative_recommendations - Usuário sem histórico, usando produtos populares")
                popular_products = self.db_service.get_popular_products(limit)
                return [p['product_id'] for p in popular_products]
            
            # Em desenvolvimento, simular recomendações baseadas no histórico
            # Em produção, usar o modelo colaborativo treinado
            popular_products = self.db_service.get_popular_products(limit)
            return [p['product_id'] for p in popular_products]
            
        except Exception as e:
            print(f"[RECOMMENDATION_SERVICE] _get_collaborative_recommendations - ERRO: {str(e)}")
            # Fallback para produtos populares
            popular_products = self.db_service.get_popular_products(limit)
            return [p['product_id'] for p in popular_products]
    
    async def _get_content_recommendations(self, user_id: str, limit: int) -> List[str]:
        """Recomendações baseadas em conteúdo"""
        print(f"[RECOMMENDATION_SERVICE] _get_content_recommendations - User: {user_id}")
        
        try:
            # Buscar histórico do usuário
            user_history = self.db_service.get_user_purchase_history(user_id)
            
            if not user_history:
                print(f"[RECOMMENDATION_SERVICE] _get_content_recommendations - Usuário sem histórico, usando produtos populares")
                popular_products = self.db_service.get_popular_products(limit)
                return [p['product_id'] for p in popular_products]
            
            # Pegar categorias que o usuário já comprou
            user_categories = list(set([item['category'] for item in user_history]))
            
            # Buscar mais produtos dessas categorias
            recommendations = []
            for category in user_categories:
                category_products = self.db_service.get_products_by_category(category, limit // len(user_categories) + 1)
                recommendations.extend([p['product_id'] for p in category_products])
            
            # Remover duplicatas e limitar
            unique_recommendations = list(dict.fromkeys(recommendations))[:limit]
            
            print(f"[RECOMMENDATION_SERVICE] _get_content_recommendations - Retornando {len(unique_recommendations)} recomendações")
            return unique_recommendations
            
        except Exception as e:
            print(f"[RECOMMENDATION_SERVICE] _get_content_recommendations - ERRO: {str(e)}")
            # Fallback para produtos populares
            popular_products = self.db_service.get_popular_products(limit)
            return [p['product_id'] for p in popular_products]
    
    async def _get_hybrid_recommendations(self, user_id: str, limit: int) -> List[str]:
        """Recomendações híbridas"""
        print(f"[RECOMMENDATION_SERVICE] _get_hybrid_recommendations - User: {user_id}")
        
        try:
            # Combinar recomendações colaborativas e de conteúdo
            collab_recs = await self._get_collaborative_recommendations(user_id, limit // 2)
            content_recs = await self._get_content_recommendations(user_id, limit // 2)
            
            # Combinar e remover duplicatas
            hybrid_recs = list(dict.fromkeys(collab_recs + content_recs))[:limit]
            
            print(f"[RECOMMENDATION_SERVICE] _get_hybrid_recommendations - Retornando {len(hybrid_recs)} recomendações híbridas")
            return hybrid_recs
            
        except Exception as e:
            print(f"[RECOMMENDATION_SERVICE] _get_hybrid_recommendations - ERRO: {str(e)}")
            # Fallback para produtos populares
            popular_products = self.db_service.get_popular_products(limit)
            return [p['product_id'] for p in popular_products]