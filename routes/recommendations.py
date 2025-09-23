from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import traceback

from schemas.recommendation import RecommendationResponse
from schemas.user import User
from app_setup import recommendation_service  # Import da instância global
from utils.auth import get_current_user

router = APIRouter()

@router.get("/user/{user_id}")
async def get_user_recommendations(
    user_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    strategy: str = Query("collaborative", regex="^(collaborative|content|hybrid)$")
):
    """
    Obter recomendações personalizadas para um usuário
    """
    print(f"[RECOMMENDATIONS] get_user_recommendations - INÍCIO")
    print(f"[RECOMMENDATIONS] get_user_recommendations - User ID: {user_id}")
    print(f"[RECOMMENDATIONS] get_user_recommendations - Current user: {current_user.get('id') if isinstance(current_user, dict) else current_user}")
    print(f"[RECOMMENDATIONS] get_user_recommendations - Limit: {limit}")
    print(f"[RECOMMENDATIONS] get_user_recommendations - Strategy: {strategy}")
    
    try:
        recommendations = await recommendation_service.get_user_recommendations(
            user_id=user_id,
            limit=limit,
            strategy=strategy
        )
        
        print(f"[RECOMMENDATIONS] get_user_recommendations - Recomendações obtidas: {len(recommendations)}")
        
        return {
            "user_id": user_id,
            "strategy": strategy,
            "recommendations": recommendations,
            "total": len(recommendations)
        }
        
    except Exception as e:
        print(f"[RECOMMENDATIONS] get_user_recommendations - ERRO: {str(e)}")
        print(f"[RECOMMENDATIONS] get_user_recommendations - Tipo do erro: {type(e)}")
        print(f"[RECOMMENDATIONS] get_user_recommendations - Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter recomendações: {str(e)}"
        )

@router.get("/popular")
async def get_popular_products(
    limit: int = Query(10, ge=1, le=100),
    state: Optional[str] = Query(None)
):
    """
    Obter produtos populares
    """
    print(f"[RECOMMENDATIONS] get_popular_products - INÍCIO")
    print(f"[RECOMMENDATIONS] get_popular_products - Limit: {limit}")
    print(f"[RECOMMENDATIONS] get_popular_products - State: {state}")
    
    try:
        products = await recommendation_service.get_popular_products(
            limit=limit,
            state=state
        )
        
        print(f"[RECOMMENDATIONS] get_popular_products - Produtos obtidos: {len(products)}")
        
        return {
            "products": products,
            "total": len(products),
            "state": state
        }
        
    except Exception as e:
        print(f"[RECOMMENDATIONS] get_popular_products - ERRO: {str(e)}")
        print(f"[RECOMMENDATIONS] get_popular_products - Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter produtos populares: {str(e)}"
        )

@router.get("/related/{product_id}")
async def get_related_products(
    product_id: str,
    limit: int = Query(5, ge=1, le=50)
):
    """
    Obter produtos relacionados
    """
    print(f"[RECOMMENDATIONS] get_related_products - INÍCIO")
    print(f"[RECOMMENDATIONS] get_related_products - Product ID: {product_id}")
    print(f"[RECOMMENDATIONS] get_related_products - Limit: {limit}")
    
    try:
        products = await recommendation_service.get_related_products(
            product_id=product_id,
            limit=limit
        )
        
        print(f"[RECOMMENDATIONS] get_related_products - Produtos obtidos: {len(products)}")
        
        return {
            "product_id": product_id,
            "related_products": products,
            "total": len(products)
        }
        
    except Exception as e:
        print(f"[RECOMMENDATIONS] get_related_products - ERRO: {str(e)}")
        print(f"[RECOMMENDATIONS] get_related_products - Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter produtos relacionados: {str(e)}"
        )

@router.get("/seasonal")
async def get_seasonal_recommendations(
    month: int = Query(..., ge=1, le=12),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Obter recomendações sazonais
    """
    print(f"[RECOMMENDATIONS] get_seasonal_recommendations - INÍCIO")
    print(f"[RECOMMENDATIONS] get_seasonal_recommendations - Month: {month}")
    print(f"[RECOMMENDATIONS] get_seasonal_recommendations - Limit: {limit}")
    
    try:
        products = await recommendation_service.get_seasonal_recommendations(
            month=month,
            limit=limit
        )
        
        print(f"[RECOMMENDATIONS] get_seasonal_recommendations - Produtos obtidos: {len(products)}")
        
        return {
            "month": month,
            "seasonal_products": products,
            "total": len(products)
        }
        
    except Exception as e:
        print(f"[RECOMMENDATIONS] get_seasonal_recommendations - ERRO: {str(e)}")
        print(f"[RECOMMENDATIONS] get_seasonal_recommendations - Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter recomendações sazonais: {str(e)}"
        )

@router.get("/top-rated")
async def get_top_rated_products(
    min_reviews: int = Query(10, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Obter produtos mais bem avaliados
    """
    print(f"[RECOMMENDATIONS] get_top_rated_products - INÍCIO")
    print(f"[RECOMMENDATIONS] get_top_rated_products - Min reviews: {min_reviews}")
    print(f"[RECOMMENDATIONS] get_top_rated_products - Limit: {limit}")
    
    try:
        products = await recommendation_service.get_top_rated_products(
            min_reviews=min_reviews,
            limit=limit
        )
        
        print(f"[RECOMMENDATIONS] get_top_rated_products - Produtos obtidos: {len(products)}")
        
        return {
            "min_reviews": min_reviews,
            "top_rated_products": products,
            "total": len(products)
        }
        
    except Exception as e:
        print(f"[RECOMMENDATIONS] get_top_rated_products - ERRO: {str(e)}")
        print(f"[RECOMMENDATIONS] get_top_rated_products - Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter produtos mais bem avaliados: {str(e)}"
        )