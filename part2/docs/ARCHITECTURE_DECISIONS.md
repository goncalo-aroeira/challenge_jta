# Architecture Decision Records (ADR)

## Contexto Geral

Este documento regista as principais decisões arquiteturais tomadas no desenvolvimento do sistema de recomendações LLM-Driven para produtos Nintendo Switch. O objetivo é documentar não apenas o que foi escolhido, mas também **o que foi rejeitado e porquê**.

---

## ADR-001: Arquitetura Híbrida - Function Calling + LangChain SQL Agent

**Data:** 2024-11-24  
**Status:** ✅ ACEITE (implementação em 2 fases)  
**Decisores:** Equipa de Engenharia

### Problema

Como permitir que o LLM aceda a dados estruturados (PostgreSQL) de forma:
- **Flexível:** Suportar queries diversas e imprevistas
- **Segura:** Sem risco de SQL injection ou queries perigosas
- **Escalável:** Funcionar com 100 produtos e com 100.000 produtos
- **Controlável:** Não inventar dados quando não tem ferramentas adequadas

### Opções Consideradas

#### ❌ Opção 1: Function Calling Puro (OpenAI)

**Descrição:** Definir explicitamente 5-10 ferramentas que o LLM pode chamar.

**Exemplo:**
```python
tools = [
    {"name": "search_products", "parameters": {"store": str, "max_age": int, ...}},
    {"name": "get_product_details", "parameters": {"product_id": int}},
    {"name": "get_cooccurrence_neighbors", "parameters": {"product_id": int}}
]
```

**Prós:**
- ✅ **Controlo total** sobre queries executadas
- ✅ **Segurança máxima** (queries validadas manualmente)
- ✅ **Performance otimizada** (queries escritas à mão)
- ✅ **Fácil debugging** e testes
- ✅ **Custo previsível** (chamadas LLM controladas)

**Contras:**
- ❌ **Inflexível** - precisa prever todas as queries possíveis
- ❌ **Manutenção alta** - adicionar ferramentas constantemente
- ❌ **Não escala** para casos edge (queries únicas/complexas)
- ❌ **User frustration** quando query não é suportada

**Exemplo de Falha:**
```
User: "Qual a percentagem de jogos indie vs AAA na Store A?"
Agent: "Desculpa, não consigo calcular percentagens." ❌
```

**Veredicto:** ⚠️ Aceite para **MVP/Fase 1**, mas insuficiente para produção.

---

#### ❌ Opção 2: RAG (Retrieval-Augmented Generation) Puro

**Descrição:** Embeddings de descrições de produtos + vector search para similaridade semântica.

**Fluxo:**
```
User Query → Embedding → Vector Search → Top-K produtos → LLM gera resposta
```

**Prós:**
- ✅ **Excelente para similaridade semântica** ("jogos parecidos com X")
- ✅ **Busca por descrições** ("jogos relaxantes", "aventuras épicas")
- ✅ **Rápido** com índices vetoriais (pgvector, Pinecone)

**Contras:**
- ❌ **Não aproveita dados estruturados** (min_age, store_a/b/c como colunas)
- ❌ **Queries numéricas imprecisas** (ex: "idade <= 7" depende de texto)
- ❌ **Não faz agregações** (COUNT, AVG, SUM)
- ❌ **Não faz filtros complexos** (exclusões, múltiplos ANDs)

**Exemplo de Falha:**
```
User: "Quantos jogos temos para menores de 7 anos na Store A?"
RAG: Busca docs similares, mas não consegue fazer COUNT WHERE age <= 7 AND store_a > 0 ❌
```

**Veredicto:** ❌ Rejeitado como solução única, mas **útil como componente** para similaridade.

---

#### ❌ Opção 3: LangChain SQL Agent Puro

**Descrição:** Agent que analisa o schema da DB e gera SQL dinamicamente.

**Exemplo:**
```python
from langchain.agents import create_sql_agent

agent = create_sql_agent(llm=llm, db=db)
agent.run("Jogos para menores de 7 anos na Store A")

# Internamente gera:
# SELECT * FROM products WHERE min_age <= 7 AND store_a > 0
```

**Prós:**
- ✅ **Extremamente flexível** - não precisa prever queries
- ✅ **Suporta queries complexas** (agregações, joins, subqueries)
- ✅ **Setup rápido** (3 linhas de código)
- ✅ **Escala naturalmente** com novas colunas/tabelas

**Contras:**
- ❌ **Menos controlo** sobre SQL gerado
- ❌ **Risco de queries ineficientes** (sem índices, full table scans)
- ❌ **Possível SQL injection** se não validado
- ❌ **Não faz busca semântica** (não usa embeddings)
- ❌ **Dependência de framework externo**

**Exemplo de Falha:**
```
User: "Jogos parecidos com Mario Odyssey"
SQL Agent: SELECT * FROM products WHERE name LIKE '%Mario%' ❌ (não entende "parecido")
```

**Veredicto:** ❌ Rejeitado como solução única, mas **útil como fallback** para edge cases.

---

#### ✅ Opção 4: Arquitetura Híbrida (ESCOLHIDO)

**Descrição:** Combinar os pontos fortes de cada abordagem em camadas.

**Arquitetura:**

```
                    User Query
                         ↓
        ┌────────────────────────────────┐
        │    Intent Classification       │
        │    (LLM analisa tipo query)    │
        └────────────┬───────────────────┘
                     ↓
         ┌───────────┴────────────┐
         │                        │
    Structured              Semantic/Complex
    (filtros, IDs)         (descrições, edge cases)
         │                        │
         ↓                        ↓
┌─────────────────┐      ┌──────────────────┐
│ Function Tools  │      │ Fallback Layer   │
│ (80% queries)   │      │ (20% queries)    │
│                 │      │                  │
│ - search_prod   │      │ - Vector Search  │
│ - get_details   │      │   (similaridade) │
│ - cooccurrence  │      │ - SQL Agent      │
│ - clarify       │      │   (queries adhoc)│
└────────┬────────┘      └────────┬─────────┘
         │                        │
         └────────────┬───────────┘
                      ↓
            ┌─────────────────┐
            │ Result Combiner │
            └────────┬────────┘
                     ↓
            ┌─────────────────┐
            │ Final Response  │
            │ (LLM synthesis) │
            └─────────────────┘
```

**Implementação em 2 Fases:**

**Fase 1 (MVP - ATUAL):**
- ✅ Function Calling com 5 ferramentas core
- ✅ System prompt forte que admite limitações
- ✅ Ferramenta de "ask_for_clarification" para casos ambíguos
- ❌ Sem SQL Agent (complexidade reduzida)
- ❌ Sem embeddings (co-occurrence serve de proxy)

**Fase 2 (Produção - FUTURO):**
- ✅ Adiciona LangChain SQL Agent como fallback
- ✅ Adiciona vector search para similaridade semântica
- ✅ Logging de fallbacks → cria novas ferramentas para padrões comuns
- ✅ Caching de queries frequentes

**Decisão de Routing:**
```python
def route_query(query: str, intent: UserIntent) -> str:
    # Queries estruturadas simples → Function Calling
    if intent.has_simple_filters():
        return "function_calling"
    
    # Queries semânticas → Vector Search
    if "similar" in query or "like" in query or "parecido" in query:
        return "vector_search"
    
    # Queries complexas/únicas → SQL Agent
    if intent.requires_aggregation() or intent.is_complex():
        return "sql_agent"
    
    # Default
    return "function_calling"
```

### Consequências

**Positivas:**
- ✅ **Controlo total no MVP** (function calling)
- ✅ **Path claro para escalar** (adicionar layers conforme necessário)
- ✅ **Não inventa dados** (admite limitações)
- ✅ **Aprende com uso real** (logs revelam patterns)
- ✅ **Cada layer tem responsabilidade clara**

**Negativas:**
- ❌ **Mais código** para manter (3 estratégias)
- ❌ **Complexidade de routing** (decidir qual layer usar)
- ❌ **Precisa monitoring** robusto para identificar padrões

**Riscos Mitigados:**
- Function calling evita SQL injection ✅
- Embeddings (Fase 2) melhoram recomendações além de co-occurrence ✅
- Fallback previne respostas "não consigo ajudar" ✅

**Métricas de Sucesso:**
- 80%+ queries resolvidas por function calling
- Latência < 500ms para queries comuns
- 0 casos de SQL injection
- Customer satisfaction > 4/5

---

## ADR-002: Estratégia de Embeddings e Text Blob

**Data:** 2024-11-24  
**Status:** ⏸️ ADIADO para Fase 2  
**Decisores:** Equipa de Engenharia

### Problema

Produtos têm campo `text_blob` com descrições. Questões:
1. **O text_blob adiciona valor** ou é redundante com conhecimento do LLM?
2. **Devemos implementar embeddings** no MVP?
3. **Que informação incluir** no text_blob para maximizar valor?

### Análise: Informação Redundante vs Única

| Tipo de Informação | Exemplo | LLM já conhece? | Incluir no embedding? |
|-------------------|---------|-----------------|----------------------|
| Nome do jogo | "Super Mario Odyssey" | ✅ Sim | ✅ Sim (identificador) |
| Gameplay/Mecânicas | "3D platformer where Mario uses Cappy to possess enemies" | ✅ Sim (treino até 2023) | ❌ **NÃO** (redundante) |
| Género | "Adventure, Platform" | ✅ Sim | ✅ Sim (estruturado) |
| Ano de lançamento | "Released in 2017" | ✅ Sim | ❌ NÃO (irrelevante para recomendação) |
| Publisher | "Nintendo" | ✅ Sim | ❌ NÃO |
| **Co-occurrence** | "Frequently bought with Zelda BotW, Mario Kart 8" | ❌ **NÃO** | ✅ **SIM** (único!) |
| **Customer insights** | "Most popular gift for ages 8-12, often for birthdays" | ❌ **NÃO** | ✅ **SIM** (único!) |
| **Store exclusives** | "Store A exclusive: includes bonus amiibo card" | ❌ **NÃO** | ✅ **SIM** (único!) |
| **Local availability** | "High stock at Store B, low at Store C" | ❌ **NÃO** | ✅ **SIM** (único!) |

**Conclusão:** ~70% do text_blob típico é **redundante**.

### Decisão: Text Blob Minimalista + Adiamento de Embeddings

#### **Para MVP (Fase 1):**

**Text Blob:**
- ❌ **Remover** descrições de gameplay que o LLM já conhece
- ✅ **Manter APENAS** informação comercial única:
  - Promoções/bundles específicos da loja
  - Customer insights ("popular gift for X demographics")
  - Cross-sell patterns ("bought with Y, Z")
  - Store exclusives

**Embeddings:**
- ⏸️ **NÃO implementar no MVP**
- Usar **co-occurrence** como proxy de similaridade
- Avaliar necessidade baseado em feedback real

**Rationale:**
1. MVP mais simples e rápido de implementar
2. Validar se users fazem queries semânticas frequentes
3. Co-occurrence já fornece "similar products" básico
4. Economiza tokens e storage

#### **Para Produção (Fase 2):**

**Implementar embeddings SE:**
- ✅ Text blobs forem enriquecidos com dados únicos
- ✅ Queries de "similaridade semântica" forem >15% do total
- ✅ Co-occurrence for insuficiente (e.g., novos produtos sem histórico)

**Fórmula do Embedding Text (quando implementar):**

```python
def create_embedding_text(product: dict, cooccurrence_top3: list) -> str:
    """
    Cria texto para embedding focado em informação ÚNICA.
    """
    parts = [f"{product['name']} ({product['segment']}, {product['franchise']})"]
    
    # Co-occurrence insights
    if cooccurrence_top3:
        parts.append(
            f"Frequently bought with: {', '.join([p['name'] for p in cooccurrence_top3])}"
        )
    
    # Age demographic
    if product['min_age'] <= 7:
        parts.append("Popular with young children and families")
    elif product['min_age'] <= 12:
        parts.append("Popular with pre-teens")
    
    # Store context (se houver exclusives/promos)
    if product.get('store_exclusive_features'):
        parts.append(product['store_exclusive_features'])
    
    return ". ".join(parts)
```

**Exemplo Output:**
```
"Super Mario Odyssey (Games, Super Mario). 
Frequently bought with: Mario Kart 8, Zelda BotW, Splatoon 2. 
Popular with pre-teens. 
Store A exclusive: includes limited edition hat pin."
```

### Alternativas Rejeitadas

#### ❌ Opção A: Embeddings desde o Início
- **Prós:** Similaridade semântica desde dia 1
- **Contras:** Overhead técnico, pode não adicionar valor se text_blob for redundante
- **Decisão:** Adiado - validar necessidade primeiro

#### ❌ Opção B: Text Blob Detalhado (gameplay completo)
- **Prós:** Máxima informação
- **Contras:** 70% redundante, desperdício de tokens/storage
- **Decisão:** Rejeitado

#### ✅ Opção C: Text Blob Minimalista (ESCOLHIDO)
- **Prós:** Sem redundância, foca em contexto único
- **Contras:** Requer curadoria de dados
- **Decisão:** Aceite com campos estruturados adicionais

### Consequências

**Positivas:**
- ✅ MVP mais simples (uma preocupação a menos)
- ✅ Não gastamos tokens com info redundante
- ✅ Path claro para adicionar embeddings baseado em dados reais

**Negativas:**
- ❌ Similaridade limitada a co-occurrence no MVP
- ❌ Queries tipo "jogos relaxantes" não funcionam bem sem embeddings
- ❌ Cold start problem para produtos novos (sem co-occurrence)

---

## ADR-003: Escalabilidade para Milhares de Tabelas

**Data:** 2024-11-24  
**Status:** 📋 PLANEAMENTO (não aplicável ao MVP)  
**Contexto:** Preparação para escala futura

### Problema

**Cenário atual:** ~10 tabelas (products, cooccurrence, etc.)  
**Cenário futuro hipotético:** 1000+ tabelas em DB empresarial

**Desafio:**
```
Schema completo de 1000 tabelas: ~2.5 milhões de tokens
Context window GPT-4: 128k tokens
Resultado: Schema não cabe! ❌
```

Mesmo que coubesse, seria ineficiente (custo de tokens, latência).

### Decisão: Estratégia por Escala

#### **< 50 Tabelas (ATUAL):**
✅ **Approach:** Schema completo no context

```python
agent = create_sql_agent(llm=llm, db=db)  # Vê todas as tabelas
```

**Rationale:** Simples, funciona perfeitamente.

---

#### **50-500 Tabelas:**
✅ **Approach:** Schema RAG (Retrieval-Augmented Generation)

**Implementação:**
```python
# 1. Criar embeddings do schema
schema_docs = []
for table in db.tables:
    doc = f"""
    Table: {table.name}
    Description: {table.comment}
    Columns: {', '.join([f"{c.name}({c.type})" for c in table.columns])}
    Common queries: {table.example_queries}
    Related tables: {table.foreign_keys}
    """
    schema_docs.append(doc)

# 2. Vector store do schema
schema_vectorstore = Pinecone.from_documents(
    schema_docs, 
    embeddings,
    namespace="db_schema"
)

# 3. Query flow
def smart_sql_agent(query: str):
    # 3a. RAG: Encontra tabelas relevantes
    relevant_tables = schema_vectorstore.similarity_search(query, k=5)
    
    # 3b. Cria mini-schema só com essas 5 tabelas
    mini_schema = {t.name: t.columns for t in relevant_tables}
    
    # 3c. SQL Agent vê apenas essas tabelas
    agent = create_sql_agent(
        llm=llm,
        db=db,
        include_tables=[t.name for t in relevant_tables]
    )
    
    return agent.run(query)
```

**Vantagens:**
- ✅ Schema completo cabe no context (só 5 tabelas)
- ✅ LLM vê apenas o relevante
- ✅ Reduz tokens de 2.5M → 10K
- ✅ Mais rápido

**Exemplo:**
```
Query: "Jogos mais vendidos na Store A"

RAG encontra: [products, sales, stores, inventory, categories]
↓
SQL Agent vê apenas essas 5 tabelas
↓
Gera: SELECT p.name, SUM(s.quantity) FROM products p 
      JOIN sales s ON p.id = s.product_id 
      WHERE s.store_id = 'A'
      GROUP BY p.name ORDER BY SUM DESC LIMIT 10
```

---

#### **> 500 Tabelas:**
✅ **Approach:** Hierarchical Routing + Schema RAG

**Implementação:**
```python
# 1. Organizar tabelas em domínios
domains = {
    "products": ["products", "categories", "brands", "inventory"],
    "sales": ["orders", "transactions", "revenue", "discounts"],
    "customers": ["users", "profiles", "addresses", "preferences"],
    "analytics": ["metrics", "kpis", "dashboards", "reports"]
}

# 2. Router identifica domínio
def route_to_domain(query: str) -> str:
    router_prompt = f"""
    Classify this query into a domain: {list(domains.keys())}
    
    Query: {query}
    """
    domain = llm.classify(router_prompt)
    return domain

# 3. Schema RAG dentro do domínio
def hierarchical_agent(query: str):
    # 3a. Identifica domínio (products, sales, etc.)
    domain = route_to_domain(query)
    
    # 3b. Schema RAG apenas nesse domínio
    domain_tables = domains[domain]
    relevant_tables = schema_rag_within_domain(query, domain_tables, k=5)
    
    # 3c. SQL Agent focado
    agent = create_sql_agent(llm, db, include_tables=relevant_tables)
    return agent.run(query)
```

**Vantagens:**
- ✅ Escala para milhares de tabelas
- ✅ Routing barato (classificação simples)
- ✅ RAG focado (menos falsos positivos)

---

### Comparação de Escalabilidade

| Approach | Max Tabelas | Tokens no Context | Latência | Complexidade | Custo |
|----------|-------------|-------------------|----------|--------------|-------|
| Schema completo | ~50 | 50K | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |
| Schema RAG | ~500 | 10K | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Hierarchical + RAG | 1000+ | 5K | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Multi-Agent | 5000+ | 3K | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

### Alternativas Rejeitadas

#### ❌ Multi-Agent System (agent por domínio)
- **Prós:** Especialização máxima, paralelização possível
- **Contras:** Overhead de coordenação, hard to debug, complexo demais
- **Decisão:** Overkill exceto para >5000 tabelas

#### ❌ LLM gera SQL sem ver schema
- **Prós:** Zero overhead de retrieval
- **Contras:** Taxa de erro ~40% (testado), SQL inválido frequente
- **Decisão:** Rejeitado (precisa do schema)

---

## ADR-004: Logging, Observability e Continuous Improvement

**Data:** 2024-11-24  
**Status:** ✅ REQUISITO para MVP  
**Decisores:** Equipa de Engenharia + Product

### Problema

Como **aprender e melhorar** o sistema baseado em uso real?

**Questões:**
- Quais queries os users fazem mais?
- Que ferramentas são mais usadas?
- Quando o sistema falha?
- Que novas ferramentas criar?

### Decisão: Structured Logging de Todas as Interações

#### **Query Log Schema:**

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class QueryLog:
    # Metadata
    timestamp: datetime
    session_id: str
    
    # Query
    query: str
    intent_type: str  # search, recommendation, unrelated, etc.
    
    # Execution
    tools_called: List[str]  # ["search_products", "get_cooccurrence"]
    tool_arguments: Dict[str, Any]
    used_fallback: bool  # True se usou SQL Agent
    
    # Results
    products_returned: int
    response_time_ms: float
    llm_tokens_used: int
    success: bool
    
    # Feedback (se disponível)
    user_feedback: Optional[int]  # 1-5 stars
    user_clicked_product: Optional[int]  # product_id
```

#### **Database Table:**

```sql
CREATE TABLE query_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    session_id VARCHAR(100),
    
    -- Query
    query TEXT NOT NULL,
    intent_type VARCHAR(50),
    
    -- Execution
    tools_called JSONB,
    tool_arguments JSONB,
    used_fallback BOOLEAN DEFAULT FALSE,
    
    -- Results
    products_returned INT,
    response_time_ms INT,
    llm_tokens_used INT,
    success BOOLEAN,
    
    -- Feedback
    user_feedback INT CHECK (user_feedback BETWEEN 1 AND 5),
    user_clicked_product INT REFERENCES products(product_id)
);

CREATE INDEX idx_query_logs_timestamp ON query_logs(timestamp);
CREATE INDEX idx_query_logs_intent ON query_logs(intent_type);
CREATE INDEX idx_query_logs_success ON query_logs(success);
```

#### **Logging Implementation:**

```python
class QueryTracker:
    def __init__(self):
        self.current_log = None
    
    def start_query(self, query: str, session_id: str):
        self.current_log = QueryLog(
            timestamp=datetime.now(),
            session_id=session_id,
            query=query,
            intent_type=None,  # Preenchido depois
            tools_called=[],
            tool_arguments={},
            used_fallback=False,
            products_returned=0,
            response_time_ms=0,
            llm_tokens_used=0,
            success=False
        )
    
    def log_tool_call(self, tool_name: str, arguments: dict):
        self.current_log.tools_called.append(tool_name)
        self.current_log.tool_arguments[tool_name] = arguments
    
    def finish_query(self, success: bool, products_count: int, elapsed_ms: float):
        self.current_log.success = success
        self.current_log.products_returned = products_count
        self.current_log.response_time_ms = elapsed_ms
        self._save_to_db()
    
    def _save_to_db(self):
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO query_logs 
                (timestamp, session_id, query, intent_type, tools_called, 
                 tool_arguments, used_fallback, products_returned, 
                 response_time_ms, llm_tokens_used, success)
                VALUES 
                (:timestamp, :session_id, :query, :intent, :tools, 
                 :args, :fallback, :count, :time, :tokens, :success)
            """), {
                "timestamp": self.current_log.timestamp,
                "session_id": self.current_log.session_id,
                "query": self.current_log.query,
                "intent": self.current_log.intent_type,
                "tools": json.dumps(self.current_log.tools_called),
                "args": json.dumps(self.current_log.tool_arguments),
                "fallback": self.current_log.used_fallback,
                "count": self.current_log.products_returned,
                "time": self.current_log.response_time_ms,
                "tokens": self.current_log.llm_tokens_used,
                "success": self.current_log.success
            })
```

### Métricas a Monitorizar

#### **Operacionais:**
- **Latência:** P50, P95, P99 por tipo de query
- **Taxa de sucesso:** % queries que retornam resultados úteis
- **Taxa de fallback:** % queries que usam SQL Agent
- **Token usage:** Custo mensal de LLM calls

#### **Produto:**
- **Tool distribution:** Que ferramentas são mais usadas?
- **Intent distribution:** Que tipos de queries são mais comuns?
- **Failed queries:** Que queries falham frequentemente?
- **User satisfaction:** Feedback médio (quando disponível)

#### **Continuous Improvement:**
- **Pattern detection:** Queries similares que não têm ferramenta dedicada
- **New tool opportunities:** Se 5%+ queries usam fallback para o mesmo padrão → criar tool
- **A/B testing:** Testar diferentes system prompts, routing strategies

### Dashboard Exemplo

```sql
-- Queries mais comuns sem ferramenta dedicada
SELECT query, COUNT(*) as frequency
FROM query_logs
WHERE used_fallback = TRUE
GROUP BY query
ORDER BY frequency DESC
LIMIT 20;

-- Performance por intent type
SELECT 
    intent_type,
    AVG(response_time_ms) as avg_latency,
    AVG(products_returned) as avg_results,
    AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate
FROM query_logs
GROUP BY intent_type;

-- Tool usage distribution
SELECT tool, COUNT(*) as calls
FROM query_logs, jsonb_array_elements_text(tools_called) as tool
GROUP BY tool
ORDER BY calls DESC;
```

### Consequências

**Positivas:**
- ✅ Dados para decisões baseadas em evidência
- ✅ Identifica gaps na funcionalidade
- ✅ Permite A/B testing
- ✅ Tracking de custos (tokens)

**Negativas:**
- ❌ Overhead de logging (~5-10ms por query)
- ❌ Storage costs (mas barato)
- ❌ Privacy concerns (armazenar queries dos users)

---

## ADR-005: Security e Rate Limiting

**Data:** 2024-11-24  
**Status:** 📋 PLANEAMENTO (Fase 2)

### Problema

Proteger o sistema contra:
- SQL injection (mesmo com function calling)
- Rate limiting abuse
- Prompt injection attacks
- Cost explosion (token usage)

### Decisão: Defense in Depth

#### **Layer 1: Input Validation**
```python
def validate_query(query: str) -> bool:
    # Max length
    if len(query) > 500:
        raise ValueError("Query too long")
    
    # No SQL keywords in user input
    dangerous = ["DROP", "DELETE", "UPDATE", "ALTER", "EXEC"]
    if any(word in query.upper() for word in dangerous):
        raise SecurityError("Suspicious input detected")
    
    return True
```

#### **Layer 2: Parameterized Queries Only**
```python
# ✅ SEMPRE usar
conn.execute(text("SELECT * FROM products WHERE id = :id"), {"id": product_id})

# ❌ NUNCA fazer
conn.execute(f"SELECT * FROM products WHERE id = {product_id}")
```

#### **Layer 3: Rate Limiting**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def call_llm_with_retry(**kwargs):
    return client.chat.completions.create(**kwargs)

# Per-user rate limiting
RATE_LIMITS = {
    "free": {"calls_per_minute": 10, "calls_per_day": 100},
    "premium": {"calls_per_minute": 60, "calls_per_day": 1000}
}
```

#### **Layer 4: Cost Control**
```python
# Token budget por query
MAX_TOKENS_PER_QUERY = 4000

# Alert se custo mensal > threshold
MONTHLY_BUDGET_USD = 500

def check_budget():
    current_spend = get_current_month_spend()
    if current_spend > MONTHLY_BUDGET_USD * 0.8:
        alert_team("Approaching budget limit")
```

---

## Sumário de Decisões

| ADR | Decisão | Status | Fase | Rationale |
|-----|---------|--------|------|-----------|
| 001 | Híbrido Function Calling + SQL Agent | ✅ Aceite | MVP: FC only, Prod: Híbrido | Controlo + Flexibilidade |
| 002 | Text blob minimalista, embeddings Fase 2 | ⏸️ Adiado | MVP: Skip, Prod: Avaliar | Simplicidade, validar necessidade |
| 003 | Schema RAG se >50 tabelas | 📋 Planeamento | Futuro | Escalabilidade comprovada |
| 004 | Logging completo de queries | ✅ Requisito | MVP | Aprender e melhorar |
| 005 | Security layers + rate limiting | 📋 Planeamento | Fase 2 | Proteção essencial |

---

## Referências

- **OpenAI Function Calling:** https://platform.openai.com/docs/guides/function-calling
- **LangChain SQL Agent:** https://python.langchain.com/docs/integrations/toolkits/sql_database
- **RAG Patterns:** https://arxiv.org/abs/2005.11401
- **pgvector:** https://github.com/pgvector/pgvector
- **Schema RAG:** https://www.databricks.com/blog/llms-and-sql-databases

---

**Última atualização:** 2024-11-24  
**Próxima revisão:** Após MVP launch (baseado em dados reais de uso)
