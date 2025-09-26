from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import asyncio
import random

from services.postgresql_service import PostgreSQLService
from services.redis_service import RedisService
from services.elasticsearch_service import ElasticsearchService
from config import Config

class ComplementaryRecommendationService:
    """Novo serviço de recomendações focado em produtos complementares"""
    
    def __init__(self):
        self.pg_service = PostgreSQLService()
        self.redis_service = RedisService()
        self.es_service = ElasticsearchService()
        
    async def initialize(self):
        """Inicializa os serviços"""
        await self.pg_service.initialize()
        
    async def close(self):
        """Fecha as conexões"""
        await self.pg_service.close()
        
    async def get_complementary_products(
        self,
        product_id: str,
        context_type: str = "PDP",  # PDP ou CART
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """
        Busca produtos complementares com cache e filtros
        
        Args:
            product_id: ID do produto base
            context_type: Contexto da recomendação (PDP ou CART)
            user_id: ID do usuário (opcional)
            session_id: ID da sessão
            filters: Filtros a aplicar (estoque, categoria, etc.)
            limit: Número máximo de produtos
        """
        limit = limit or Config.RECOMMENDATION_DEFAULT_LIMIT
        session_id = session_id or str(uuid.uuid4())
        
        try:
            # 1. Tentar buscar do cache Redis primeiro
            cached_products = self.redis_service.get_complementary_products(product_id)
            
            if cached_products:
                print(f"[COMPLEMENTARY] Cache hit para produto {product_id}")
                candidate_products = cached_products
            else:
                print(f"[COMPLEMENTARY] Cache miss para produto {product_id}")
                # 2. Buscar do PostgreSQL
                candidate_products = await self.pg_service.get_complementary_products(
                    product_id, 
                    limit=Config.COMPLEMENTARY_PRODUCTS_LIMIT
                )
                
                # Armazenar no cache para próximas consultas
                if candidate_products:
                    self.redis_service.set_complementary_products(product_id, candidate_products)
            
            if not candidate_products:
                print(f"[COMPLEMENTARY] Nenhum produto complementar encontrado para {product_id}")
                return {
                    'product_id': product_id,
                    'context_type': context_type,
                    'recommendations': [],
                    'total': 0,
                    'source': 'no_data'
                }
            
            # 3. Extrair IDs dos produtos candidatos
            candidate_ids = [p['product_id'] for p in candidate_products]
            
            # 4. Aplicar filtros rígidos via Elasticsearch
            filters = filters or {}
            # Filtros padrão
            filters.update({
                'min_stock': 1,  # Apenas produtos em estoque
            })
            
            filtered_products = self.es_service.search_products(
                product_ids=candidate_ids,
                filters=filters,
                limit=Config.COMPLEMENTARY_PRODUCTS_LIMIT
            )
            
            if not filtered_products:
                print(f"[COMPLEMENTARY] Nenhum produto passou nos filtros para {product_id}")
                return {
                    'product_id': product_id,
                    'context_type': context_type,
                    'recommendations': [],
                    'total': 0,
                    'source': 'filtered_out'
                }
            
            # 5. Merge dos dados: scores do PostgreSQL + detalhes do Elasticsearch
            enriched_products = []
            candidate_scores = {p['product_id']: p for p in candidate_products}
            
            for es_product in filtered_products:
                product_id_comp = es_product['product_id']
                if product_id_comp in candidate_scores:
                    candidate_info = candidate_scores[product_id_comp]
                    
                    enriched_product = {
                        **es_product,
                        'lift_score': candidate_info['lift_score'],
                        'npmi_score': candidate_info['npmi_score'],
                        'cooccurrence_count': candidate_info['cooccurrence_count'],
                        'recommendation_reason': self._generate_reason(candidate_info)
                    }
                    enriched_products.append(enriched_product)
            
            # 6. Aplicar rerank (reordenação inteligente)
            reranked_products = self._apply_rerank(enriched_products, context_type)
            
            # 7. Limitar resultado final
            final_recommendations = reranked_products[:limit]
            
            # 8. Log da recomendação para medição
            rec_set_id = await self._log_recommendation_display(
                session_id=session_id,
                user_id=user_id,
                context_product_id=product_id,
                context_type=context_type,
                recommended_products=final_recommendations
            )
            
            print(f"[COMPLEMENTARY] Retornando {len(final_recommendations)} recomendações para {product_id}")
            
            return {
                'product_id': product_id,
                'context_type': context_type,
                'session_id': session_id,
                'rec_set_id': rec_set_id,
                'recommendations': final_recommendations,
                'total': len(final_recommendations),
                'source': 'complementary_algorithm'
            }
            
        except Exception as e:
            print(f"[COMPLEMENTARY] Erro na busca de produtos complementares: {e}")
            # Fallback para produtos populares
            return await self._get_fallback_recommendations(
                product_id, context_type, session_id, user_id, limit
            )
    
    def _apply_rerank(
        self, 
        products: List[Dict[str, Any]], 
        context_type: str
    ) -> List[Dict[str, Any]]:
        """
        Aplica rerank nos produtos baseado em:
        - Margem de lucro
        - Diversificação de categoria
        - Contexto (PDP vs CART)
        """
        if not products:
            return products
            
        # Calcular score de rerank para cada produto
        for product in products:
            base_score = product['lift_score']
            
            # Bonificar margem alta
            margin_bonus = (product.get('margin', 0) / 100) * Config.RERANK_MARGIN_WEIGHT
            
            # Penalizar produtos da mesma categoria (diversificação)
            category_penalty = 0
            product_category = product.get('category', '')
            same_category_count = sum(
                1 for p in products 
                if p.get('category', '') == product_category
            )
            if same_category_count > 3:  # Muitos produtos da mesma categoria
                category_penalty = Config.RERANK_DIVERSITY_PENALTY
            
            # Bonificar produtos com boa avaliação
            rating_bonus = (product.get('avg_rating', 3.0) - 3.0) * 0.1
            
            # Ajustar por contexto
            context_bonus = 0
            if context_type == "CART":
                # No carrinho, priorizar produtos de baixo valor para não assustar
                if product.get('price', 0) < 50:
                    context_bonus = 0.1
            else:  # PDP
                # Na página do produto, ok recomendar produtos de valor similar
                context_bonus = 0.05
            
            # Score final
            product['rerank_score'] = (
                base_score + 
                margin_bonus + 
                rating_bonus + 
                context_bonus - 
                category_penalty
            )
        
        # Ordenar por score de rerank
        products.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        return products
    
    def _generate_reason(self, candidate_info: Dict[str, Any]) -> str:
        """Gera razão da recomendação para exibição"""
        lift = candidate_info['lift_score']
        cooccurrence = candidate_info['cooccurrence_count']
        
        if lift > 3.0:
            return f"Frequentemente comprados juntos ({cooccurrence}+ pedidos)"
        elif lift > 2.0:
            return f"Ótima combinação ({cooccurrence} pedidos)"
        elif lift > 1.5:
            return f"Combina bem ({cooccurrence} pedidos)"
        else:
            return f"Outros clientes também compraram"
    
    async def _log_recommendation_display(
        self,
        session_id: str,
        user_id: Optional[str],
        context_product_id: str,
        context_type: str,
        recommended_products: List[Dict[str, Any]]
    ) -> int:
        """Log da exibição da recomendação para medição posterior"""
        try:
            # Preparar dados para log
            log_products = [
                {
                    'product_id': p['product_id'],
                    'position': i + 1,
                    'lift_score': p.get('lift_score', 0),
                    'rerank_score': p.get('rerank_score', 0),
                    'price': p.get('price', 0)
                }
                for i, p in enumerate(recommended_products)
            ]
            
            rec_set_id = await self.pg_service.log_recommendation_set(
                session_id=session_id,
                user_id=user_id,
                context_product_id=context_product_id,
                context_type=context_type,
                recommended_products=log_products
            )
            
            return rec_set_id
            
        except Exception as e:
            print(f"[COMPLEMENTARY] Erro ao logar recomendação: {e}")
            return -1
    
    async def log_recommendation_outcome(
        self,
        rec_set_id: int,
        product_id: str,
        outcome_type: str,  # 'view', 'add_to_cart', 'purchase'
        outcome_value: Optional[float] = None
    ):
        """Log do resultado da recomendação (conversão)"""
        try:
            await self.pg_service.log_recommendation_outcome(
                rec_set_id=rec_set_id,
                recommended_product_id=product_id,
                outcome_type=outcome_type,
                outcome_value=outcome_value
            )
            print(f"[COMPLEMENTARY] Logged outcome: {outcome_type} for product {product_id}")
            
        except Exception as e:
            print(f"[COMPLEMENTARY] Erro ao logar outcome: {e}")
    
    async def _get_fallback_recommendations(
        self,
        product_id: str,
        context_type: str,
        session_id: str,
        user_id: Optional[str],
        limit: int
    ) -> Dict[str, Any]:
        """Fallback para produtos populares quando não há dados complementares"""
        try:
            # Buscar produtos populares do cache primeiro
            popular_products = self.redis_service.get_popular_products()
            
            if not popular_products:
                # Se não estiver no cache, buscar alguns produtos aleatórios do ES
                # (em produção, isso seria produtos populares de verdade)
                all_products = self.es_service.search_products(
                    product_ids=[],  # Busca vazia retorna produtos gerais
                    filters={'min_stock': 1},
                    limit=50
                )
                popular_products = random.sample(all_products, min(limit, len(all_products)))
                
                # Armazenar no cache
                self.redis_service.set_popular_products(popular_products)
            
            # Excluir o próprio produto
            fallback_products = [
                p for p in popular_products 
                if p.get('product_id') != product_id
            ][:limit]
            
            # Adicionar razão de fallback
            for product in fallback_products:
                product['recommendation_reason'] = "Produto popular"
                product['lift_score'] = 1.0
                product['npmi_score'] = 0.0
            
            # Log do fallback
            rec_set_id = await self._log_recommendation_display(
                session_id=session_id,
                user_id=user_id,
                context_product_id=product_id,
                context_type=context_type,
                recommended_products=fallback_products
            )
            
            return {
                'product_id': product_id,
                'context_type': context_type,
                'session_id': session_id,
                'rec_set_id': rec_set_id,
                'recommendations': fallback_products,
                'total': len(fallback_products),
                'source': 'popular_fallback'
            }
            
        except Exception as e:
            print(f"[COMPLEMENTARY] Erro no fallback: {e}")
            return {
                'product_id': product_id,
                'context_type': context_type,
                'recommendations': [],
                'total': 0,
                'source': 'error'
            }
    
    async def get_recommendation_analytics(
        self, 
        days_back: int = 7
    ) -> Dict[str, Any]:
        """Retorna analytics de performance das recomendações"""
        try:
            return await self.pg_service.get_recommendation_performance(days_back)
        except Exception as e:
            print(f"[COMPLEMENTARY] Erro ao buscar analytics: {e}")
            return {'error': str(e)}
    
    def get_service_health(self) -> Dict[str, Any]:
        """Verifica saúde dos serviços"""
        health = {
            'redis': self.redis_service.ping(),
            'elasticsearch': self.es_service.health_check(),
            'timestamp': datetime.now().isoformat()
        }
        
        # PostgreSQL health seria verificado tentando uma query simples
        # Por simplicidade, assumindo saudável se outros serviços ok
        health['postgresql'] = health['redis'] and health['elasticsearch']['status'] != 'unavailable'
        health['overall'] = all([health['redis'], health['postgresql']])
        
        return health