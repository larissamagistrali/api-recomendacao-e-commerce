from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import traceback

from schemas.analytics import MetricsResponse, CategoryResponse, UserBehaviorResponse
from schemas.user import User
from app_setup import analytics_service  # Import da instância global
from utils.auth import get_current_user

router = APIRouter()

@router.get("/metrics", response_model=MetricsResponse)
async def get_general_metrics():
    """
    Obter métricas gerais da plataforma
    """
    print(f"[ANALYTICS] get_general_metrics - INÍCIO")
    
    try:
        metrics = await analytics_service.get_general_metrics()
        print(f"[ANALYTICS] get_general_metrics - Métricas obtidas")
        return metrics
        
    except Exception as e:
        print(f"[ANALYTICS] get_general_metrics - ERRO: {str(e)}")
        print(f"[ANALYTICS] get_general_metrics - Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter métricas: {str(e)}"
        )

@router.get("/categories", response_model=CategoryResponse)
async def get_popular_categories(
    limit: int = Query(10, ge=1, le=50)
):
    """
    Obter categorias mais populares
    """
    print(f"[ANALYTICS] get_popular_categories - INÍCIO")
    print(f"[ANALYTICS] get_popular_categories - Limit: {limit}")
    
    try:
        categories = await analytics_service.get_popular_categories(limit=limit)
        
        print(f"[ANALYTICS] get_popular_categories - Categorias obtidas: {len(categories)}")
        
        return {
            "categories": categories,
            "total": len(categories)
        }
        
    except Exception as e:
        print(f"[ANALYTICS] get_popular_categories - ERRO: {str(e)}")
        print(f"[ANALYTICS] get_popular_categories - Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter categorias: {str(e)}"
        )

# Adicionar rota alternativa para popular-categories
@router.get("/popular-categories", response_model=CategoryResponse)
async def get_popular_categories_alt(
    limit: int = Query(10, ge=1, le=50)
):
    """
    Obter categorias mais populares (rota alternativa)
    """
    print(f"[ANALYTICS] get_popular_categories_alt - INÍCIO")
    print(f"[ANALYTICS] get_popular_categories_alt - Limit: {limit}")
    
    try:
        categories = await analytics_service.get_popular_categories(limit=limit)
        
        print(f"[ANALYTICS] get_popular_categories_alt - Categorias obtidas: {len(categories)}")
        
        return {
            "categories": categories,
            "total": len(categories)
        }
        
    except Exception as e:
        print(f"[ANALYTICS] get_popular_categories_alt - ERRO: {str(e)}")
        print(f"[ANALYTICS] get_popular_categories_alt - Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter categorias: {str(e)}"
        )

@router.get("/user-behavior/{user_id}", response_model=UserBehaviorResponse)
async def get_user_behavior(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obter comportamento de um usuário específico
    """
    print(f"[ANALYTICS] get_user_behavior - INÍCIO")
    print(f"[ANALYTICS] get_user_behavior - User ID: {user_id}")
    print(f"[ANALYTICS] get_user_behavior - Current user: {current_user.get('id') if isinstance(current_user, dict) else current_user}")
    
    try:
        behavior = await analytics_service.get_user_behavior(user_id=user_id)
        
        print(f"[ANALYTICS] get_user_behavior - Comportamento obtido")
        return behavior
        
    except Exception as e:
        print(f"[ANALYTICS] get_user_behavior - ERRO: {str(e)}")
        print(f"[ANALYTICS] get_user_behavior - Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter comportamento do usuário: {str(e)}"
        )

@router.get("/sales-overview")
async def get_sales_overview(
    period: str = Query("last_30_days", regex="^(last_7_days|last_30_days|last_90_days|last_year)$")
):
    """
    Obter overview de vendas por período
    """
    print(f"[ANALYTICS] get_sales_overview - INÍCIO")
    print(f"[ANALYTICS] get_sales_overview - Period: {period}")
    
    try:
        # Para desenvolvimento, retornar dados simulados
        overview = {
            "period": period,
            "total_sales": 15000,
            "total_revenue": 2500000.00,
            "avg_order_value": 166.67,
            "growth_rate": 0.12,
            "top_categories": [
                {"category": "electronics", "percentage": 25.5},
                {"category": "housewares", "percentage": 18.3},
                {"category": "fashion", "percentage": 15.2}
            ]
        }
        
        print(f"[ANALYTICS] get_sales_overview - Overview gerado")
        return overview
        
    except Exception as e:
        print(f"[ANALYTICS] get_sales_overview - ERRO: {str(e)}")
        print(f"[ANALYTICS] get_sales_overview - Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter overview de vendas: {str(e)}"
        )

@router.get("/trends")
async def get_trends(
    category: Optional[str] = Query(None),
    period: str = Query("last_30_days", regex="^(last_7_days|last_30_days|last_90_days|last_year)$")
):
    """
    Obter tendências de vendas
    """
    print(f"[ANALYTICS] get_trends - INÍCIO")
    print(f"[ANALYTICS] get_trends - Category: {category}, Period: {period}")
    
    try:
        # Para desenvolvimento, retornar dados simulados
        trends = {
            "period": period,
            "category": category,
            "trending_up": [
                {"product_category": "electronics", "growth_rate": 0.25},
                {"product_category": "sports", "growth_rate": 0.18}
            ],
            "trending_down": [
                {"product_category": "books", "growth_rate": -0.12},
                {"product_category": "toys", "growth_rate": -0.08}
            ],
            "stable": [
                {"product_category": "housewares", "growth_rate": 0.02}
            ]
        }
        
        print(f"[ANALYTICS] get_trends - Tendências geradas")
        return trends
        
    except Exception as e:
        print(f"[ANALYTICS] get_trends - ERRO: {str(e)}")
        print(f"[ANALYTICS] get_trends - Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter tendências: {str(e)}"
        )

# Adicionar endpoint para listar todas as rotas disponíveis
@router.get("/")
async def list_analytics_endpoints():
    """
    Listar todos os endpoints de analytics disponíveis
    """
    return {
        "message": "Analytics API Endpoints",
        "endpoints": [
            {
                "path": "/analytics/metrics",
                "method": "GET",
                "description": "Obter métricas gerais da plataforma"
            },
            {
                "path": "/analytics/categories",
                "method": "GET", 
                "description": "Obter categorias mais populares"
            },
            {
                "path": "/analytics/popular-categories",
                "method": "GET",
                "description": "Obter categorias mais populares (rota alternativa)"
            },
            {
                "path": "/analytics/user-behavior/{user_id}",
                "method": "GET",
                "description": "Obter comportamento de um usuário específico"
            },
            {
                "path": "/analytics/sales-overview",
                "method": "GET",
                "description": "Obter overview de vendas por período"
            },
            {
                "path": "/analytics/trends",
                "method": "GET",
                "description": "Obter tendências de vendas"
            }
        ]
    }