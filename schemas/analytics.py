from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from decimal import Decimal

class CategoryStats(BaseModel):
    category_name: str
    category_english: Optional[str] = None
    total_sales: int
    total_revenue: Decimal
    avg_rating: Optional[float] = None
    growth_rate: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "category_name": "utilidades_domesticas",
                "category_english": "housewares",
                "total_sales": 1500,
                "total_revenue": 150000.00,
                "avg_rating": 4.2,
                "growth_rate": 0.15
            }
        }

class UserBehavior(BaseModel):
    user_id: str
    total_purchases: int
    favorite_categories: List[str]
    avg_order_value: Decimal
    purchase_frequency: str
    seasonal_patterns: Optional[Dict[str, Any]] = None
    last_purchase_date: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "customer123",
                "total_purchases": 25,
                "favorite_categories": ["electronics", "housewares"],
                "avg_order_value": 156.50,
                "purchase_frequency": "monthly",
                "seasonal_patterns": {"peak_month": 12, "avg_monthly_purchases": 2.1},
                "last_purchase_date": "2025-09-15"
            }
        }

class AnalyticsResponse(BaseModel):
    metric_name: str
    value: Any
    period: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "metric_name": "total_sales",
                "value": 50000,
                "period": "last_30_days",
                "timestamp": "2025-09-22T10:30:00Z",
                "metadata": {"growth_rate": 0.12, "comparison_period": "previous_30_days"}
            }
        }

class SalesMetrics(BaseModel):
    total_sales: int
    total_revenue: Decimal
    avg_order_value: Decimal
    unique_customers: int
    top_selling_products: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_sales": 10000,
                "total_revenue": 1500000.00,
                "avg_order_value": 150.00,
                "unique_customers": 5000,
                "top_selling_products": ["prod1", "prod2", "prod3"]
            }
        }

# Adicionar as classes que estavam faltando
class MetricsResponse(BaseModel):
    """Resposta para métricas gerais"""
    total_orders: int
    total_products: int
    total_customers: int
    total_sellers: int
    total_revenue: float
    avg_order_value: float
    avg_rating: float
    last_updated: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_orders": 99441,
                "total_products": 32951,
                "total_customers": 99441,
                "total_sellers": 3095,
                "total_revenue": 13591643.70,
                "avg_order_value": 137.75,
                "avg_rating": 4.09,
                "last_updated": "2025-09-22T10:30:00Z"
            }
        }

class CategoryResponse(BaseModel):
    """Resposta para categorias populares"""
    categories: List[Dict[str, Any]]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "categories": [
                    {
                        "category": "cama_mesa_banho",
                        "order_count": 11119,
                        "total_revenue": 1218670.30,
                        "avg_price": 109.65
                    }
                ],
                "total": 10
            }
        }

class UserBehaviorResponse(BaseModel):
    """Resposta para comportamento do usuário"""
    user_id: str
    total_orders: int
    total_spent: float
    avg_order_value: float
    favorite_categories: List[Dict[str, Any]]
    last_purchase: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "8d8e5a13-5f48-4235-8067-3a600eeb4460",
                "total_orders": 3,
                "total_spent": 285.50,
                "avg_order_value": 95.17,
                "favorite_categories": [
                    {"category": "electronics", "count": 2},
                    {"category": "housewares", "count": 1}
                ],
                "last_purchase": "2023-05-15T14:30:00Z"
            }
        }

# Manter compatibilidade com nomes antigos
CategoryStats = CategoryStats
UserBehavior = UserBehavior
AnalyticsResponse = AnalyticsResponse
SalesMetrics = SalesMetrics