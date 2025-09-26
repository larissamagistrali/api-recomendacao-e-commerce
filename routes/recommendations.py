from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import Optional, List, Dict, Any
import traceback

from services.complementary_service import ComplementaryRecommendationService

router = APIRouter()

# Instância global do serviço de produtos complementares
complementary_service = ComplementaryRecommendationService()

@router.on_event("startup")
async def startup_event():
    """Inicializa o serviço na startup da aplicação"""
    await complementary_service.initialize()

@router.on_event("shutdown")
async def shutdown_event():
    """Fecha conexões na shutdown da aplicação"""
    await complementary_service.close()

@router.get("/complementary/{product_id}")
async def get_complementary_products(
    product_id: str,
    context_type: str = Query("PDP", regex="^(PDP|CART)$"),
    user_id: Optional[str] = Query(None),
    session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    limit: int = Query(10, ge=1, le=50),
    min_stock: Optional[int] = Query(1, ge=0),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5)
):
    """
    Obter produtos complementares ("Comprados Juntos") para um produto
    
    Args:
        product_id: ID do produto base
        context_type: Contexto da recomendação (PDP = Página do Produto, CART = Carrinho)
        user_id: ID do usuário (opcional)
        session_id: ID da sessão do usuário (header X-Session-ID)
        limit: Número máximo de produtos a retornar
        min_stock: Estoque mínimo necessário
        category: Filtrar por categoria específica
        min_price: Preço mínimo
        max_price: Preço máximo
        min_rating: Avaliação mínima
    """
    print(f"[COMPLEMENTARY_API] Buscando produtos complementares para {product_id}")
    
    try:
        # Construir filtros
        filters = {}
        if min_stock is not None:
            filters['min_stock'] = min_stock
        if category:
            filters['category'] = category
        if min_price is not None:
            filters['min_price'] = min_price
        if max_price is not None:
            filters['max_price'] = max_price
        if min_rating is not None:
            filters['min_rating'] = min_rating
        
        # Buscar produtos complementares
        result = await complementary_service.get_complementary_products(
            product_id=product_id,
            context_type=context_type,
            user_id=user_id,
            session_id=session_id,
            filters=filters,
            limit=limit
        )
        
        print(f"[COMPLEMENTARY_API] Retornando {result['total']} recomendações")
        
        return result
        
    except Exception as e:
        print(f"[COMPLEMENTARY_API] Erro: {str(e)}")
        print(f"[COMPLEMENTARY_API] Traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar produtos complementares: {str(e)}"
        )

@router.post("/outcome/{rec_set_id}")
async def log_recommendation_outcome(
    rec_set_id: int,
    product_id: str,
    outcome_type: str = Query(..., regex="^(view|add_to_cart|purchase)$"),
    outcome_value: Optional[float] = Query(None, ge=0)
):
    """
    Registra o resultado de uma recomendação (conversão)
    
    Args:
        rec_set_id: ID do conjunto de recomendações
        product_id: ID do produto que teve interação
        outcome_type: Tipo de resultado (view, add_to_cart, purchase)
        outcome_value: Valor monetário da conversão (para purchases)
    """
    try:
        await complementary_service.log_recommendation_outcome(
            rec_set_id=rec_set_id,
            product_id=product_id,
            outcome_type=outcome_type,
            outcome_value=outcome_value
        )
        
        return {
            "status": "success",
            "rec_set_id": rec_set_id,
            "product_id": product_id,
            "outcome_type": outcome_type,
            "outcome_value": outcome_value
        }
        
    except Exception as e:
        print(f"[COMPLEMENTARY_API] Erro ao logar outcome: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao registrar resultado: {str(e)}"
        )

@router.get("/analytics")
async def get_recommendation_analytics(
    days_back: int = Query(7, ge=1, le=90)
):
    """
    Obter analytics de performance das recomendações
    """
    try:
        analytics = await complementary_service.get_recommendation_analytics(days_back)
        
        return {
            "period_days": days_back,
            "analytics": analytics
        }
        
    except Exception as e:
        print(f"[COMPLEMENTARY_API] Erro ao buscar analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao buscar analytics: {str(e)}"
        )

@router.get("/health")
async def get_service_health():
    """
    Verifica a saúde dos serviços
    """
    try:
        health = complementary_service.get_service_health()
        return health
        
    except Exception as e:
        return {
            "error": str(e),
            "overall": False,
            "timestamp": None
        }