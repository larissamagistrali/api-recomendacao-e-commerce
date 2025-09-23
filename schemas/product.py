from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

class ProductBase(BaseModel):
    product_id: str
    product_category_name: Optional[str] = None
    product_weight_g: Optional[int] = None
    product_length_cm: Optional[int] = None
    product_height_cm: Optional[int] = None
    product_width_cm: Optional[int] = None

class Product(ProductBase):
    product_name_length: Optional[int] = None
    product_description_length: Optional[int] = None
    product_photos_qty: Optional[int] = None
    category_english: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "product_id": "1e9e8ef04dbcff4541ed26657ea5f2f8",
                "product_category_name": "utilidades_domesticas",
                "category_english": "housewares",
                "product_weight_g": 500,
                "product_length_cm": 20,
                "product_height_cm": 10,
                "product_width_cm": 15
            }
        }

class ProductStats(BaseModel):
    product_id: str
    total_sales: int
    avg_rating: Optional[float] = None
    total_reviews: int
    avg_price: Optional[Decimal] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "1e9e8ef04dbcff4541ed26657ea5f2f8",
                "total_sales": 150,
                "avg_rating": 4.5,
                "total_reviews": 45,
                "avg_price": 89.90
            }
        }