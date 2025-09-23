# 🛒 Olist Recommendation API

Uma API REST moderna para sistema de recomendações de produtos do e-commerce Olist, construída com FastAPI e algoritmos de machine learning.

## 🎯 Visão Geral

A Olist Recommendation API fornece recomendações personalizadas de produtos baseadas em diferentes estratégias de filtragem, incluindo filtragem colaborativa, baseada em conteúdo e híbrida. A API utiliza dados reais do marketplace brasileiro Olist para gerar recomendações inteligentes.

### Principais Características

- ⚡ **Alta Performance**: Construída com FastAPI e processamento assíncrono
- 🤖 **Múltiplos Algoritmos**: Filtragem colaborativa, baseada em conteúdo e híbrida
- 🗄️ **Integração com SQL Server**: Armazenamento e consulta otimizada de dados
- 📊 **Analytics em Tempo Real**: Métricas de performance e uso da API
- 🔒 **Segurança**: Autenticação JWT e validação de dados
- 📚 **Documentação Automática**: Swagger/OpenAPI integrado

## ✨ Funcionalidades

### Tipos de Recomendação

1. **Recomendação por Popularidade**: Produtos mais vendidos globalmente ou por região
2. **Filtragem Colaborativa**: Baseada no comportamento de usuários similares
3. **Filtragem por Conteúdo**: Baseada em características dos produtos
4. **Recomendação Híbrida**: Combinação de múltiplas estratégias
5. **Recomendação Sazonal**: Produtos populares em épocas específicas
6. **Produtos Relacionados**: Itens frequentemente comprados juntos

### Recursos Adicionais

- Recomendações por estado/região
- Produtos melhor avaliados
- Análise de sentimento de reviews
- Cache inteligente para performance
- Rate limiting para controle de uso
- Logs estruturados para monitoramento

## 🛠️ Tecnologias

- **Framework**: FastAPI 0.104+
- **Banco de Dados**: SQL Server com SQLAlchemy
- **Machine Learning**: Scikit-learn, NumPy, SciPy
- **Processamento de Dados**: Pandas
- **Autenticação**: JWT com python-jose
- **Documentação**: Swagger/OpenAPI
- **Testes**: Pytest
- **Qualidade de Código**: Black, Flake8, MyPy

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- SQL Server 2019+ ou SQL Server Express
- ODBC Driver 17 for SQL Server

### Instalação Local

1. **Clone o repositório:**

```bash
[git clone https://github.com/larissamagistrali/algoritmos-recomendacao.git](https://github.com/larissamagistrali/api-recomendacao-e-commerce.git)
```

2. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

3. **Configure o banco de dados:**

```bash
python3 -c "from db_service import DatabaseService; db = DatabaseService(); print('Database service initialized successfully')"
```

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env`

```env
# Database
SQL_SERVER=localhost
SQL_DATABASE=OlistRecommendations
SQL_TRUSTED_CONNECTION=True

# API
API_HOST=127.0.0.1
API_PORT=8000
SECRET_KEY=your-super-secret-key-here

# ML Models
MAX_RECOMMENDATIONS=20
CACHE_TTL=3600
```

### Configuração do Banco de Dados

A API utiliza SQL Server como banco principal. Certifique-se de:

1. Ter o SQL Server instalado e rodando
2. Criar um banco chamado `OlistRecommendations`
3. Configurar as credenciais no arquivo `.env`

## 🎮 Uso

### Iniciando o Servidor

```bash
# Desenvolvimento
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Produção
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

```

### Acessando a Documentação

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🔗 Endpoints

### Autenticação

```http
POST /auth/token
POST /auth/register
```

### Recomendações

#### Recomendações por Usuário

```http
GET /recommendations/user/{user_id}?limit=10&strategy=collaborative
```

#### Produtos Populares

```http
GET /recommendations/popular?limit=10&state=SP
```

#### Produtos Relacionados

```http
GET /recommendations/related/{product_id}?limit=5
```

#### Recomendações Sazonais

```http
GET /recommendations/seasonal?month=12&limit=10
```

#### Produtos Melhor Avaliados

```http
GET /recommendations/top-rated?min_reviews=10&limit=10
```

### Analytics

```http
GET /analytics/metrics
GET /analytics/popular-categories
GET /analytics/user-behavior/{user_id}
```

### Exemplo de Uso

```python
import requests

# Obter token de autenticação
auth_response = requests.post("http://localhost:8000/auth/token", {
    "username": "user@example.com",
    "password": "password"
})
token = auth_response.json()["access_token"]

# Headers com autenticação
headers = {"Authorization": f"Bearer {token}"}

# Obter recomendações para um usuário
response = requests.get(
    "http://localhost:8000/recommendations/user/123?limit=5&strategy=hybrid",
    headers=headers
)

recommendations = response.json()
print(recommendations)
```

## 🧠 Algoritmos de Recomendação

### 1. Filtragem Colaborativa

- **User-Based**: Recomenda produtos baseado em usuários similares
- **Item-Based**: Recomenda produtos similares aos já comprados
- **Matrix Factorization**: SVD para redução de dimensionalidade

### 2. Filtragem por Conteúdo

- Análise de características dos produtos
- Similaridade baseada em categorias
- Processamento de texto de descrições

### 3. Algoritmos Híbridos

- Combinação ponderada de múltiplas estratégias
- Switch híbrido baseado em contexto
- Meta-learning para seleção de algoritmos

### 4. Recomendações Contextuais

- Sazonalidade (datas especiais, meses)
- Localização geográfica
- Tendências de mercado

### Monitoramento

- **Logs estruturados** com Structlog
- **Métricas de performance** via endpoints `/metrics`
- **Health checks** via endpoint `/health`
