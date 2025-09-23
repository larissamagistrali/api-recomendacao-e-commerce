import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import NMF
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class CollaborativeFilteringModel:
    """Modelo de filtragem colaborativa para recomendações"""
    
    def __init__(self, n_factors: int = 10, random_state: int = 42):
        """
        Inicializa o modelo de filtragem colaborativa
        
        Args:
            n_factors: Número de fatores latentes
            random_state: Seed para reprodutibilidade
        """
        self.n_factors = n_factors
        self.random_state = random_state
        self.model = NMF(n_components=n_factors, random_state=random_state)
        self.user_item_matrix = None
        self.user_factors = None
        self.item_factors = None
        self.is_fitted = False
    
    def fit(self, interactions: pd.DataFrame, user_col: str = 'user_id', 
            item_col: str = 'product_id', rating_col: str = 'rating') -> 'CollaborativeFilteringModel':
        """
        Treina o modelo com as interações usuário-item
        
        Args:
            interactions: DataFrame com interações usuário-item
            user_col: Nome da coluna de usuário
            item_col: Nome da coluna de item
            rating_col: Nome da coluna de rating/pontuação
        """
        try:
            # Criar matriz usuário-item
            self.user_item_matrix = interactions.pivot_table(
                index=user_col, 
                columns=item_col, 
                values=rating_col, 
                fill_value=0
            )
            
            # Treinar modelo NMF
            user_item_array = self.user_item_matrix.values
            self.user_factors = self.model.fit_transform(user_item_array)
            self.item_factors = self.model.components_
            
            self.is_fitted = True
            logger.info(f"Modelo colaborativo treinado com {len(self.user_item_matrix)} usuários e {len(self.user_item_matrix.columns)} itens")
            return self
            
        except Exception as e:
            logger.error(f"Erro ao treinar modelo colaborativo: {e}")
            raise
    
    def predict(self, user_id: str, n_recommendations: int = 10) -> List[Tuple[str, float]]:
        """
        Gera recomendações para um usuário
        
        Args:
            user_id: ID do usuário
            n_recommendations: Número de recomendações
            
        Returns:
            Lista de tuplas (item_id, score)
        """
        if not self.is_fitted:
            raise ValueError("Modelo não foi treinado. Execute fit() primeiro.")
        
        try:
            if user_id not in self.user_item_matrix.index:
                logger.warning(f"Usuário {user_id} não encontrado no conjunto de treino")
                return []
            
            user_idx = self.user_item_matrix.index.get_loc(user_id)
            user_profile = self.user_factors[user_idx]
            
            # Calcular scores para todos os itens
            item_scores = np.dot(user_profile, self.item_factors)
            
            # Obter itens já consumidos pelo usuário
            consumed_items = self.user_item_matrix.loc[user_id]
            consumed_items = consumed_items[consumed_items > 0].index.tolist()
            
            # Criar lista de recomendações (excluindo itens já consumidos)
            recommendations = []
            for idx, score in enumerate(item_scores):
                item_id = self.user_item_matrix.columns[idx]
                if item_id not in consumed_items:
                    recommendations.append((item_id, float(score)))
            
            # Ordenar por score e retornar top N
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:n_recommendations]
            
        except Exception as e:
            logger.error(f"Erro na predição para usuário {user_id}: {e}")
            return []
    
    def get_user_similarity(self, user1: str, user2: str) -> float:
        """Retorna similaridade entre dois usuários"""
        if not self.is_fitted:
            return 0.0
        
        try:
            if user1 not in self.user_item_matrix.index or user2 not in self.user_item_matrix.index:
                return 0.0
            
            user1_idx = self.user_item_matrix.index.get_loc(user1)
            user2_idx = self.user_item_matrix.index.get_loc(user2)
            
            user1_profile = self.user_factors[user1_idx]
            user2_profile = self.user_factors[user2_idx]
            
            # Calcular similaridade de cosseno
            similarity = cosine_similarity([user1_profile], [user2_profile])[0][0]
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Erro ao calcular similaridade entre usuários: {e}")
            return 0.0

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