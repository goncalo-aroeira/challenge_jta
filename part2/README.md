# Part II — LLM-Driven Recommendation System

## Contexto

Este exercício avalia a capacidade de:

- Trabalhar numa área nova,
- Pensar em escala,
- Estruturar dados para sistemas inteligentes,
- Conceptualizar arquiteturas de recomendação,
- Aplicar grandes modelos de linguagem (LLMs) de forma agentic.

Foram fornecidos dois ficheiros:

1. **Um ficheiro JSON** com informação de produtos da Nintendo Switch  
   Inclui:
   - `times_sold`
   - `Store_A`, `Store_B`, `Store_C`
   - Descrições e características gerais

2. **Um ficheiro Excel** com uma *co-occurrence matrix*  
   - Células não diagonais: número de vezes que dois produtos foram vendidos juntos  
   - Células diagonais: vendas isoladas de cada produto

---

## Objetivo

Criar um sistema de recomendações baseado em LLMs capaz de:

- Interpretar pedidos simples ou complexos
- Efetuar planeamento (agentic loop)
- Consultar dados estruturados
- Gerar recomendações personalizadas

O output esperado é:

- Conceitos técnicos
- Código funcional
- Estruturas de dados adequadas
- Demonstrações via consultas (unrelated, complex queries)
- Descrição de limitações e próximos passos

---

## Tarefas Principais

### 1. Estruturação dos Dados

Deves transformar os ficheiros fornecidos em estruturas eficientes:

- Tabelas de produtos
- Tabelas (ou grafos) de co-ocorrências
- Uma camada de embeddings para similaridade
- Índices para filtros (store, faixa etária, categorias)
- Possivelmente um vector store para suporte semântico

Cada estrutura deve ser pensada com foco em:

- Consultas rápidas
- Escalabilidade para milhares de produtos
- Integração natural com LLMs

---

## 2. Sistema Agentic LLM

Criar um fluxo composto por:

### a) Módulo de interpretação (Intent Parser)

O LLM analisa texto e extrai:

- Objetivo do utilizador  
- Restrições (idade, loja, exclusões, estilos, etc.)
- Produtos mencionados
- Preferências

### b) Planner / Router

Decide:

- Que ferramentas chamar
- Que dados recuperar
- Como construir uma recomendação coerente

### c) Tool Layer

Funções acessíveis pelo LLM, incluindo:

- `get_product(name)`
- `find_similar(product_id)`
- `cooccurrence_neighbors(product_id)`
- `filter_by_constraints(products, constraints)`

### d) LLM Final Answer Generator

Gera uma recomendação natural, clara e justificada.

---

## 3. QA / Testes

O sistema deve demonstrar capacidade de lidar com:

### Unrelated Query
Exemplo:
> "I want a pepperoni pizza with extra cheese please."

Resposta esperada:
- Detetar que é irrelevante
- Responder educadamente
- Não inventar recomendações irrelevantes

### Complex Query
Exemplo:
> "I want to buy a game for my nephew, at Store A, who is 5 years old.  
> We loved Super Mario Odyssey, but I cannot buy a game from this family as he already has all Super Mario games."

Resposta esperada:
- Interpretar idade, loja, produto de referência, restrições
- Usar similaridade + coocorrência + filtros
- Produzir recomendações adequadas

---

## 4. Limitações e Próximos Passos

O relatório deve incluir:

- Problemas conhecidos (dados esparsos, cold start)
- Métricas necessárias em cenário real
- Considerações de performance
- Como escalar para milhões de interações
- Estratégias para:
  - vector search
  - caching
  - compressão de histórico
  - modelos sequenciais (SASRec, transformers, etc.)

---

## 5. What-If Scenario

Preparar discussão sobre:

> Como adaptar o sistema se tivéssemos acesso ao historial completo do cliente,  
> onde cada recomendação depende de todas as interações anteriores?

Considerar:

- Sistemas sequenciais
- Cold start
- Modelos híbridos LLM + embeddings sequenciais
- Summarization de long histories

---

## Entregáveis Recomendações

- Código + notebook demonstrativo
- Arquitectura explicada
- Ficheiros resultantes da preparação de dados
- Exemplos de queries
- README (este ficheiro)

---
