from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Adicionar o diretório pai ao path para importar db_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_service import DatabaseService

class AnalyticsService:
    """Serviço de analytics e métricas"""
    
    def __init__(self, db_service: DatabaseService):
        print(f"[ANALYTICS_SERVICE] __init__ - Inicializando AnalyticsService")
        self.db_service = db_service
        print(f"[ANALYTICS_SERVICE] __init__ - AnalyticsService inicializado")
    
    async def get_general_metrics(self) -> Dict[str, Any]:
        """Obter métricas gerais da plataforma"""
        print(f"[ANALYTICS_SERVICE] get_general_metrics - Calculando métricas gerais")
        
        try:
            # Métricas simples baseadas nos datasets carregados
            total_orders = len(self.db_service.orders)
            total_products = len(self.db_service.products)
            total_customers = len(self.db_service.customers)
            total_sellers = len(self.db_service.sellers)
            
            # Calcular receita total
            total_revenue = self.db_service.order_items['price'].sum()
            
            # Ticket médio
            avg_order_value = self.db_service.order_items.groupby('order_id')['price'].sum().mean()
            
            # Reviews médias
            avg_rating = self.db_service.reviews['review_score'].mean()
            
            metrics = {
                "total_orders": int(total_orders),
                "total_products": int(total_products),
                "total_customers": int(total_customers),
                "total_sellers": int(total_sellers),
                "total_revenue": float(total_revenue),
                "avg_order_value": float(avg_order_value),
                "avg_rating": float(avg_rating),
                "last_updated": datetime.now().isoformat()
            }
            
            print(f"[ANALYTICS_SERVICE] get_general_metrics - Métricas calculadas: {len(metrics)} itens")
            return metrics
            
        except Exception as e:
            print(f"[ANALYTICS_SERVICE] get_general_metrics - ERRO: {str(e)}")
            return {
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
    
    async def get_popular_categories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obter categorias mais populares"""
        print(f"[ANALYTICS_SERVICE] get_popular_categories - Limit: {limit}")
        
        try:
            # Juntar order_items com products para ter categorias
            items_with_products = self.db_service.order_items.merge(
                self.db_service.products, 
                on='product_id', 
                how='inner'
            )
            
            # Agrupar por categoria
            category_stats = (items_with_products.groupby('product_category_name')
                            .agg({
                                'order_id': 'count',
                                'price': ['sum', 'mean']
                            }))
            
            # Achatar colunas
            category_stats.columns = ['order_count', 'total_revenue', 'avg_price']
            
            # Ordenar por número de pedidos
            top_categories = category_stats.sort_values('order_count', ascending=False).head(limit)
            
            result = []
            for category, stats in top_categories.iterrows():
                if pd.notna(category):  # Ignorar categorias vazias
                    result.append({
                        "category": category,
                        "order_count": int(stats['order_count']),
                        "total_revenue": float(stats['total_revenue']),
                        "avg_price": float(stats['avg_price'])
                    })
            
            print(f"[ANALYTICS_SERVICE] get_popular_categories - Retornando {len(result)} categorias")
            return result
            
        except Exception as e:
            print(f"[ANALYTICS_SERVICE] get_popular_categories - ERRO: {str(e)}")
            return []
    
    async def get_user_behavior(self, user_id: str) -> Dict[str, Any]:
        """Obter comportamento de um usuário específico"""
        print(f"[ANALYTICS_SERVICE] get_user_behavior - User ID: {user_id}")
        
        try:
            # Buscar histórico de compras do usuário
            user_history = self.db_service.get_user_purchase_history(user_id)
            
            if not user_history:
                return {
                    "user_id": user_id,
                    "total_orders": 0,
                    "total_spent": 0.0,
                    "favorite_categories": [],
                    "avg_order_value": 0.0,
                    "message": "Usuário sem histórico de compras"
                }
            
            # Calcular estatísticas
            total_orders = len(user_history)
            total_spent = sum([item['price'] for item in user_history])
            avg_order_value = total_spent / total_orders if total_orders > 0 else 0.0
            
            # Categorias favoritas
            category_counts = {}
            for item in user_history:
                category = item['category']
                category_counts[category] = category_counts.get(category, 0) + 1
            
            favorite_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            behavior = {
                "user_id": user_id,
                "total_orders": total_orders,
                "total_spent": float(total_spent),
                "avg_order_value": float(avg_order_value),
                "favorite_categories": [{"category": cat, "count": count} for cat, count in favorite_categories],
                "last_purchase": user_history[-1]['purchase_timestamp'] if user_history else None
            }
            
            print(f"[ANALYTICS_SERVICE] get_user_behavior - Comportamento calculado para {user_id}")
            return behavior
            
        except Exception as e:
            print(f"[ANALYTICS_SERVICE] get_user_behavior - ERRO: {str(e)}")
            return {
                "user_id": user_id,
                "error": str(e)
            }