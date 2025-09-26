import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
import os

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.cooccurrence import CooccurrenceModel
from services.postgresql_service import PostgreSQLService
from services.elasticsearch_service import ElasticsearchService
from config import Config

class BatchProcessor:
    """Processador batch para calcular produtos complementares"""
    
    def __init__(self):
        self.cooccurrence_model = CooccurrenceModel()
        self.pg_service = PostgreSQLService()
        self.es_service = ElasticsearchService()
        self.data_path = Path("ds")
        
    async def initialize(self):
        """Inicializa os serviços"""
        print("[BATCH] Inicializando serviços...")
        await self.pg_service.initialize()
        self.es_service.create_products_index()
        print("[BATCH] Serviços inicializados")
        
    async def close(self):
        """Fecha as conexões"""
        await self.pg_service.close()
        
    def load_order_data(self, months_back: int = None) -> pd.DataFrame:
        """Carrega dados de pedidos dos últimos N meses"""
        months_back = months_back or Config.BATCH_PROCESSING_MONTHS
        
        print(f"[BATCH] Carregando dados dos últimos {months_back} meses...")
        
        # Carregar datasets
        orders_df = pd.read_csv(self.data_path / "olist_orders_dataset.csv")
        order_items_df = pd.read_csv(self.data_path / "olist_order_items_dataset.csv")
        
        # Converter data de compra
        orders_df['order_purchase_timestamp'] = pd.to_datetime(orders_df['order_purchase_timestamp'])
        
        # Filtrar pedidos recentes - usar todos os dados para demonstração
        print("[BATCH] Usando todos os pedidos para demonstração (não filtrando por data)")
        recent_orders = orders_df[
            orders_df['order_status'].isin(['delivered', 'shipped'])
        ]
        
        # Fazer join com itens dos pedidos
        order_items_filtered = order_items_df[
            order_items_df['order_id'].isin(recent_orders['order_id'])
        ]
        
        print(f"[BATCH] Carregados {len(recent_orders)} pedidos com {len(order_items_filtered)} itens")
        
        return order_items_filtered[['order_id', 'product_id']]
        
    def load_product_catalog(self) -> pd.DataFrame:
        """Carrega catálogo de produtos com informações adicionais"""
        print("[BATCH] Carregando catálogo de produtos...")
        
        # Carregar datasets
        products_df = pd.read_csv(self.data_path / "olist_products_dataset.csv")
        order_items_df = pd.read_csv(self.data_path / "olist_order_items_dataset.csv")
        reviews_df = pd.read_csv(self.data_path / "olist_order_reviews_dataset.csv")
        
        # Calcular estatísticas por produto
        product_stats = order_items_df.groupby('product_id').agg({
            'price': ['mean', 'count'],
            'freight_value': 'mean'
        }).round(2)
        
        product_stats.columns = ['avg_price', 'order_count', 'avg_freight']
        product_stats = product_stats.reset_index()
        
        # Calcular avaliações médias
        review_stats = reviews_df.groupby('order_id')['review_score'].mean().reset_index()
        order_reviews = order_items_df.merge(review_stats, on='order_id', how='left')
        product_reviews = order_reviews.groupby('product_id')['review_score'].agg(['mean', 'count']).reset_index()
        product_reviews.columns = ['product_id', 'avg_rating', 'review_count']
        
        # Merge com dados do produto
        catalog = products_df.merge(product_stats, on='product_id', how='left')
        catalog = catalog.merge(product_reviews, on='product_id', how='left')
        
        # Preencher valores faltantes
        catalog['avg_price'] = catalog['avg_price'].fillna(0)
        catalog['order_count'] = catalog['order_count'].fillna(0)
        catalog['avg_rating'] = catalog['avg_rating'].fillna(3.0)
        catalog['review_count'] = catalog['review_count'].fillna(0)
        
        # Limpar valores NaN antes de conversões
        catalog = catalog.fillna({
            'order_count': 0,
            'avg_price': 0,
            'avg_rating': 3.0,
            'review_count': 0,
            'product_weight_g': 0,
            'product_length_cm': 0,
            'product_height_cm': 0,
            'product_width_cm': 0
        })
        
        # Simular dados de estoque e margem (dados fictícios)
        catalog['stock_quantity'] = (catalog['order_count'] * 10).astype(int)
        catalog['in_stock'] = catalog['stock_quantity'] > 0
        catalog['margin'] = (catalog['avg_price'] * 0.3).round(2)  # 30% de margem fictícia
        catalog['is_active'] = True
        catalog['created_at'] = datetime.now().isoformat()
        catalog['updated_at'] = datetime.now().isoformat()
        
        # Traduzir categorias se disponível
        try:
            translation_df = pd.read_csv(self.data_path / "product_category_name_translation.csv")
            catalog = catalog.merge(
                translation_df.rename(columns={'product_category_name_english': 'category_english'}),
                left_on='product_category_name',
                right_on='product_category_name',
                how='left'
            )
            catalog['category'] = catalog['category_english'].fillna(catalog['product_category_name'])
        except FileNotFoundError:
            catalog['category'] = catalog['product_category_name']
            
        print(f"[BATCH] Catálogo carregado com {len(catalog)} produtos")
        
        return catalog
        
    async def process_complementary_products(self):
        """Processa produtos complementares completo"""
        print("[BATCH] Iniciando processamento de produtos complementares...")
        
        try:
            # 1. Carregar dados de pedidos
            order_items = self.load_order_data()
            
            # 2. Treinar modelo de coocorrência
            print("[BATCH] Treinando modelo de coocorrência...")
            self.cooccurrence_model.fit(order_items, Config.BATCH_MIN_COOCCURRENCE)
            
            # 3. Gerar candidatos complementares
            print("[BATCH] Gerando candidatos complementares...")
            candidates = self.cooccurrence_model.get_all_complementary_candidates(
                min_lift=1.1,  # Lift > 1.1 indica correlação positiva
                min_npmi=0.1   # NPMI > 0.1 indica associação moderada
            )
            
            # 4. Limitar candidatos por produto (top 50)
            print("[BATCH] Filtrando top candidatos por produto...")
            candidates_by_product = {}
            for candidate in candidates:
                product_id = candidate['product_id']
                if product_id not in candidates_by_product:
                    candidates_by_product[product_id] = []
                candidates_by_product[product_id].append(candidate)
            
            # Ordenar e limitar
            final_candidates = []
            for product_id, product_candidates in candidates_by_product.items():
                # Ordenar por lift e NPMI
                sorted_candidates = sorted(
                    product_candidates,
                    key=lambda x: (x['lift_score'], x['npmi_score']),
                    reverse=True
                )
                final_candidates.extend(sorted_candidates[:Config.COMPLEMENTARY_PRODUCTS_LIMIT])
            
            # 5. Armazenar no PostgreSQL
            print(f"[BATCH] Armazenando {len(final_candidates)} candidatos no PostgreSQL...")
            await self.pg_service.store_complementary_candidates(final_candidates)
            
            # 6. Atualizar Elasticsearch com catálogo de produtos
            print("[BATCH] Atualizando Elasticsearch...")
            catalog = self.load_product_catalog()
            
            # Converter para formato adequado para ES
            es_products = []
            for _, product in catalog.iterrows():
                # Conversão mais segura de tipos
                def safe_int(value, default=0):
                    try:
                        return int(float(value)) if pd.notna(value) else default
                    except (ValueError, TypeError):
                        return default
                
                def safe_float(value, default=0.0):
                    try:
                        return float(value) if pd.notna(value) else default
                    except (ValueError, TypeError):
                        return default
                        
                es_product = {
                    'product_id': str(product['product_id']),
                    'product_name': str(product.get('product_name_lenght', 'Produto sem nome')),
                    'category': str(product['category']),
                    'subcategory': str(product.get('product_category_name', '')),
                    'brand': 'Generic',  # Não disponível nos dados Olist
                    'price': safe_float(product['avg_price']),
                    'margin': safe_float(product['margin']),
                    'stock_quantity': safe_int(product['stock_quantity']),
                    'in_stock': bool(product['in_stock']),
                    'weight_g': safe_int(product.get('product_weight_g', 0)),
                    'length_cm': safe_int(product.get('product_length_cm', 0)),
                    'height_cm': safe_int(product.get('product_height_cm', 0)),
                    'width_cm': safe_int(product.get('product_width_cm', 0)),
                    'description': f"Produto da categoria {product['category']}",
                    'tags': [str(product['category'])],
                    'seller_id': 'unknown',
                    'avg_rating': safe_float(product['avg_rating'], 3.0),
                    'review_count': safe_int(product['review_count']),
                    'created_at': str(product['created_at']),
                    'updated_at': str(product['updated_at']),
                    'is_active': bool(product['is_active'])
                }
                es_products.append(es_product)
            
            # Indexar em lotes
            batch_size = 1000
            for i in range(0, len(es_products), batch_size):
                batch = es_products[i:i + batch_size]
                self.es_service.index_products(batch)
                print(f"[BATCH] Indexados {min(i + batch_size, len(es_products))}/{len(es_products)} produtos")
            
            # 7. Salvar modelo
            model_path = "models/cooccurrence_model.pkl"
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            self.cooccurrence_model.save_model(model_path)
            
            print("[BATCH] Processamento concluído com sucesso!")
            
            return {
                'status': 'success',
                'total_candidates': len(final_candidates),
                'unique_products': len(candidates_by_product),
                'es_products_indexed': len(es_products),
                'model_stats': self.cooccurrence_model.get_model_stats()
            }
            
        except Exception as e:
            print(f"[BATCH] Erro no processamento: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def run_daily_update(self):
        """Executa atualização diária (versão simplificada)"""
        print("[BATCH] Executando atualização diária...")
        
        try:
            # Processar apenas últimos 7 dias para atualização incremental
            order_items = self.load_order_data(months_back=1)  # Último mês para contexto
            
            # Re-treinar modelo
            self.cooccurrence_model.fit(order_items, Config.BATCH_MIN_COOCCURRENCE)
            
            # Gerar e armazenar novos candidatos
            candidates = self.cooccurrence_model.get_all_complementary_candidates(
                min_lift=1.1,
                min_npmi=0.1
            )
            
            # Filtrar e armazenar
            candidates_by_product = {}
            for candidate in candidates:
                product_id = candidate['product_id']
                if product_id not in candidates_by_product:
                    candidates_by_product[product_id] = []
                candidates_by_product[product_id].append(candidate)
            
            final_candidates = []
            for product_id, product_candidates in candidates_by_product.items():
                sorted_candidates = sorted(
                    product_candidates,
                    key=lambda x: (x['lift_score'], x['npmi_score']),
                    reverse=True
                )
                final_candidates.extend(sorted_candidates[:Config.COMPLEMENTARY_PRODUCTS_LIMIT])
            
            await self.pg_service.store_complementary_candidates(final_candidates)
            
            print(f"[BATCH] Atualização diária concluída: {len(final_candidates)} candidatos atualizados")
            
            return {
                'status': 'success',
                'updated_candidates': len(final_candidates)
            }
            
        except Exception as e:
            print(f"[BATCH] Erro na atualização diária: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


async def main():
    """Função principal para execução standalone"""
    processor = BatchProcessor()
    
    try:
        await processor.initialize()
        result = await processor.process_complementary_products()
        print(f"[BATCH] Resultado final: {result}")
        
    finally:
        await processor.close()


if __name__ == "__main__":
    asyncio.run(main())