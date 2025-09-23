import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class ContentBasedModel:
    """Modelo de filtragem baseada em conteúdo para recomendações"""
    
    def __init__(self, features_columns: List[str] = None):
        """
        Inicializa o modelo de filtragem baseada em conteúdo
        
        Args:
            features_columns: Lista de colunas de características dos itens
        """
        self.features_columns = features_columns or []
        self.item_features = None
        self.similarity_matrix = None
        self.tfidf_vectorizer = None
        self.is_fitted = False
    
    def fit(self, item_features: pd.DataFrame) -> 'ContentBasedModel':
        """
        Treina o modelo com as características dos itens
        
        Args:
            item_features: DataFrame com características dos itens
        """
        try:
            self.item_features = item_features.copy()
            
            # Preparar features para cálculo de similaridade
            if self.features_columns:
                features_data = self.item_features[self.features_columns]
            else:
                features_data = self.item_features
            
            # Calcular matriz de similaridade
            self._calculate_similarity_matrix(features_data)
            
            self.is_fitted = True
            logger.info("Modelo baseado em conteúdo treinado com sucesso")
            return self
            
        except Exception as e:
            logger.error(f"Erro ao treinar modelo baseado em conteúdo: {e}")
            raise
    
    def _calculate_similarity_matrix(self, features_data: pd.DataFrame):
        """Calcula matriz de similaridade entre itens"""
        # Para features numéricas, usar cosine similarity diretamente
        numeric_cols = features_data.select_dtypes(include=[np.number]).columns
        text_cols = features_data.select_dtypes(include=['object']).columns
        
        if len(numeric_cols) > 0:
            numeric_similarity = cosine_similarity(features_data[numeric_cols].fillna(0))
        else:
            numeric_similarity = np.zeros((len(features_data), len(features_data)))
        
        # Para features de texto, usar TF-IDF
        if len(text_cols) > 0:
            text_features = features_data[text_cols].fillna('').apply(
                lambda x: ' '.join(x.astype(str)), axis=1
            )
            self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(text_features)
            text_similarity = cosine_similarity(tfidf_matrix)
        else:
            text_similarity = np.zeros((len(features_data), len(features_data)))
        
        # Combinar similaridades (média ponderada)
        combined_similarity = (numeric_similarity + text_similarity) / 2
        
        self.similarity_matrix = pd.DataFrame(
            combined_similarity,
            index=features_data.index,
            columns=features_data.index
        )
    
    def predict(self, user_items: List[str], n_recommendations: int = 10) -> List[Tuple[str, float]]:
        """
        Gera recomendações baseadas nos itens que o usuário já interagiu
        
        Args:
            user_items: Lista de IDs dos itens que o usuário já consumiu
            n_recommendations: Número de recomendações
            
        Returns:
            Lista de tuplas (item_id, score)
        """
        if not self.is_fitted:
            raise ValueError("Modelo não foi treinado. Execute fit() primeiro.")
        
        try:
            item_scores = {}
            
            # Para cada item não consumido
            for item_id in self.similarity_matrix.index:
                if item_id not in user_items:
                    score = 0
                    count = 0
                    
                    # Calcular score baseado na similaridade com itens consumidos
                    for user_item in user_items:
                        if user_item in self.similarity_matrix.index:
                            similarity = self.similarity_matrix.loc[item_id, user_item]
                            score += similarity
                            count += 1
                    
                    if count > 0:
                        item_scores[item_id] = score / count
            
            # Ordenar e retornar top N
            sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_items[:n_recommendations]
            
        except Exception as e:
            logger.error(f"Erro na predição: {e}")
            return []
    
    def get_item_similarity(self, item1: str, item2: str) -> float:
        """Retorna similaridade entre dois itens"""
        if not self.is_fitted:
            return 0.0
        
        if item1 in self.similarity_matrix.index and item2 in self.similarity_matrix.columns:
            return float(self.similarity_matrix.loc[item1, item2])
        return 0.0
    
    def get_similar_items(self, item_id: str, n_similar: int = 5) -> List[Tuple[str, float]]:
        """
        Retorna itens similares a um item específico
        
        Args:
            item_id: ID do item de referência
            n_similar: Número de itens similares a retornar
            
        Returns:
            Lista de tuplas (item_id, similarity_score)
        """
        if not self.is_fitted:
            return []
        
        try:
            if item_id not in self.similarity_matrix.index:
                logger.warning(f"Item {item_id} não encontrado na matriz de similaridade")
                return []
            
            # Obter similaridades para o item
            item_similarities = self.similarity_matrix.loc[item_id]
            
            # Excluir o próprio item
            item_similarities = item_similarities.drop(item_id)
            
            # Ordenar por similaridade decrescente
            sorted_similarities = item_similarities.sort_values(ascending=False)
            
            # Retornar top N
            similar_items = [(item, float(score)) for item, score in sorted_similarities.head(n_similar).items()]
            return similar_items
            
        except Exception as e:
            logger.error(f"Erro ao buscar itens similares: {e}")
            return []