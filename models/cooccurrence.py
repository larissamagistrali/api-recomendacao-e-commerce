import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from itertools import combinations
from math import log
import warnings
warnings.filterwarnings('ignore')

class CooccurrenceModel:
    """Modelo para calcular coocorrência, lift e NPMI entre produtos"""
    
    def __init__(self):
        self.cooccurrence_matrix = None
        self.product_counts = None
        self.total_orders = 0
        
    def fit(self, order_items_df: pd.DataFrame, min_cooccurrence: int = 5):
        """
        Treina o modelo com dados de itens de pedidos
        
        Args:
            order_items_df: DataFrame com colunas ['order_id', 'product_id']
            min_cooccurrence: Número mínimo de coocorrências para considerar um par
        """
        print(f"[COOCCURRENCE] Iniciando treinamento com {len(order_items_df)} itens")
        
        # Agrupar produtos por pedido
        orders_products = order_items_df.groupby('order_id')['product_id'].apply(list).reset_index()
        
        # Contar ocorrências individuais de produtos
        self.product_counts = order_items_df['product_id'].value_counts().to_dict()
        self.total_orders = orders_products['order_id'].nunique()
        
        print(f"[COOCCURRENCE] {len(self.product_counts)} produtos únicos em {self.total_orders} pedidos")
        
        # Calcular coocorrências
        cooccurrences = {}
        
        for _, row in orders_products.iterrows():
            products = row['product_id']
            
            # Gerar pares de produtos do mesmo pedido
            if len(products) > 1:
                for product_a, product_b in combinations(products, 2):
                    # Ordenar para manter consistência
                    pair = tuple(sorted([product_a, product_b]))
                    cooccurrences[pair] = cooccurrences.get(pair, 0) + 1
        
        # Filtrar pares com coocorrência mínima
        self.cooccurrence_matrix = {
            pair: count for pair, count in cooccurrences.items() 
            if count >= min_cooccurrence
        }
        
        print(f"[COOCCURRENCE] {len(self.cooccurrence_matrix)} pares de produtos com coocorrência >= {min_cooccurrence}")
        
    def calculate_lift_and_npmi(self, product_a: str, product_b: str) -> Tuple[float, float]:
        """
        Calcula lift e NPMI para um par de produtos
        
        Returns:
            Tuple[lift, npmi]
        """
        pair = tuple(sorted([product_a, product_b]))
        
        # Verificar se o par existe na matriz de coocorrência
        if pair not in self.cooccurrence_matrix:
            return 0.0, 0.0
            
        # Obter contagens
        cooccurrence_count = self.cooccurrence_matrix[pair]
        count_a = self.product_counts.get(product_a, 0)
        count_b = self.product_counts.get(product_b, 0)
        
        if count_a == 0 or count_b == 0 or self.total_orders == 0:
            return 0.0, 0.0
            
        # Calcular probabilidades
        p_a = count_a / self.total_orders
        p_b = count_b / self.total_orders
        p_ab = cooccurrence_count / self.total_orders
        
        # Calcular Lift: P(A,B) / (P(A) * P(B))
        lift = p_ab / (p_a * p_b) if (p_a * p_b) > 0 else 0.0
        
        # Calcular NPMI: PMI / -log(P(A,B))
        if p_ab > 0:
            pmi = log(p_ab / (p_a * p_b)) if (p_a * p_b) > 0 else 0.0
            npmi = pmi / (-log(p_ab)) if p_ab > 0 else 0.0
        else:
            npmi = 0.0
            
        return lift, npmi
        
    def get_complementary_products(
        self, 
        product_id: str, 
        min_lift: float = 1.0,
        min_npmi: float = 0.0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retorna produtos complementares para um produto específico
        
        Args:
            product_id: ID do produto
            min_lift: Lift mínimo para considerar complementar
            min_npmi: NPMI mínimo para considerar complementar
            limit: Número máximo de produtos a retornar
        """
        if product_id not in self.product_counts:
            return []
            
        complementary = []
        
        # Buscar todos os pares que incluem o produto
        for pair, cooccurrence_count in self.cooccurrence_matrix.items():
            if product_id in pair:
                # Identificar o produto complementar
                other_product = pair[1] if pair[0] == product_id else pair[0]
                
                # Calcular métricas
                lift, npmi = self.calculate_lift_and_npmi(product_id, other_product)
                
                # Aplicar filtros
                if lift >= min_lift and npmi >= min_npmi:
                    complementary.append({
                        'product_id': product_id,
                        'complementary_product_id': other_product,
                        'lift_score': lift,
                        'npmi_score': npmi,
                        'cooccurrence_count': cooccurrence_count
                    })
        
        # Ordenar por lift (descendente) e depois por NPMI (descendente)
        complementary.sort(key=lambda x: (x['lift_score'], x['npmi_score']), reverse=True)
        
        return complementary[:limit]
        
    def get_all_complementary_candidates(
        self,
        min_lift: float = 1.0,
        min_npmi: float = 0.0,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Gera todos os candidatos complementares para processamento em lote
        
        Returns:
            Lista de candidatos complementares
        """
        all_candidates = []
        processed = 0
        
        print("[COOCCURRENCE] Gerando candidatos complementares...")
        
        for pair, cooccurrence_count in self.cooccurrence_matrix.items():
            product_a, product_b = pair
            
            # Calcular métricas
            lift, npmi = self.calculate_lift_and_npmi(product_a, product_b)
            
            # Aplicar filtros
            if lift >= min_lift and npmi >= min_npmi:
                # Adicionar ambas as direções (A->B e B->A)
                all_candidates.extend([
                    {
                        'product_id': product_a,
                        'complementary_product_id': product_b,
                        'lift_score': lift,
                        'npmi_score': npmi,
                        'cooccurrence_count': cooccurrence_count
                    },
                    {
                        'product_id': product_b,
                        'complementary_product_id': product_a,
                        'lift_score': lift,
                        'npmi_score': npmi,
                        'cooccurrence_count': cooccurrence_count
                    }
                ])
            
            processed += 1
            if processed % batch_size == 0:
                print(f"[COOCCURRENCE] Processados {processed}/{len(self.cooccurrence_matrix)} pares")
        
        print(f"[COOCCURRENCE] Gerados {len(all_candidates)} candidatos complementares")
        return all_candidates
        
    def get_model_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do modelo"""
        if not self.cooccurrence_matrix:
            return {'error': 'Modelo não treinado'}
            
        # Calcular estatísticas de lift e NPMI
        all_lifts = []
        all_npmis = []
        
        sample_pairs = list(self.cooccurrence_matrix.items())[:1000]  # Amostra para performance
        
        for pair, _ in sample_pairs:
            product_a, product_b = pair
            lift, npmi = self.calculate_lift_and_npmi(product_a, product_b)
            all_lifts.append(lift)
            all_npmis.append(npmi)
            
        return {
            'total_products': len(self.product_counts),
            'total_orders': self.total_orders,
            'total_pairs': len(self.cooccurrence_matrix),
            'avg_lift': np.mean(all_lifts) if all_lifts else 0,
            'median_lift': np.median(all_lifts) if all_lifts else 0,
            'avg_npmi': np.mean(all_npmis) if all_npmis else 0,
            'median_npmi': np.median(all_npmis) if all_npmis else 0,
            'top_products_by_frequency': list(
                sorted(self.product_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            )
        }
        
    def save_model(self, filepath: str):
        """Salva o modelo treinado"""
        import pickle
        
        model_data = {
            'cooccurrence_matrix': self.cooccurrence_matrix,
            'product_counts': self.product_counts,
            'total_orders': self.total_orders
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
            
        print(f"[COOCCURRENCE] Modelo salvo em {filepath}")
        
    def load_model(self, filepath: str):
        """Carrega um modelo salvo"""
        import pickle
        
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
            
        self.cooccurrence_matrix = model_data['cooccurrence_matrix']
        self.product_counts = model_data['product_counts']
        self.total_orders = model_data['total_orders']
        
        print(f"[COOCCURRENCE] Modelo carregado de {filepath}")