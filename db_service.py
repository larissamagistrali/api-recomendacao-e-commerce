import pandas as pd
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

class DatabaseService:
    """Serviço de banco de dados usando arquivos CSV para desenvolvimento"""
    
    def __init__(self):
        """Inicializa o serviço carregando os dados dos CSVs"""
        print(f"[DB_SERVICE] __init__ - Inicializando DatabaseService")
        
        # Caminho para os arquivos CSV
        self.data_path = Path(__file__).parent / "ds"
        print(f"[DB_SERVICE] __init__ - Caminho dos dados: {self.data_path}")
        
        # Verificar se a pasta existe
        if not self.data_path.exists():
            print(f"[DB_SERVICE] __init__ - ERRO: Pasta de dados não encontrada: {self.data_path}")
            raise FileNotFoundError(f"Pasta de dados não encontrada: {self.data_path}")
        
        # Carregar os datasets
        self._load_datasets()
        print(f"[DB_SERVICE] __init__ - DatabaseService inicializado com sucesso")
    
    def _load_datasets(self):
        """Carrega todos os datasets necessários"""
        try:
            print(f"[DB_SERVICE] _load_datasets - Carregando datasets...")
            
            # Carregar datasets principais
            self.orders = pd.read_csv(self.data_path / "olist_orders_dataset.csv")
            self.order_items = pd.read_csv(self.data_path / "olist_order_items_dataset.csv")
            self.products = pd.read_csv(self.data_path / "olist_products_dataset.csv")
            self.customers = pd.read_csv(self.data_path / "olist_customers_dataset.csv")
            self.reviews = pd.read_csv(self.data_path / "olist_order_reviews_dataset.csv")
            self.sellers = pd.read_csv(self.data_path / "olist_sellers_dataset.csv")
            self.payments = pd.read_csv(self.data_path / "olist_order_payments_dataset.csv")
            
            # Carregar tradução de categorias se existir
            category_translation_path = self.data_path / "product_category_name_translation.csv"
            if category_translation_path.exists():
                self.category_translation = pd.read_csv(category_translation_path)
            else:
                self.category_translation = None
            
            print(f"[DB_SERVICE] _load_datasets - Datasets carregados:")
            print(f"  - Orders: {len(self.orders)} registros")
            print(f"  - Order Items: {len(self.order_items)} registros")
            print(f"  - Products: {len(self.products)} registros")
            print(f"  - Customers: {len(self.customers)} registros")
            print(f"  - Reviews: {len(self.reviews)} registros")
            print(f"  - Sellers: {len(self.sellers)} registros")
            print(f"  - Payments: {len(self.payments)} registros")
            
        except Exception as e:
            print(f"[DB_SERVICE] _load_datasets - ERRO ao carregar datasets: {str(e)}")
            raise e
    
    def get_popular_products(self, limit: int = 10, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retorna produtos populares baseado na quantidade de vendas"""
        print(f"[DB_SERVICE] get_popular_products - Limite: {limit}, Estado: {state}")
        
        try:
            # Juntar order_items com orders para ter informações completas
            merged_data = self.order_items.merge(self.orders, on='order_id', how='inner')
            
            # Se estado foi especificado, filtrar por customers desse estado
            if state:
                # Juntar com customers para filtrar por estado
                merged_data = merged_data.merge(self.customers, on='customer_id', how='inner')
                merged_data = merged_data[merged_data['customer_state'] == state.upper()]
            
            # Agrupar por produto e contar vendas
            product_sales = (merged_data.groupby('product_id')
                           .agg({
                               'order_item_id': 'count',  # Quantidade vendida
                               'price': 'mean',           # Preço médio
                               'freight_value': 'mean'    # Frete médio
                           })
                           .rename(columns={'order_item_id': 'sales_count'}))
            
            # Ordenar por vendas e pegar os top N
            top_products = product_sales.sort_values('sales_count', ascending=False).head(limit)
            
            # Juntar com informações do produto
            result = []
            for product_id, row in top_products.iterrows():
                product_info = self.products[self.products['product_id'] == product_id]
                
                if not product_info.empty:
                    product_data = product_info.iloc[0]
                    
                    result.append({
                        'product_id': product_id,
                        'sales_count': int(row['sales_count']),
                        'average_price': float(row['price']),
                        'average_freight': float(row['freight_value']),
                        'category': product_data.get('product_category_name', 'Unknown'),
                        'weight_g': product_data.get('product_weight_g', 0),
                        'length_cm': product_data.get('product_length_cm', 0),
                        'height_cm': product_data.get('product_height_cm', 0),
                        'width_cm': product_data.get('product_width_cm', 0)
                    })
            
            print(f"[DB_SERVICE] get_popular_products - Retornando {len(result)} produtos")
            return result
            
        except Exception as e:
            print(f"[DB_SERVICE] get_popular_products - ERRO: {str(e)}")
            import traceback
            print(f"[DB_SERVICE] get_popular_products - Traceback: {traceback.format_exc()}")
            raise e
    
    def get_user_purchase_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Retorna o histórico de compras de um usuário"""
        print(f"[DB_SERVICE] get_user_purchase_history - User ID: {user_id}")
        
        try:
            # Como não temos user_id real, vamos simular baseado no customer_id
            # Em produção, isso seria uma busca real no banco
            user_orders = self.orders[self.orders['customer_id'].str.contains(user_id[:8], na=False)]
            
            if user_orders.empty:
                print(f"[DB_SERVICE] get_user_purchase_history - Nenhum pedido encontrado, retornando lista vazia")
                return []
            
            # Juntar com order_items para ter os produtos
            user_items = user_orders.merge(self.order_items, on='order_id', how='inner')
            
            # Juntar com products para ter informações dos produtos
            user_purchases = user_items.merge(self.products, on='product_id', how='left')
            
            result = []
            for _, row in user_purchases.iterrows():
                result.append({
                    'order_id': row['order_id'],
                    'product_id': row['product_id'],
                    'category': row.get('product_category_name', 'Unknown'),
                    'price': float(row['price']),
                    'purchase_timestamp': row['order_purchase_timestamp']
                })
            
            print(f"[DB_SERVICE] get_user_purchase_history - Retornando {len(result)} compras")
            return result
            
        except Exception as e:
            print(f"[DB_SERVICE] get_user_purchase_history - ERRO: {str(e)}")
            return []
    
    def get_product_details(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Retorna detalhes de um produto específico"""
        print(f"[DB_SERVICE] get_product_details - Product ID: {product_id}")
        
        try:
            product_info = self.products[self.products['product_id'] == product_id]
            
            if product_info.empty:
                print(f"[DB_SERVICE] get_product_details - Produto não encontrado")
                return None
            
            product_data = product_info.iloc[0]
            
            # Buscar estatísticas de vendas
            sales_data = self.order_items[self.order_items['product_id'] == product_id]
            
            result = {
                'product_id': product_id,
                'category': product_data.get('product_category_name', 'Unknown'),
                'weight_g': product_data.get('product_weight_g', 0),
                'length_cm': product_data.get('product_length_cm', 0),
                'height_cm': product_data.get('product_height_cm', 0),
                'width_cm': product_data.get('product_width_cm', 0),
                'sales_count': len(sales_data),
                'average_price': float(sales_data['price'].mean()) if not sales_data.empty else 0.0
            }
            
            print(f"[DB_SERVICE] get_product_details - Produto encontrado: {result['category']}")
            return result
            
        except Exception as e:
            print(f"[DB_SERVICE] get_product_details - ERRO: {str(e)}")
            return None
    
    def get_products_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna produtos de uma categoria específica"""
        print(f"[DB_SERVICE] get_products_by_category - Categoria: {category}, Limite: {limit}")
        
        try:
            # Filtrar produtos por categoria
            category_products = self.products[
                self.products['product_category_name'].str.contains(category, case=False, na=False)
            ].head(limit)
            
            result = []
            for _, product in category_products.iterrows():
                # Buscar estatísticas de vendas
                sales_data = self.order_items[self.order_items['product_id'] == product['product_id']]
                
                result.append({
                    'product_id': product['product_id'],
                    'category': product.get('product_category_name', 'Unknown'),
                    'weight_g': product.get('product_weight_g', 0),
                    'sales_count': len(sales_data),
                    'average_price': float(sales_data['price'].mean()) if not sales_data.empty else 0.0
                })
            
            print(f"[DB_SERVICE] get_products_by_category - Retornando {len(result)} produtos")
            return result
            
        except Exception as e:
            print(f"[DB_SERVICE] get_products_by_category - ERRO: {str(e)}")
            return []
    
    def get_top_rated_products(self, min_reviews: int = 10, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna produtos mais bem avaliados"""
        print(f"[DB_SERVICE] get_top_rated_products - Min reviews: {min_reviews}, Limite: {limit}")
        
        try:
            # Juntar reviews com order_items para ter product_id
            reviews_with_products = self.reviews.merge(self.order_items, on='order_id', how='inner')
            
            # Agrupar por produto e calcular estatísticas
            product_ratings = (reviews_with_products.groupby('product_id')
                             .agg({
                                 'review_score': ['mean', 'count']
                             }))
            
            # Achatar colunas
            product_ratings.columns = ['avg_rating', 'review_count']
            
            # Filtrar por mínimo de reviews e ordenar por rating
            top_rated = (product_ratings[product_ratings['review_count'] >= min_reviews]
                        .sort_values('avg_rating', ascending=False)
                        .head(limit))
            
            result = []
            for product_id, row in top_rated.iterrows():
                product_info = self.products[self.products['product_id'] == product_id]
                
                if not product_info.empty:
                    product_data = product_info.iloc[0]
                    
                    result.append({
                        'product_id': product_id,
                        'average_rating': float(row['avg_rating']),
                        'review_count': int(row['review_count']),
                        'category': product_data.get('product_category_name', 'Unknown')
                    })
            
            print(f"[DB_SERVICE] get_top_rated_products - Retornando {len(result)} produtos")
            return result
            
        except Exception as e:
            print(f"[DB_SERVICE] get_top_rated_products - ERRO: {str(e)}")
            return []