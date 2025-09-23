from db_service import OlistDatabaseService
from config import DEFAULT_DB_CONFIG

def main():
    """Exemplo de uso do serviço de banco de dados"""
    
    # Inicializar serviço
    db_service = OlistDatabaseService(
        server=DEFAULT_DB_CONFIG.server,
        database=DEFAULT_DB_CONFIG.database,
        trusted_connection=DEFAULT_DB_CONFIG.trusted_connection
    )
    
    try:
        # 1. Criar schema do banco
        print("Criando schema do banco...")
        db_service.create_database_schema()
        
        # 2. Carregar dados dos CSVs
        print("Carregando dados...")
        db_service.load_all_olist_data(DEFAULT_DB_CONFIG.data_path)
        
        # 3. Exemplos de consultas para recomendações
        print("\n=== ANÁLISES DE RECOMENDAÇÃO ===")
        
        # Produtos mais populares
        popular = db_service.get_popular_products(10)
        print(f"Produtos mais vendidos: {popular[:5]}")
        
        # Produtos por região
        sp_products = db_service.get_products_by_state("SP", 10)
        print(f"Mais vendidos em SP: {sp_products[:5]}")
        
        # Produtos melhor avaliados
        best_rated = db_service.get_best_rated_products(min_reviews=10, limit=10)
        print(f"Melhor avaliados: {best_rated[:5]}")
        
        # Produtos sazonais (dezembro)
        december_products = db_service.get_seasonal_products(12, 10)
        print(f"Mais vendidos em dezembro: {december_products[:5]}")
        
        # Pares de produtos frequentes
        frequent_pairs = db_service.get_frequent_pairs(5)
        print(f"Pares frequentes: {frequent_pairs[:3]}")
        
        # Matriz usuário-item para filtragem colaborativa
        print("\nCarregando matriz usuário-item...")
        user_item_matrix = db_service.get_user_item_matrix()
        print(f"Dimensões da matriz: {user_item_matrix.shape}")
        
        print("\n✅ Banco de dados configurado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        db_service.close_connection()

if __name__ == "__main__":
    main()