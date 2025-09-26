-- Tabela para matriz de similaridade entre produtos
drop table if exists public.item_similarity;
CREATE TABLE public.item_similarity (
    product_id VARCHAR PRIMARY KEY
);