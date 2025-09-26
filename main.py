from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
import os

# Importar configuração dos serviços
from app_setup import analytics_service

# Importar as rotas
from routes import recommendations, analytics

# Configuração da aplicação
app = FastAPI(
    title="Olist Recommendation API",
    description="API de recomendações para e-commerce Olist",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir as rotas
app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

@app.get("/", response_class=HTMLResponse)
async def root():
    """Página inicial da API"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Olist Recommendation API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .endpoint { background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 8px; }
            .method { color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; }
            .get { background-color: #61affe; }
            .post { background-color: #49cc90; }
            .put { background-color: #fca130; }
            .delete { background-color: #f93e3e; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛒 Olist Recommendation API</h1>
            <p>API de recomendações para e-commerce usando dados da Olist</p>
            
            <h2>📋 Endpoints Disponíveis</h2>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span> /docs</h3>
                <p>Documentação interativa da API (Swagger UI)</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span> /recommendations/complementary/{product_id}</h3>
                <p>Obter produtos complementares para um produto</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span> /recommendations/health</h3>
                <p>Status de saúde da API</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span> /analytics/metrics</h3>
                <p>Obter métricas gerais da plataforma</p>
            </div>
            
            <h2>🚀 Como testar</h2>
            <p>1. Acesse <a href="/docs">/docs</a> para a documentação interativa</p>
            <p>2. Use o arquivo test_api.html para testes completos</p>
            <p>3. Registre um usuário em <code>/auth/register</code></p>
            <p>4. Faça login em <code>/auth/token</code> para obter um token</p>
            <p>5. Use o token para acessar endpoints protegidos</p>
        </div>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Verificação de saúde da API"""
    return {
        "status": "healthy",
        "message": "Olist Recommendation API está funcionando",
        "services": {
            "auth": "active",
            "recommendations": "active", 
            "analytics": "active"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )