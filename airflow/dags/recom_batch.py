from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from sklearn.metrics.pairwise import cosine_similarity
import os, glob, pandas as pd, numpy as np
from sqlalchemy import create_engine
import gc

try:
    from scipy.sparse import csr_matrix
except ImportError:
    print("Warning: scipy not available, falling back to dense matrices")
    csr_matrix = None

# --- Configuração do banco ---
OP_CONN = {
    "host": os.getenv("OP_DB_HOST", "op-db"),
    "port": int(os.getenv("OP_DB_PORT", 5432)),
    "dbname": os.getenv("OP_DB_NAME", "opdb"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
}

DATA_PATH = "/opt/airflow/data"

# --- Função para ingestão de CSVs ---
def ingest_csvs():
    csv_files = glob.glob(os.path.join(DATA_PATH, "*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {DATA_PATH}")

    engine = create_engine(
        f"postgresql+psycopg2://{OP_CONN['user']}:{OP_CONN['password']}@{OP_CONN['host']}:{OP_CONN['port']}/{OP_CONN['dbname']}"
    )
    print(f"postgresql+psycopg2://{OP_CONN['user']}:{OP_CONN['password']}@{OP_CONN['host']}:{OP_CONN['port']}/{OP_CONN['dbname']}")

    for csv_file in csv_files:
        table_name = os.path.splitext(os.path.basename(csv_file.replace("olist_", "").replace("_dataset", "")))[0]
        df = pd.read_csv(csv_file)
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Tabela '{table_name}' criada/atualizada com dados de '{csv_file}'.")

# --- Função para criar tabela de similaridade ---
def create_item_similarity():
    engine = create_engine(
        f"postgresql+psycopg2://{OP_CONN['user']}:{OP_CONN['password']}@{OP_CONN['host']}:{OP_CONN['port']}/{OP_CONN['dbname']}"
    )

    # --- Verificar existência das tabelas necessárias ---
    tables = pd.read_sql(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'", engine
    )['table_name'].tolist()

    required_tables = ['orders', 'order_items', 'customers', 'products']
    missing_tables = [t for t in required_tables if t not in tables]
    if missing_tables:
        raise ValueError(f"As seguintes tabelas estão faltando no banco: {missing_tables}")

    # --- Analisar dimensões dos dados ---
    print("Analisando dimensões dos dados...")
    num_customers = pd.read_sql("SELECT COUNT(DISTINCT customer_id) as count FROM customers", engine).iloc[0]['count']
    num_products = pd.read_sql("SELECT COUNT(DISTINCT product_id) as count FROM products", engine).iloc[0]['count']
    num_orders = pd.read_sql("SELECT COUNT(*) as count FROM orders", engine).iloc[0]['count']
    num_order_items = pd.read_sql("SELECT COUNT(*) as count FROM order_items", engine).iloc[0]['count']
    
    print("Dimensões encontradas:")
    print(f"- Clientes únicos: {num_customers:,}")
    print(f"- Produtos únicos: {num_products:,}")
    print(f"- Pedidos: {num_orders:,}")
    print(f"- Itens de pedido: {num_order_items:,}")
    print(f"- Matrix potencial: {num_customers:,} x {num_products:,} = {num_customers * num_products:,} células")

    # --- Filtrar por produtos mais populares para reduzir dimensionalidade ---
    MIN_PRODUCT_PURCHASES = 5  # Produtos que foram comprados pelo menos 5 vezes
    MAX_PRODUCTS = 1000  # Limitar a no máximo 1000 produtos mais populares
    
    print(f"Filtrando produtos (mín {MIN_PRODUCT_PURCHASES} compras, máx {MAX_PRODUCTS} produtos)...")
    
    popular_products_query = """
    SELECT oi.product_id, COUNT(*) as purchase_count
    FROM order_items oi 
    GROUP BY oi.product_id 
    HAVING COUNT(*) >= %s
    ORDER BY COUNT(*) DESC 
    LIMIT %s
    """
    
    try:
        popular_products_df = pd.read_sql(popular_products_query, engine, params=(MIN_PRODUCT_PURCHASES, MAX_PRODUCTS))
        popular_product_ids = popular_products_df['product_id'].tolist()
        
        print(f"Produtos selecionados: {len(popular_product_ids):,}")
        
        if len(popular_product_ids) == 0:
            raise ValueError("Nenhum produto encontrado com os critérios especificados")
            
    except Exception as e:
        print(f"Erro ao buscar produtos populares: {e}")
        raise

    # --- Ler apenas dados relevantes ---
    print("Carregando dados filtrados...")
    
    # Query otimizada que já faz o join e filtra produtos
    # Usar IN com placeholders para evitar problemas de formatação
    placeholders = ','.join(['%s'] * len(popular_product_ids))
    data_query = f"""
    SELECT 
        o.customer_id,
        oi.product_id,
        COUNT(*) as purchase_count
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE oi.product_id IN ({placeholders})
    GROUP BY o.customer_id, oi.product_id
    """
    
    try:
        # Convert list to tuple for pd.read_sql params
        product_counts = pd.read_sql(data_query, engine, params=tuple(popular_product_ids))
        print(f"Registros de compra: {len(product_counts):,}")
        
    except Exception as e:
        print(f"Erro ao executar query de dados: {e}")
        print(f"Query: {data_query}")
        print(f"Params: {popular_product_ids[:5]}...")  # Mostrar apenas os primeiros 5
        raise
    
    # --- Criar matriz user-item ---
    print("Criando matriz user-item...")
    
    # Mapear IDs para índices
    unique_customers = sorted(product_counts['customer_id'].unique())
    unique_products = sorted(product_counts['product_id'].unique())
    
    customer_to_idx = {cust: idx for idx, cust in enumerate(unique_customers)}
    product_to_idx = {prod: idx for idx, prod in enumerate(unique_products)}
    
    if csr_matrix is not None:
        # Criar matriz esparsa se scipy disponível
        print("Usando matriz esparsa (scipy)...")
        rows = [customer_to_idx[cust] for cust in product_counts['customer_id']]
        cols = [product_to_idx[prod] for prod in product_counts['product_id']]
        data = product_counts['purchase_count'].values
        
        user_item_matrix = csr_matrix((data, (rows, cols)), shape=(len(unique_customers), len(unique_products)))
        print(f"Matriz esparsa criada: {user_item_matrix.shape[0]:,} x {user_item_matrix.shape[1]:,}")
        print(f"Densidade: {user_item_matrix.nnz / (user_item_matrix.shape[0] * user_item_matrix.shape[1]):.4%}")
    else:
        # Fallback para pivot table com dados limitados
        print("Usando pivot table (fallback)...")
        user_item_matrix = product_counts.pivot_table(
            index='customer_id',
            columns='product_id', 
            values='purchase_count',
            fill_value=0
        )
        print(f"Matriz densa criada: {user_item_matrix.shape[0]:,} x {user_item_matrix.shape[1]:,}")
        
    print("Matriz user-item criada com sucesso")
    
    # Limpar memória
    del product_counts, rows, cols, data
    gc.collect()

    # --- Calcular similaridade entre itens ---
    print("Calculando similaridade entre itens...")
    
    if csr_matrix is not None and hasattr(user_item_matrix, 'T'):
        # Para matriz esparsa
        item_matrix = user_item_matrix.T.tocsr()
        del user_item_matrix
        gc.collect()
        item_similarity = cosine_similarity(item_matrix)
        del item_matrix
        gc.collect()
    else:
        # Para matriz densa (pivot table)
        item_matrix = user_item_matrix.T
        del user_item_matrix
        gc.collect()
        item_similarity = cosine_similarity(item_matrix)
        del item_matrix
        gc.collect()
    
    print("Similaridade calculada com sucesso")

    # --- Criar DataFrame apenas com similaridades significativas ---
    print("Processando resultados...")
    
    # Converter para DataFrame, mantendo apenas valores acima de um threshold
    SIMILARITY_THRESHOLD = 0.1  # Manter apenas similaridades >= 0.1
    
    similarity_data = []
    n_products = len(unique_products)
    
    for i in range(n_products):
        for j in range(i+1, n_products):  # Evitar duplicatas (matriz simétrica)
            similarity = item_similarity[i, j]
            if similarity >= SIMILARITY_THRESHOLD:
                similarity_data.append({
                    'product_id_1': unique_products[i],
                    'product_id_2': unique_products[j],
                    'similarity': similarity
                })
    
    if similarity_data:
        item_similarity_df = pd.DataFrame(similarity_data)
        
        # --- Persistir no banco ---
        print(f"Salvando {len(item_similarity_df):,} pares de similaridade no banco...")
        item_similarity_df.to_sql('item_similarity', engine, if_exists='replace', index=False)
        print("Tabela 'item_similarity' atualizada com sucesso.")
    else:
        print("Nenhuma similaridade significativa encontrada. Criando tabela vazia.")
        empty_df = pd.DataFrame(columns=['product_id_1', 'product_id_2', 'similarity'])
        empty_df.to_sql('item_similarity', engine, if_exists='replace', index=False)
    
    # Limpar memória final
    del item_similarity
    gc.collect()
    
    print("Processamento concluído!")

# --- DAG ---
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    'recom_batch',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False
) as dag:

    ingest_task = PythonOperator(task_id="ingest_csvs", python_callable=ingest_csvs)
    similarity_task = PythonOperator(task_id='create_item_similarity', python_callable=create_item_similarity)

    # Ordem: ingestão -> similaridade
    ingest_task >> similarity_task
