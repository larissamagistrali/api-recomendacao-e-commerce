import asyncpg
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from config import Config

class PostgreSQLService:
    """Serviço PostgreSQL para armazenar candidatos complementares e logs de atribuição"""
    
    def __init__(self):
        self.connection_string = f"postgresql://{Config.POSTGRES_USERNAME}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DATABASE}"
        self.pool = None
        self.is_available = False
        
    async def initialize(self):
        """Inicializa o pool de conexões e cria as tabelas"""
        try:
            self.pool = await asyncpg.create_pool(self.connection_string)
            await self._create_tables()
            self.is_available = True
            print(f"[POSTGRESQL] Conectado ao PostgreSQL em {Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}")
        except Exception as e:
            print(f"[POSTGRESQL] AVISO: Não foi possível conectar ao PostgreSQL: {e}")
            print("[POSTGRESQL] Funcionalidades de log serão desabilitadas")
            self.is_available = False
        
    async def close(self):
        """Fecha o pool de conexões"""
        if self.pool:
            await self.pool.close()
            
    async def _create_tables(self):
        """Cria as tabelas necessárias se não existirem"""
        async with self.pool.acquire() as conn:
            # Tabela para candidatos complementares
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS complementary_candidates (
                    id SERIAL PRIMARY KEY,
                    product_id VARCHAR(255) NOT NULL,
                    complementary_product_id VARCHAR(255) NOT NULL,
                    lift_score DECIMAL(10, 6),
                    npmi_score DECIMAL(10, 6),
                    cooccurrence_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(product_id, complementary_product_id)
                );
            """)
            
            # Índices para performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_complementary_product_id 
                ON complementary_candidates(product_id);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_complementary_lift_score 
                ON complementary_candidates(product_id, lift_score DESC);
            """)
            
            # Tabela para conjuntos de recomendações (rec_sets)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS rec_sets (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255),
                    user_id VARCHAR(255),
                    context_product_id VARCHAR(255),
                    context_type VARCHAR(50), -- 'PDP' ou 'CART'
                    recommended_products JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Tabela para resultados das recomendações (rec_outcomes)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS rec_outcomes (
                    id SERIAL PRIMARY KEY,
                    rec_set_id INTEGER REFERENCES rec_sets(id),
                    recommended_product_id VARCHAR(255),
                    outcome_type VARCHAR(50), -- 'view', 'add_to_cart', 'purchase'
                    outcome_value DECIMAL(10, 2), -- valor da compra se aplicável
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Índices para análise
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rec_sets_context 
                ON rec_sets(context_product_id, context_type);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rec_outcomes_rec_set 
                ON rec_outcomes(rec_set_id, outcome_type);
            """)
            
    async def store_complementary_candidates(self, candidates: List[Dict[str, Any]]):
        """Armazena ou atualiza candidatos complementares"""
        if not self.is_available:
            print("[POSTGRESQL] Serviço não disponível - pulando armazenamento")
            return
            
        async with self.pool.acquire() as conn:
            # Preparar dados para inserção em lote
            values = [
                (
                    candidate['product_id'],
                    candidate['complementary_product_id'],
                    candidate['lift_score'],
                    candidate['npmi_score'],
                    candidate['cooccurrence_count']
                )
                for candidate in candidates
            ]
            
            # Usar UPSERT para atualizar registros existentes
            await conn.executemany("""
                INSERT INTO complementary_candidates 
                (product_id, complementary_product_id, lift_score, npmi_score, cooccurrence_count, updated_at)
                VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                ON CONFLICT (product_id, complementary_product_id)
                DO UPDATE SET 
                    lift_score = EXCLUDED.lift_score,
                    npmi_score = EXCLUDED.npmi_score,
                    cooccurrence_count = EXCLUDED.cooccurrence_count,
                    updated_at = CURRENT_TIMESTAMP
            """, values)
            
    async def get_complementary_products(
        self, 
        product_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Busca produtos complementares para um produto específico"""
        if not self.is_available:
            print("[POSTGRESQL] Serviço não disponível - retornando lista vazia")
            return []
            
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    complementary_product_id,
                    lift_score,
                    npmi_score,
                    cooccurrence_count
                FROM complementary_candidates
                WHERE product_id = $1
                ORDER BY lift_score DESC, npmi_score DESC
                LIMIT $2
            """, product_id, limit)
            
            return [
                {
                    'product_id': row['complementary_product_id'],
                    'lift_score': float(row['lift_score']),
                    'npmi_score': float(row['npmi_score']),
                    'cooccurrence_count': row['cooccurrence_count']
                }
                for row in rows
            ]
            
    async def log_recommendation_set(
        self,
        session_id: str,
        user_id: Optional[str],
        context_product_id: str,
        context_type: str,
        recommended_products: List[Dict[str, Any]]
    ) -> int:
        """Registra um conjunto de recomendações mostrado ao usuário"""
        async with self.pool.acquire() as conn:
            rec_set_id = await conn.fetchval("""
                INSERT INTO rec_sets 
                (session_id, user_id, context_product_id, context_type, recommended_products)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, session_id, user_id, context_product_id, context_type, json.dumps(recommended_products))
            
            return rec_set_id
            
    async def log_recommendation_outcome(
        self,
        rec_set_id: int,
        recommended_product_id: str,
        outcome_type: str,
        outcome_value: float = None
    ):
        """Registra o resultado de uma recomendação"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO rec_outcomes 
                (rec_set_id, recommended_product_id, outcome_type, outcome_value)
                VALUES ($1, $2, $3, $4)
            """, rec_set_id, recommended_product_id, outcome_type, outcome_value)
            
    async def get_recommendation_performance(
        self,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Analisa a performance das recomendações nos últimos N dias"""
        async with self.pool.acquire() as conn:
            since_date = datetime.now() - timedelta(days=days_back)
            
            # Métricas gerais
            metrics = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT rs.id) as total_rec_sets,
                    COUNT(ro.id) as total_outcomes,
                    COUNT(CASE WHEN ro.outcome_type = 'add_to_cart' THEN 1 END) as add_to_cart_count,
                    COUNT(CASE WHEN ro.outcome_type = 'purchase' THEN 1 END) as purchase_count,
                    AVG(CASE WHEN ro.outcome_type = 'purchase' THEN ro.outcome_value END) as avg_purchase_value
                FROM rec_sets rs
                LEFT JOIN rec_outcomes ro ON rs.id = ro.rec_set_id
                WHERE rs.created_at >= $1
            """, since_date)
            
            # Performance por contexto
            context_performance = await conn.fetch("""
                SELECT 
                    rs.context_type,
                    COUNT(DISTINCT rs.id) as rec_sets_count,
                    COUNT(CASE WHEN ro.outcome_type = 'add_to_cart' THEN 1 END) as add_to_cart_count,
                    COUNT(CASE WHEN ro.outcome_type = 'purchase' THEN 1 END) as purchase_count
                FROM rec_sets rs
                LEFT JOIN rec_outcomes ro ON rs.id = ro.rec_set_id
                WHERE rs.created_at >= $1
                GROUP BY rs.context_type
            """, since_date)
            
            return {
                'period_days': days_back,
                'total_recommendations_shown': metrics['total_rec_sets'],
                'total_interactions': metrics['total_outcomes'],
                'add_to_cart_count': metrics['add_to_cart_count'],
                'purchase_count': metrics['purchase_count'],
                'avg_purchase_value': float(metrics['avg_purchase_value']) if metrics['avg_purchase_value'] else 0,
                'context_performance': [
                    {
                        'context': row['context_type'],
                        'recommendations_shown': row['rec_sets_count'],
                        'add_to_cart_rate': row['add_to_cart_count'] / row['rec_sets_count'] if row['rec_sets_count'] > 0 else 0,
                        'purchase_rate': row['purchase_count'] / row['rec_sets_count'] if row['rec_sets_count'] > 0 else 0
                    }
                    for row in context_performance
                ]
            }