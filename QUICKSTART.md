# 🚀 API de Produtos Complementares - Guia Rápido

## Como Executar (Modo Desenvolvimento)

### Opção 1: Inicialização Simples (Recomendado)

```bash
python start_simple.py
```

### Opção 2: Inicialização Completa

```bash
# Se você tem PostgreSQL, Redis e Elasticsearch configurados
python init_system.py

# OU apenas iniciar a API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🌐 Testando a API

### 1. Verificar se está funcionando

```bash
curl -X GET "http://localhost:8000/recommendations/health"
```

### 2. Buscar produtos populares

```bash
curl -X GET "http://localhost:8000/recommendations/popular?limit=5"
```

### 3. Buscar produtos complementares

```bash
# Use um product_id real dos dados Olist
curl -X GET "http://localhost:8000/recommendations/complementary/aca2eb7d00ea1a7b8ebd4e68314663af?context_type=PDP&limit=5" \
  -H "X-Session-ID: test_session_123"
```

### 4. Ver documentação interativa

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📊 Principais Endpoints

| Endpoint                                      | Método | Descrição               |
| --------------------------------------------- | ------ | ----------------------- |
| `/recommendations/health`                     | GET    | Status dos serviços     |
| `/recommendations/popular`                    | GET    | Produtos populares      |
| `/recommendations/complementary/{product_id}` | GET    | Produtos complementares |
| `/recommendations/outcome/{rec_set_id}`       | POST   | Log de conversão        |
| `/recommendations/analytics`                  | GET    | Métricas (requer auth)  |

## 🔧 Exemplos Avançados

### Filtros de Produtos Complementares

```bash
curl -X GET "http://localhost:8000/recommendations/complementary/PRODUTO123" \
  -G \
  -d "context_type=PDP" \
  -d "limit=10" \
  -d "min_stock=5" \
  -d "min_price=20.00" \
  -d "max_price=100.00" \
  -d "min_rating=4.0" \
  -H "X-Session-ID: session_abc"
```

### Log de Conversão

```bash
curl -X POST "http://localhost:8000/recommendations/outcome/12345" \
  -G \
  -d "product_id=PRODUTO456" \
  -d "outcome_type=purchase" \
  -d "outcome_value=89.90"
```

## 🎯 Como Funciona

### 1. Algoritmo de Coocorrência

- **Lift**: Mede associação entre produtos (>1.0 = correlação positiva)
- **NPMI**: Normaliza a associação (-1 a +1, onde >0 é positivo)

### 2. Sistema de Cache

- **Primeira busca**: Calcula em tempo real dos dados CSV
- **Buscas seguintes**: Usa cache em memória para velocidade

### 3. Filtros Inteligentes

- **Estoque**: Apenas produtos disponíveis
- **Preço**: Faixa configurável
- **Categoria**: Filtro específico
- **Avaliação**: Produtos bem avaliados

### 4. Rerank

- **Margem**: Produtos com maior margem têm prioridade
- **Diversidade**: Evita muitos produtos da mesma categoria
- **Contexto**: PDP vs Carrinho têm estratégias diferentes

## 🔍 IDs de Produtos para Teste

Use estes IDs reais dos dados Olist para testar:

```bash
# Produto popular
curl -X GET "http://localhost:8000/recommendations/complementary/aca2eb7d00ea1a7b8ebd4e68314663af"

# Outro produto
curl -X GET "http://localhost:8000/recommendations/complementary/422879e10f46682990de24d770e7f83d"

# Mais um produto
curl -X GET "http://localhost:8000/recommendations/complementary/368c6c730842d78016ad823897a372db"
```

## 📈 Métricas Importantes

### Response Time

- **Cache Hit**: ~50ms
- **Cache Miss**: ~200-500ms (dependendo do tamanho dos dados)

### Formatos de Resposta

```json
{
  "product_id": "abc123",
  "context_type": "PDP",
  "session_id": "sess_789",
  "rec_set_id": 12345,
  "recommendations": [
    {
      "product_id": "def456",
      "lift_score": 2.34,
      "npmi_score": 0.67,
      "cooccurrence_count": 234,
      "recommendation_reason": "Frequentemente comprados juntos (234+ pedidos)",
      "price": 89.9,
      "category": "eletrônicos"
    }
  ],
  "total": 1,
  "source": "complementary_algorithm"
}
```

## ⚡ Performance Tips

1. **Use o cache**: Faça a mesma busca duas vezes para ver a diferença
2. **Limite resultados**: Use `limit=5` para testes rápidos
3. **Context matters**: `PDP` vs `CART` têm comportamentos diferentes
4. **Session tracking**: Use `X-Session-ID` para tracking completo

## 🎉 Próximos Passos

1. **Teste básico**: Verifique se a API responde
2. **Explore dados**: Use `/popular` para encontrar produtos interessantes
3. **Teste complementares**: Use produtos reais para ver recomendações
4. **Simule conversões**: Use `/outcome` para simular compras
5. **Analise performance**: Compare cache hit vs miss

## 🆘 Troubleshooting

### API não inicia

- Verifique se a porta 8000 está livre: `lsof -i :8000`
- Use `python start_simple.py` para modo básico

### Nenhuma recomendação

- Use produtos populares primeiro: `/popular`
- Verifique se o product_id existe nos dados
- Teste com `limit=1` para começar simples

### Dados de teste

- Os dados Olist devem estar na pasta `ds/`
- Arquivos necessários: `olist_*.csv`

---

**✨ Pronto para testar!** Comece com `python start_simple.py` e explore a API.
