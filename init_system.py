#!/usr/bin/env python3
"""
Script de inicialização e demonstração do sistema de produtos complementares

Este script:
1. Configura o ambiente de desenvolvimento
2. Executa o processamento batch inicial
3. Demonstra como usar a API
4. Fornece comandos úteis para administração
"""

import asyncio
import os
import sys
from pathlib import Path

# Adicionar o diretório da aplicação ao path
sys.path.insert(0, str(Path(__file__).parent))

from batch_processor import BatchProcessor
from services.complementary_service import ComplementaryRecommendationService
from config import Config

class SystemInitializer:
    """Inicializador do sistema de produtos complementares"""
    
    def __init__(self):
        self.batch_processor = BatchProcessor()
        self.complementary_service = ComplementaryRecommendationService()
        
    async def check_environment(self):
        """Verifica se o ambiente está configurado corretamente"""
        print("=== VERIFICAÇÃO DO AMBIENTE ===")
        
        # Verificar se os dados estão disponíveis
        data_path = Path("ds")
        required_files = [
            "olist_orders_dataset.csv",
            "olist_order_items_dataset.csv", 
            "olist_products_dataset.csv",
            "olist_customers_dataset.csv"
        ]
        
        missing_files = []
        for file in required_files:
            if not (data_path / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Arquivos de dados faltando: {missing_files}")
            print("   Baixe os dados do Olist: https://www.kaggle.com/olistbr/brazilian-ecommerce")
            return False
        else:
            print("✅ Arquivos de dados encontrados")
        
        print(f"   PostgreSQL: {Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}")
        print(f"   Redis: {Config.REDIS_HOST}:{Config.REDIS_PORT}")
        print(f"   Elasticsearch: {Config.ELASTICSEARCH_HOST}:{Config.ELASTICSEARCH_PORT}")
    
        return True
        
    async def run_initial_setup(self):
        """Executa a configuração inicial completa"""
        print("\n=== CONFIGURAÇÃO INICIAL ===")
        
        try:
            # Inicializar serviços
            print("🔧 Inicializando serviços...")
            await self.batch_processor.initialize()
            await self.complementary_service.initialize()
            
            # Executar processamento batch inicial
            print("🔄 Executando processamento batch inicial...")
            print("   (Isso pode levar alguns minutos...)")
            
            result = await self.batch_processor.process_complementary_products()
            
            if result['status'] == 'success':
                print("✅ Processamento batch concluído com sucesso!")
                print(f"   - {result['total_candidates']} candidatos complementares gerados")
                print(f"   - {result['unique_products']} produtos únicos processados")
                print(f"   - {result['es_products_indexed']} produtos indexados no Elasticsearch")
            else:
                print(f"❌ Erro no processamento batch: {result.get('error', 'Erro desconhecido')}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na configuração inicial: {e}")
            return False
        finally:
            await self.batch_processor.close()
            await self.complementary_service.close()
            
        return True
        
    async def run_demo(self):
        """Executa uma demonstração da API"""
        print("\n=== DEMONSTRAÇÃO DA API ===")
        
        try:
            await self.complementary_service.initialize()
            
            # Pegar alguns produtos para demonstração
            from db_service import DatabaseService
            db_service = DatabaseService()
            
            # Buscar produtos populares
            popular_products = db_service.get_popular_products(limit=5)
            
            if not popular_products:
                print("❌ Nenhum produto encontrado para demonstração")
                return
                
            print(f"🎯 Testando recomendações para {len(popular_products)} produtos populares:")
            
            for i, product in enumerate(popular_products[:3]):  # Testar apenas 3 produtos
                product_id = product['product_id']
                print(f"\n--- Produto {i+1}: {product_id} ---")
                
                # Testar recomendações
                result = await self.complementary_service.get_complementary_products(
                    product_id=product_id,
                    context_type="PDP",
                    limit=5
                )
                
                print(f"   Fonte: {result['source']}")
                print(f"   Total: {result['total']} recomendações")
                
                for j, rec in enumerate(result['recommendations'][:3]):
                    print(f"   {j+1}. {rec['product_id']} - Lift: {rec['lift_score']:.2f}")
                    
        except Exception as e:
            print(f"❌ Erro na demonstração: {e}")
        finally:
            await self.complementary_service.close()
            
    def print_usage_examples(self):
        """Imprime exemplos de uso da API"""
        print("\n=== EXEMPLOS DE USO DA API ===")
        
        print("1. Buscar produtos complementares (PDP):")
        print("   GET /recommendations/complementary/{product_id}?context_type=PDP&limit=10")
        print("   Headers: X-Session-ID: {session_id}")
        
        print("\n2. Buscar produtos complementares (Carrinho):")
        print("   GET /recommendations/complementary/{product_id}?context_type=CART&limit=5")
        
        print("\n3. Filtrar por categoria e estoque:")
        print("   GET /recommendations/complementary/{product_id}?category=eletrônicos&min_stock=10")
        
        print("\n4. Registrar conversão:")
        print("   POST /recommendations/outcome/{rec_set_id}?product_id={product_id}&outcome_type=purchase&outcome_value=99.90")
        
        print("\n5. Ver analytics:")
        print("   GET /recommendations/analytics?days_back=30")
        
        print("\n6. Verificar saúde do sistema:")
        print("   GET /recommendations/health")
        
    def print_admin_commands(self):
        """Imprime comandos úteis para administração"""
        print("\n=== COMANDOS DE ADMINISTRAÇÃO ===")
        
        print("1. Executar processamento batch manual:")
        print("   python batch_processor.py")
        
        print("\n2. Iniciar a API:")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        
        print("\n3. Executar atualização diária:")
        print("   # Agendar com cron:")
        print("   # 0 2 * * * cd /path/to/api && python -c \"import asyncio; from batch_processor import BatchProcessor; asyncio.run(BatchProcessor().run_daily_update())\"")
        
        print("\n4. Monitorar logs:")
        print("   tail -f logs/complementary_api.log")
        
        print("\n5. Limpar cache Redis:")
        print("   redis-cli FLUSHDB")


async def main():
    """Função principal"""
    initializer = SystemInitializer()
    
    print("🚀 INICIALIZADOR DO SISTEMA DE PRODUTOS COMPLEMENTARES")
    print("=" * 60)
    
    # Verificar ambiente
    if not await initializer.check_environment():
        print("\n❌ Problemas no ambiente detectados. Corrija e tente novamente.")
        return
        
    # Perguntar ao usuário o que fazer
    print("\nO que você gostaria de fazer?")
    print("1. Configuração inicial completa (recomendado para primeira execução)")
    print("2. Apenas demonstração da API (assumindo que já foi configurado)")
    print("3. Mostrar exemplos de uso")
    print("4. Mostrar comandos de administração")
    print("5. Sair")
    
    try:
        choice = input("\nEscolha uma opção (1-5): ").strip()
    except KeyboardInterrupt:
        print("\n\n👋 Operação cancelada pelo usuário")
        return
        
    if choice == "1":
        success = await initializer.run_initial_setup()
        if success:
            print("\n🎉 Sistema configurado com sucesso!")
            print("   Agora você pode iniciar a API com: uvicorn main:app --reload")
            await initializer.run_demo()
        else:
            print("\n❌ Falha na configuração inicial")
            
    elif choice == "2":
        await initializer.run_demo()
        
    elif choice == "3":
        initializer.print_usage_examples()
        
    elif choice == "4":
        initializer.print_admin_commands()
        
    elif choice == "5":
        print("\n👋 Até logo!")
        
    else:
        print("\n❌ Opção inválida")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()