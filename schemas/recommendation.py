from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

class ProductRecommendation(BaseModel):
    product_id: str
    score: float
    reason: Optional[str] = None
    category: Optional[str] = None
    avg_rating: Optional[float] = None
    total_sales: Optional[int] = None
    avg_price: Optional[Decimal] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "1e9e8ef04dbcff4541ed26657ea5f2f8",
                "score": 0.85,
                "reason": "Frequentemente comprado junto com seus produtos favoritos",
                "category": "housewares",
                "avg_rating": 4.5,
                "total_sales": 150,
                "avg_price": 89.90
            }
        }

class RecommendationResponse(BaseModel):
    user_id: str
    strategy: str
    recommendations: List[ProductRecommendation]
    total_count: int
    timestamp: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "customer123",
                "strategy": "hybrid",
                "recommendations": [
                    {
                        "product_id": "1e9e8ef04dbcff4541ed26657ea5f2f8",
                        "score": 0.85,
                        "reason": "Similar aos seus produtos favoritos",
                        "category": "housewares"
                    }
                ],
                "total_count": 1,
                "timestamp": "2025-09-22T10:30:00Z"
            }
        }

class RecommendationRequest(BaseModel):
    user_id: str
    strategy: str = "hybrid"
    limit: int = 10
    filters: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "customer123",
                "strategy": "collaborative",
                "limit": 5,
                "filters": {"category": "electronics", "min_rating": 4.0}
            }
        }