from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ComplementaryProductRequest(BaseModel):
    """Request para produtos complementares"""
    product_id: str = Field(..., description="ID do produto base")
    context_type: str = Field("PDP", description="Contexto da recomendação (PDP ou CART)")
    user_id: Optional[str] = Field(None, description="ID do usuário")
    session_id: Optional[str] = Field(None, description="ID da sessão")
    limit: int = Field(10, ge=1, le=50, description="Número máximo de produtos")
    
    # Filtros
    min_stock: Optional[int] = Field(1, ge=0, description="Estoque mínimo")
    category: Optional[str] = Field(None, description="Categoria específica")
    min_price: Optional[float] = Field(None, ge=0, description="Preço mínimo")
    max_price: Optional[float] = Field(None, ge=0, description="Preço máximo")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Avaliação mínima")

class ComplementaryProduct(BaseModel):
    """Produto complementar com scores"""
    product_id: str
    product_name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    margin: Optional[float] = None
    stock_quantity: Optional[int] = None
    in_stock: Optional[bool] = None
    avg_rating: Optional[float] = None
    review_count: Optional[int] = None
    
    # Scores de recomendação
    lift_score: float = Field(..., description="Score de lift (coocorrência)")
    npmi_score: float = Field(..., description="Score NPMI (associação normalizada)")
    cooccurrence_count: int = Field(..., description="Número de coocorrências")
    rerank_score: Optional[float] = Field(None, description="Score após rerank")
    
    # Metadados
    recommendation_reason: Optional[str] = Field(None, description="Razão da recomendação")
    position: Optional[int] = Field(None, description="Posição na lista")

class ComplementaryResponse(BaseModel):
    """Resposta de produtos complementares"""
    product_id: str
    context_type: str
    session_id: Optional[str] = None
    rec_set_id: Optional[int] = None
    recommendations: List[ComplementaryProduct]
    total: int
    source: str = Field(..., description="Fonte da recomendação (algorithm, cache, fallback)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class OutcomeLogRequest(BaseModel):
    """Request para log de resultado de recomendação"""
    rec_set_id: int = Field(..., description="ID do conjunto de recomendações")
    product_id: str = Field(..., description="ID do produto")
    outcome_type: str = Field(..., regex="^(view|add_to_cart|purchase)$", description="Tipo de resultado")
    outcome_value: Optional[float] = Field(None, ge=0, description="Valor monetário")

class OutcomeLogResponse(BaseModel):
    """Resposta do log de resultado"""
    status: str
    rec_set_id: int
    product_id: str
    outcome_type: str
    outcome_value: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class RecommendationAnalytics(BaseModel):
    """Analytics de performance das recomendações"""
    period_days: int
    total_recommendations_shown: int
    total_interactions: int
    add_to_cart_count: int
    purchase_count: int
    avg_purchase_value: float
    
    # Métricas calculadas
    interaction_rate: Optional[float] = Field(None, description="Taxa de interação")
    add_to_cart_rate: Optional[float] = Field(None, description="Taxa de adição ao carrinho")
    purchase_rate: Optional[float] = Field(None, description="Taxa de compra")
    
    context_performance: List[Dict[str, Any]] = Field(default_factory=list)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Calcular métricas derivadas
        if self.total_recommendations_shown > 0:
            self.interaction_rate = self.total_interactions / self.total_recommendations_shown
            self.add_to_cart_rate = self.add_to_cart_count / self.total_recommendations_shown
            self.purchase_rate = self.purchase_count / self.total_recommendations_shown

class ServiceHealth(BaseModel):
    """Status de saúde dos serviços"""
    redis: bool
    postgresql: bool
    elasticsearch: Dict[str, Any]
    overall: bool
    timestamp: Optional[str] = None

class BatchProcessingResult(BaseModel):
    """Resultado do processamento batch"""
    status: str
    total_candidates: Optional[int] = None
    unique_products: Optional[int] = None
    es_products_indexed: Optional[int] = None
    model_stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

class CacheStats(BaseModel):
    """Estatísticas do cache Redis"""
    redis_version: Optional[str] = None
    used_memory_human: Optional[str] = None
    connected_clients: Optional[int] = None
    total_keys: Optional[int] = None
    key_counts: Dict[str, int] = Field(default_factory=dict)
    hit_rate: float = 0.0