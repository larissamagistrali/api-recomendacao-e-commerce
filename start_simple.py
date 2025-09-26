#!/usr/bin/env python3

import asyncio
import uvicorn
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Inicia a API em modo simplificado"""
    print("🚀 INICIANDO API DE PRODUTOS COMPLEMENTARES (MODO DESENVOLVIMENTO)")
    print("=" * 70)
    print()
    print("📋 CONFIGURAÇÃO:")
    print("   - Modo: Desenvolvimento (usando CSVs locais)")
    print("   - PostgreSQL: Desabilitado (logs simulados)")
    print("   - Redis: Desabilitado (cache em memória)")
    print("   - Elasticsearch: Desabilitado (busca simplificada)")
    print()
    print("🌐 ENDPOINTS DISPONÍVEIS:")
    print("   - Swagger UI: http://localhost:8000/docs")
    print("   - ReDoc: http://localhost:8000/redoc")
    print("   - Health Check: http://localhost:8000/recommendations/health")
    print("   - Produtos Populares: http://localhost:8000/recommendations/popular")
    print("   - Complementares: http://localhost:8000/recommendations/complementary/{product_id}")
    print()
    print("📦 EXEMPLO DE TESTE:")
    print("   curl -X GET 'http://localhost:8000/recommendations/popular?limit=5'")
    print()
    print("🛑 Para parar: Ctrl+C")
    print("=" * 70)
    print()
    
    # Iniciar a API
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["."],
        log_level="info"
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 API encerrada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar a API: {e}")
        sys.exit(1)