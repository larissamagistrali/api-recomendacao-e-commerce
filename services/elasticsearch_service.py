from elasticsearch import Elasticsearch
from typing import List, Dict, Any, Optional
from config import Config
import json

class ElasticsearchService:
    """Serviço Elasticsearch para busca rápida de produtos com filtros"""
    
    def __init__(self):
        # Configurar conexão com Elasticsearch
        es_config = {
            'hosts': [{'host': Config.ELASTICSEARCH_HOST, 'port': Config.ELASTICSEARCH_PORT}],
            'request_timeout': 30,
            'max_retries': 3,
            'retry_on_timeout': True
        }
        
        # Adicionar autenticação se configurada
        if Config.ELASTICSEARCH_USERNAME and Config.ELASTICSEARCH_PASSWORD:
            es_config['http_auth'] = (Config.ELASTICSEARCH_USERNAME, Config.ELASTICSEARCH_PASSWORD)
            
        # Configurar SSL se necessário
        if Config.ELASTICSEARCH_USE_SSL:
            es_config['use_ssl'] = True
            es_config['verify_certs'] = True
            
        try:
            self.es = Elasticsearch(**es_config)
            self.products_index = Config.ELASTICSEARCH_INDEX_PRODUCTS
            print(f"[ELASTICSEARCH] Conectado ao Elasticsearch em {Config.ELASTICSEARCH_HOST}:{Config.ELASTICSEARCH_PORT}")
        except Exception as e:
            print(f"[ELASTICSEARCH] AVISO: Não foi possível conectar ao Elasticsearch: {e}")
            print(f"[ELASTICSEARCH] Modo fallback ativado - algumas funcionalidades podem não funcionar")
            self.es = None
            self.products_index = Config.ELASTICSEARCH_INDEX_PRODUCTS
        
    def create_products_index(self):
        """Cria o índice de produtos com mapeamento otimizado"""
        if not self.es:
            print("[ELASTICSEARCH] Serviço não disponível - pulando criação de índice")
            return
            
        mapping = {
            "mappings": {
                "properties": {
                    "product_id": {"type": "keyword"},
                    "product_name": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "category": {"type": "keyword"},
                    "subcategory": {"type": "keyword"},
                    "brand": {"type": "keyword"},
                    "price": {"type": "float"},
                    "margin": {"type": "float"},
                    "stock_quantity": {"type": "integer"},
                    "in_stock": {"type": "boolean"},
                    "weight_g": {"type": "integer"},
                    "length_cm": {"type": "integer"},
                    "height_cm": {"type": "integer"},
                    "width_cm": {"type": "integer"},
                    "description": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "tags": {"type": "keyword"},
                    "seller_id": {"type": "keyword"},
                    "avg_rating": {"type": "float"},
                    "review_count": {"type": "integer"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "is_active": {"type": "boolean"}
                }
            }
        }
        
        try:
            if self.es.indices.exists(index=self.products_index):
                print(f"[ELASTICSEARCH] Índice {self.products_index} já existe")
                return
                
            self.es.indices.create(index=self.products_index, body=mapping)
            print(f"[ELASTICSEARCH] Índice {self.products_index} criado com sucesso")
        except Exception as e:
            print(f"[ELASTICSEARCH] Erro ao criar índice: {e}")
            
    def index_products(self, products: List[Dict[str, Any]]):
        """Indexa produtos em lote no Elasticsearch"""
        if not self.es:
            print("[ELASTICSEARCH] Serviço não disponível - pulando indexação")
            return
            
        if not products:
            return
            
        try:
            body = []
            for product in products:
                body.append({
                    "index": {
                        "_index": self.products_index,
                        "_id": product['product_id']
                    }
                })
                body.append(product)
                
            response = self.es.bulk(body=body)
            
            # Verificar erros
            if response['errors']:
                errors = [item for item in response['items'] if 'error' in item.get('index', {})]
                print(f"[ELASTICSEARCH] Erros ao indexar {len(errors)} produtos")
            else:
                print(f"[ELASTICSEARCH] {len(products)} produtos indexados com sucesso")
                
        except Exception as e:
            print(f"[ELASTICSEARCH] Erro ao indexar produtos: {e}")
            
    def search_products(
        self,
        product_ids: List[str],
        filters: Dict[str, Any] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Busca produtos por IDs com filtros aplicados"""
        if not self.es:
            print("[ELASTICSEARCH] Serviço não disponível - retornando lista vazia")
            return []
            
        if not product_ids:
            return []
            
        # Construir query base
        query = {
            "bool": {
                "must": [
                    {"terms": {"product_id": product_ids}},
                    {"term": {"is_active": True}}  # Apenas produtos ativos
                ]
            }
        }
        
        # Aplicar filtros
        if filters:
            # Filtro de estoque mínimo
            if filters.get('min_stock', 0) > 0:
                query["bool"]["must"].append({
                    "range": {"stock_quantity": {"gte": filters['min_stock']}}
                })
                
            # Filtro de categoria
            if filters.get('category'):
                query["bool"]["must"].append({
                    "term": {"category": filters['category']}
                })
                
            # Filtro de marca
            if filters.get('brand'):
                query["bool"]["must"].append({
                    "term": {"brand": filters['brand']}
                })
                
            # Filtro de faixa de preço
            if filters.get('min_price') or filters.get('max_price'):
                price_range = {}
                if filters.get('min_price'):
                    price_range['gte'] = filters['min_price']
                if filters.get('max_price'):
                    price_range['lte'] = filters['max_price']
                query["bool"]["must"].append({
                    "range": {"price": price_range}
                })
                
            # Filtro de avaliação mínima
            if filters.get('min_rating'):
                query["bool"]["must"].append({
                    "range": {"avg_rating": {"gte": filters['min_rating']}}
                })
                
        # Configurar ordenação (por relevância e margem)
        sort = [
            "_score",
            {"margin": {"order": "desc"}},
            {"avg_rating": {"order": "desc"}}
        ]
        
        try:
            response = self.es.search(
                index=self.products_index,
                body={
                    "query": query,
                    "sort": sort,
                    "size": limit,
                    "_source": True
                }
            )
            
            products = []
            for hit in response['hits']['hits']:
                product = hit['_source']
                product['_score'] = hit['_score']
                products.append(product)
                
            return products
            
        except Exception as e:
            print(f"[ELASTICSEARCH] Erro na busca de produtos: {e}")
            return []
            
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Busca um produto específico por ID"""
        try:
            response = self.es.get(
                index=self.products_index,
                id=product_id
            )
            return response['_source']
        except Exception as e:
            print(f"[ELASTICSEARCH] Produto {product_id} não encontrado: {e}")
            return None
            
    def update_product_stock(self, product_id: str, stock_quantity: int):
        """Atualiza o estoque de um produto"""
        try:
            self.es.update(
                index=self.products_index,
                id=product_id,
                body={
                    "doc": {
                        "stock_quantity": stock_quantity,
                        "in_stock": stock_quantity > 0,
                        "updated_at": "now"
                    }
                }
            )
        except Exception as e:
            print(f"[ELASTICSEARCH] Erro ao atualizar estoque do produto {product_id}: {e}")
            
    def search_similar_products(
        self,
        product_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Busca produtos similares usando More Like This"""
        try:
            response = self.es.search(
                index=self.products_index,
                body={
                    "query": {
                        "more_like_this": {
                            "fields": ["product_name", "description", "category"],
                            "like": [
                                {
                                    "_index": self.products_index,
                                    "_id": product_id
                                }
                            ],
                            "min_term_freq": 1,
                            "max_query_terms": 25
                        }
                    },
                    "size": limit
                }
            )
            
            products = []
            for hit in response['hits']['hits']:
                if hit['_id'] != product_id:  # Excluir o próprio produto
                    product = hit['_source']
                    product['similarity_score'] = hit['_score']
                    products.append(product)
                    
            return products
            
        except Exception as e:
            print(f"[ELASTICSEARCH] Erro na busca de produtos similares: {e}")
            return []
            
    def get_category_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas por categoria"""
        try:
            response = self.es.search(
                index=self.products_index,
                body={
                    "size": 0,
                    "aggs": {
                        "categories": {
                            "terms": {
                                "field": "category",
                                "size": 50
                            },
                            "aggs": {
                                "avg_price": {"avg": {"field": "price"}},
                                "total_stock": {"sum": {"field": "stock_quantity"}},
                                "avg_rating": {"avg": {"field": "avg_rating"}}
                            }
                        }
                    }
                }
            )
            
            categories = []
            for bucket in response['aggregations']['categories']['buckets']:
                categories.append({
                    'category': bucket['key'],
                    'product_count': bucket['doc_count'],
                    'avg_price': bucket['avg_price']['value'],
                    'total_stock': bucket['total_stock']['value'],
                    'avg_rating': bucket['avg_rating']['value']
                })
                
            return {'categories': categories}
            
        except Exception as e:
            print(f"[ELASTICSEARCH] Erro ao obter estatísticas de categoria: {e}")
            return {}
            
    def health_check(self) -> Dict[str, Any]:
        """Verifica a saúde do cluster Elasticsearch"""
        if not self.es:
            return {'error': 'Elasticsearch não configurado', 'status': 'unavailable'}
            
        try:
            health = self.es.cluster.health()
            return {
                'status': health['status'],
                'cluster_name': health['cluster_name'],
                'number_of_nodes': health['number_of_nodes'],
                'active_primary_shards': health['active_primary_shards'],
                'active_shards': health['active_shards'],
                'relocating_shards': health['relocating_shards'],
                'initializing_shards': health['initializing_shards'],
                'unassigned_shards': health['unassigned_shards']
            }
        except Exception as e:
            return {'error': str(e), 'status': 'unavailable'}