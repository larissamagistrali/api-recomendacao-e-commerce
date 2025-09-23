import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging

from .collaborative import CollaborativeFilteringModel
from .content_based import ContentBasedModel

logger = logging.getLogger(__name__)

class HybridModel:
    """Modelo híbrido que combina filtragem colaborativa e baseada em conteúdo"""
    
    def __init__(self, 
                 collaborative_weight: float = 0.6, 
                 content_weight: float = 0.4,
                 min_interactions: int = 5):
        """
        Inicializa o modelo híbrido
        
        Args:
            collaborative_weight: Peso para filtragem colaborativa
            content_weight: Peso para filtragem baseada em conteúdo
            min_interactions: Mínimo de interações para usar filtragem colaborativa
        """
        if collaborative_weight + content_weight != 1.0:
            raise ValueError("A soma dos pesos deve ser igual a 1.0")
        
        self.collaborative_weight = collaborative_weight
        self.content_weight = content_weight
        self.min_interactions = min_interactions
        
        self.collaborative_model = CollaborativeFilteringModel()
        self.content_model = ContentBasedModel()
        
        self.is_fitted = False
    
    def fit(self, 
            interactions: pd.DataFrame, 
            item_features: pd.DataFrame,
            user_col: str = 'user_id',
            item_col: str = 'product_id',
            rating_col: str = 'rating') -> 'HybridModel':
        """
        Treina ambos os modelos (colaborativo e baseado em conteúdo)
        
        Args:
            interactions: DataFrame com interações usuário-item
            item_features: DataFrame com características dos itens
            user_col: Nome da coluna de usuário
            item_col: Nome da coluna de item
            rating_col: Nome da coluna de rating
        """
        try:
            logger.info("Iniciando treinamento do modelo híbrido...")
            
            # Treinar modelo colaborativo
            logger.info("Treinando modelo colaborativo...")
            self.collaborative_model.fit(interactions, user_col, item_col, rating_col)
            
            # Treinar modelo baseado em conteúdo
            logger.info("Treinando modelo baseado em conteúdo...")
            self.content_model.fit(item_features)
            
            self.is_fitted = True
            logger.info("Modelo híbrido treinado com sucesso")
            return self
            
        except Exception as e:
            logger.error(f"Erro ao treinar modelo híbrido: {e}")
            raise
    
    def predict(self, 
                user_id: str, 
                user_interactions: Optional[List[str]] = None,
                n_recommendations: int = 10) -> List[Tuple[str, float]]:
        """
        Gera recomendações híbridas para um usuário
        
        Args:
            user_id: ID do usuário
            user_interactions: Lista de itens que o usuário já interagiu (opcional)
            n_recommendations: Número de recomendações
            
        Returns:
            Lista de tuplas (item_id, score)
        """
        if not self.is_fitted:
            raise ValueError("Modelo não foi treinado. Execute fit() primeiro.")
        
        try:
            # Determinar estratégia baseada no número de interações do usuário
            strategy = self._determine_strategy(user_id, user_interactions)
            
            if strategy == "collaborative":
                return self._collaborative_predictions(user_id, n_recommendations)
            elif strategy == "content_based":
                return self._content_predictions(user_interactions, n_recommendations)
            else:  # hybrid
                return self._hybrid_predictions(user_id, user_interactions, n_recommendations)
                
        except Exception as e:
            logger.error(f"Erro na predição híbrida para usuário {user_id}: {e}")
            return []
    
    def _determine_strategy(self, user_id: str, user_interactions: Optional[List[str]]) -> str:
        """Determina qual estratégia usar baseada no perfil do usuário"""
        try:
            # Verificar se usuário existe no modelo colaborativo
            if hasattr(self.collaborative_model, 'user_item_matrix') and \
               self.collaborative_model.user_item_matrix is not None and \
               user_id in self.collaborative_model.user_item_matrix.index:
                
                # Contar interações do usuário
                user_interactions_count = (self.collaborative_model.user_item_matrix.loc[user_id] > 0).sum()
                
                if user_interactions_count >= self.min_interactions:
                    return "hybrid"
                else:
                    return "content_based"
            else:
                # Usuário novo - usar conteúdo se tiver interações, senão popular
                return "content_based" if user_interactions else "popular"
                
        except Exception as e:
            logger.warning(f"Erro ao determinar estratégia: {e}")
            return "content_based"
    
    def _collaborative_predictions(self, user_id: str, n_recommendations: int) -> List[Tuple[str, float]]:
        """Predições usando apenas filtragem colaborativa"""
        try:
            return self.collaborative_model.predict(user_id, n_recommendations)
        except Exception as e:
            logger.warning(f"Erro na predição colaborativa: {e}")
            return []
    
    def _content_predictions(self, user_interactions: Optional[List[str]], n_recommendations: int) -> List[Tuple[str, float]]:
        """Predições usando apenas filtragem baseada em conteúdo"""
        try:
            if not user_interactions:
                return []
            return self.content_model.predict(user_interactions, n_recommendations)
        except Exception as e:
            logger.warning(f"Erro na predição baseada em conteúdo: {e}")
            return []
    
    def _hybrid_predictions(self, 
                           user_id: str, 
                           user_interactions: Optional[List[str]], 
                           n_recommendations: int) -> List[Tuple[str, float]]:
        """Predições híbridas combinando ambos os modelos"""
        try:
            # Obter predições de ambos os modelos
            collaborative_recs = self._collaborative_predictions(user_id, n_recommendations * 2)
            content_recs = self._content_predictions(user_interactions, n_recommendations * 2) if user_interactions else []
            
            # Combinar scores
            combined_scores = {}
            
            # Adicionar scores colaborativos
            for item_id, score in collaborative_recs:
                combined_scores[item_id] = score * self.collaborative_weight
            
            # Adicionar scores baseados em conteúdo
            for item_id, score in content_recs:
                if item_id in combined_scores:
                    combined_scores[item_id] += score * self.content_weight
                else:
                    combined_scores[item_id] = score * self.content_weight
            
            # Ordenar por score combinado
            sorted_items = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_items[:n_recommendations]
            
        except Exception as e:
            logger.error(f"Erro na predição híbrida: {e}")
            return []
    
    def get_model_explanation(self, user_id: str, user_interactions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Retorna explicação sobre qual modelo/estratégia foi usada
        
        Args:
            user_id: ID do usuário
            user_interactions: Lista de interações do usuário
            
        Returns:
            Dicionário com explicação da estratégia utilizada
        """
        strategy = self._determine_strategy(user_id, user_interactions)
        
        explanations = {
            "collaborative": {
                "strategy": "Filtragem Colaborativa",
                "description": "Recomendações baseadas em usuários similares",
                "reason": f"Usuário tem {self.min_interactions}+ interações"
            },
            "content_based": {
                "strategy": "Baseado em Conteúdo", 
                "description": "Recomendações baseadas nas características dos itens",
                "reason": "Usuário novo ou com poucas interações"
            },
            "hybrid": {
                "strategy": "Híbrido",
                "description": f"Combinação de colaborativo ({self.collaborative_weight:.0%}) e conteúdo ({self.content_weight:.0%})",
                "reason": "Usuário com histórico suficiente para análise completa"
            }
        }
        
        return explanations.get(strategy, explanations["content_based"])
    
    def update_weights(self, collaborative_weight: float, content_weight: float):
        """
        Atualiza os pesos dos modelos
        
        Args:
            collaborative_weight: Novo peso para filtragem colaborativa
            content_weight: Novo peso para filtragem baseada em conteúdo
        """
        if collaborative_weight + content_weight != 1.0:
            raise ValueError("A soma dos pesos deve ser igual a 1.0")
        
        self.collaborative_weight = collaborative_weight
        self.content_weight = content_weight
        
        logger.info(f"Pesos atualizados: Colaborativo={collaborative_weight:.2f}, Conteúdo={content_weight:.2f}")