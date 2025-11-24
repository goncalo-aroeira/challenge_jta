# Testing the LLM Agent with Function Calling

## ✅ Implementações Completadas

### 1. **Documento de Arquitetura** (`docs/ARCHITECTURE_DECISIONS.md`)
   - ADR-001: Arquitetura Híbrida (Function Calling + LangChain SQL Agent)
   - ADR-002: Estratégia de Embeddings e Text Blob
   - ADR-003: Escalabilidade para Milhares de Tabelas
   - ADR-004: Logging e Observabilidade
   - ADR-005: Security e Rate Limiting

### 2. **Core Tools** (`src/recsys/tools.py`)
   - ✅ `search_products()` - Busca com filtros (store, age, franchise, segment)
   - ✅ `get_product_details()` - Detalhes de produto específico
   - ✅ `get_cooccurrence_neighbors()` - Produtos comprados juntos
   - ✅ `find_similar_products()` - Produtos similares (usa co-occurrence como proxy)
   - ✅ `get_product_by_name_fuzzy()` - Busca fuzzy por nome

### 3. **Agent com Function Calling** (`src/agent/core.py`)
   - ✅ Agentic loop com OpenAI Function Calling
   - ✅ Decide automaticamente quais ferramentas usar
   - ✅ Múltiplas iterações se necessário
   - ✅ Tracking integrado de queries

### 4. **System Prompt Melhorado** (`src/agent/prompts.py`)
   - ✅ Instruções claras sobre cada ferramenta
   - ✅ Guidelines de quando usar cada tool
   - ✅ Special cases (unrelated queries, unclear requests, no results)
   - ✅ Limitações explícitas

### 5. **Sistema de Logging** (`src/utils/tracking.py`)
   - ✅ QueryLog dataclass
   - ✅ QueryTracker para tracking de queries
   - ✅ Métricas: response time, tools usadas, produtos retornados
   - ✅ Estatísticas agregadas

---

## 🚀 Como Testar

### Pré-requisitos

1. **OpenAI API Key:**
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

2. **Ambiente Virtual Ativo:**
   ```bash
   source /home/goncalo/challenge_jta/.venv/bin/activate
   ```

3. **Database Configurada:**
   O sistema espera PostgreSQL com os dados já carregados (parte do ETL anterior).

---

### Teste 1: Ferramentas Individuais

```bash
cd /home/goncalo/challenge_jta/part2
python -m src.recsys.tools
```

**Output esperado:**
```
=== Testing recsys/tools.py ===

1. Search products for kids at Store A:
  - Animal Crossing: New Horizons (Age: 3+)
  - Super Mario Odyssey (Age: 7+)
  - Mario Kart 8 Deluxe (Age: 6+)

2. Get details of product ID 1:
  - Animal Crossing: New Horizons
  - Franchise: Animal Crossing
  - Stores: A=500000, B=300000, C=0

3. Products bought with product ID 1:
  - Nintendo Switch Pro Controller (co-occurrence: 200000)
  - Nintendo Switch (co-occurrence: 200000)
  - Joy-Con Controllers (Pair) (co-occurrence: 100000)

4. Fuzzy search for 'Mario':
  - Super Mario Odyssey
  - Mario Kart 8 Deluxe
  - Mario Party Superstars

=== All tests passed! ===
```

---

### Teste 2: Agent com Function Calling

```bash
cd /home/goncalo/challenge_jta/part2
python test_agent.py
```

**Queries testadas:**

1. **Unrelated Query (do README):**
   ```
   "I want a pepperoni pizza with extra cheese please."
   ```
   **Comportamento esperado:** Agent detecta que é irrelevante e responde educadamente

2. **Simple Search:**
   ```
   "I want games for a 5 year old child at Store A"
   ```
   **Comportamento esperado:** Usa `search_products(store="Store A", max_age=5)`

3. **Complex Query (do README):**
   ```
   "I want to buy a game for my nephew, at Store A, who is 5 years old.
    We loved Super Mario Odyssey, but I cannot buy a game from this family 
    as he already has all Super Mario games."
   ```
   **Comportamento esperado:**
   - Usa `get_product_by_name_fuzzy("Super Mario Odyssey")` para encontrar o ID
   - Usa `get_cooccurrence_neighbors(product_id)` para encontrar jogos comprados juntos
   - Usa `search_products(store="Store A", max_age=5, exclude_franchise="Super Mario")`
   - Combina resultados e recomenda

4. **Similar Products:**
   ```
   "What games are similar to Animal Crossing?"
   ```
   **Comportamento esperado:**
   - Usa `get_product_by_name_fuzzy("Animal Crossing")`
   - Usa `find_similar_products(product_id)`

**Output esperado:**
```
============================================================
TESTING AGENT WITH FUNCTION CALLING
============================================================

...

============================================================
QUERY TRACKER STATISTICS
============================================================
Total Queries: 4
Success Rate: 100.0%
Avg Response Time: 2500ms
Avg Products Returned: 8.5
Fallback Usage: 0.0%

Tool Usage:
  - search_products: 3 calls
  - get_product_by_name_fuzzy: 2 calls
  - get_cooccurrence_neighbors: 1 call
  - find_similar_products: 1 call
============================================================
```

---

### Teste 3: Tracking System

```bash
cd /home/goncalo/challenge_jta/part2
python -m src.utils.tracking
```

**Output esperado:**
```
Testing QueryTracker...

============================================================
QUERY TRACKER STATISTICS
============================================================
Total Queries: 2
Success Rate: 100.0%
Avg Response Time: 182ms
Avg Products Returned: 2.5
Fallback Usage: 0.0%

Tool Usage:
  - search_products: 1 calls
============================================================

✓ QueryTracker test completed
```

---

## 📊 Verificar Dados no Banco

Para verificar se os logs estão sendo salvos:

```sql
-- Ver últimas queries
SELECT * FROM query_logs ORDER BY timestamp DESC LIMIT 10;

-- Estatísticas de ferramentas
SELECT 
    jsonb_array_elements_text(tools_called) as tool,
    COUNT(*) as usage_count
FROM query_logs
GROUP BY tool
ORDER BY usage_count DESC;

-- Performance por sucesso
SELECT 
    success,
    AVG(response_time_ms) as avg_time,
    COUNT(*) as count
FROM query_logs
GROUP BY success;
```

---

## 🔍 Debugging

Se algo não funcionar:

1. **Erro de módulo não encontrado:**
   ```bash
   # Certifica-te que estás no diretório correto
   cd /home/goncalo/challenge_jta/part2
   
   # Usa python -m para importar como módulo
   python -m src.agent.core
   ```

2. **Erro de OpenAI API:**
   ```bash
   # Verifica se a chave está definida
   echo $OPENAI_API_KEY
   
   # Se não estiver, define:
   export OPENAI_API_KEY="sk-..."
   ```

3. **Erro de Database:**
   ```bash
   # Testa a conexão
   python -m src.utils.test_connection
   ```

4. **Ver logs detalhados:**
   O agent já imprime logs detalhados no terminal durante a execução.

---

## 📈 Próximos Passos (Fase 2)

Conforme documentado em `ARCHITECTURE_DECISIONS.md`:

1. **Embeddings + Vector Search:**
   - Gerar embeddings dos text_blobs (apenas contexto único)
   - Setup pgvector ou Pinecone
   - Implementar `find_similar_by_embedding()`

2. **LangChain SQL Agent como Fallback:**
   - Adicionar para queries não previstas
   - Logging de fallbacks para criar novas ferramentas

3. **Caching:**
   - Redis para cache de queries frequentes
   - In-memory cache para ferramentas

4. **Melhorias no Text Blob:**
   - Adicionar customer insights reais
   - Store exclusives
   - Cross-sell patterns

5. **Dashboard de Analytics:**
   - Grafana + PostgreSQL
   - Métricas em tempo real
   - A/B testing

---

## 📝 Notas Importantes

- **MVP Atual:** Function calling puro, sem embeddings (conforme ADR-002)
- **Co-occurrence como proxy:** `find_similar_products()` usa co-occurrence até embeddings serem implementados
- **Logging:** Todas as queries são tracked, mas salvar no DB depende da tabela `query_logs` existir
- **Token usage:** Tracking de tokens depende da resposta da OpenAI incluir `usage`

---

## ✅ Checklist de Implementação

- [x] Documento de decisões arquiteturais (ARCHITECTURE_DECISIONS.md)
- [x] 5 core tools implementadas e testadas
- [x] Agent com function calling e agentic loop
- [x] System prompt melhorado
- [x] Sistema de logging e tracking
- [x] Testes para unrelated query e complex query
- [ ] Embeddings + Vector search (Fase 2)
- [ ] LangChain SQL Agent fallback (Fase 2)
- [ ] Caching (Fase 2)
- [ ] Dashboard de analytics (Fase 2)

---

**Última atualização:** 2024-11-24  
**Autor:** Implementação baseada nos ADRs documentados
