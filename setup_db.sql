-- Criação das tabelas para o sistema de produtos complementares

-- Tabela para armazenar candidatos complementares (resultado do processamento batch)
CREATE TABLE IF NOT EXISTS complementary_candidates (
    id SERIAL PRIMARY KEY,
    product_a VARCHAR(255) NOT NULL,
    product_b VARCHAR(255) NOT NULL,
    lift_score DECIMAL(10,4),
    npmi_score DECIMAL(10,4),
    cooccurrence_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para armazenar conjuntos de recomendações exibidas
CREATE TABLE IF NOT EXISTS rec_sets (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    product_id VARCHAR(255) NOT NULL,
    context_type VARCHAR(50) NOT NULL,
    recommendations JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para armazenar resultados das recomendações (cliques, compras, etc.)
CREATE TABLE IF NOT EXISTS rec_outcomes (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    product_id VARCHAR(255) NOT NULL,
    recommended_product_id VARCHAR(255) NOT NULL,
    outcome_type VARCHAR(50) NOT NULL, -- 'click', 'purchase', 'view', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_complementary_product_a ON complementary_candidates(product_a);
CREATE INDEX IF NOT EXISTS idx_complementary_product_b ON complementary_candidates(product_b);
CREATE INDEX IF NOT EXISTS idx_complementary_scores ON complementary_candidates(lift_score DESC, npmi_score DESC);
CREATE INDEX IF NOT EXISTS idx_rec_sets_session ON rec_sets(session_id);
CREATE INDEX IF NOT EXISTS idx_rec_sets_product ON rec_sets(product_id);
CREATE INDEX IF NOT EXISTS idx_rec_outcomes_session ON rec_outcomes(session_id);
CREATE INDEX IF NOT EXISTS idx_rec_outcomes_product ON rec_outcomes(product_id);
CREATE INDEX IF NOT EXISTS idx_rec_outcomes_recommended ON rec_outcomes(recommended_product_id);

-- Comentários nas tabelas
COMMENT ON TABLE complementary_candidates IS 'Armazena produtos complementares calculados via algoritmos de coocorrência';
COMMENT ON TABLE rec_sets IS 'Registra conjuntos de recomendações exibidas aos usuários';
COMMENT ON TABLE rec_outcomes IS 'Registra resultados das recomendações (cliques, compras, etc.)';