import sys
import os
from typing import List, Optional, Dict, Any

# Add part2 root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from sqlalchemy import text
from src.config.database import engine


# ---------- Helpers internos ----------

def _map_store_to_column(store: Optional[str]) -> Optional[str]:
    """
    Traduz uma string de loja ('Store A', 'A', 'store_a') para o nome da coluna na BD.
    """
    if store is None:
        return None

    s = store.strip().lower()
    if s in ("store a", "a", "store_a"):
        return "store_a"
    if s in ("store b", "b", "store_b"):
        return "store_b"
    if s in ("store c", "c", "store_c"):
        return "store_c"

    # Caso não reconheça, devolve None (sem filtro de loja)
    return None


# ---------- Função 1: search_products ----------

def search_products(
    store: Optional[str] = None,
    max_age: Optional[int] = None,
    exclude_franchise: Optional[str] = None,
    segment: Optional[str] = "Games",
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Procura produtos na tabela 'products' com vários filtros.

    Pensada para ser usada como 'tool' pelo LLM:
      - store: 'Store A', 'Store B', 'Store C' (ou None para qualquer)
      - max_age: idade máxima da criança (filtra min_age <= max_age)
      - exclude_franchise: ex. 'Super Mario' (exclui essa franchise)
      - segment: normalmente 'Games' para só recomendar jogos
      - limit: número máximo de resultados

    Retorna uma lista de dicts com info relevante para recomendações.
    """

    store_col = _map_store_to_column(store)

    where_clauses = []
    params = {}

    # Filtrar por segmento (Games, Console, Accessories)
    if segment is not None:
        where_clauses.append("segment = :segment")
        params["segment"] = segment

    # Filtrar por idade
    if max_age is not None:
        where_clauses.append("min_age <= :max_age")
        params["max_age"] = max_age

    # Excluir franchise específica
    if exclude_franchise:
        where_clauses.append("franchise <> :exclude_franchise")
        params["exclude_franchise"] = exclude_franchise

    # Filtrar por loja (produto tem de ter vendas > 0 nessa loja)
    order_by = "popularity_global DESC"
    if store_col:
        where_clauses.append(f"{store_col} > 0")
        order_by = f"{store_col} DESC, popularity_global DESC"

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = f"""
        SELECT
            product_id,
            name,
            segment,
            category,
            type,
            franchise,
            min_age,
            popularity_global,
            text_blob
        FROM products
        {where_sql}
        ORDER BY {order_by}
        LIMIT :limit
    """
    params["limit"] = limit

    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
        return [dict(r) for r in rows]


# ---------- Função 2: get_product_details ----------

def get_product_details(product_id: Optional[int] = None, product_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Obtém detalhes completos de um produto específico.
    
    Args:
        product_id: ID do produto (prioritário)
        product_name: Nome do produto (usado se product_id não fornecido)
    
    Returns:
        Dict com info do produto ou None se não encontrado
    """
    if product_id is None and product_name is None:
        return None
    
    with engine.connect() as conn:
        if product_id:
            sql = """
                SELECT 
                    product_id,
                    name,
                    segment,
                    category,
                    type,
                    franchise,
                    min_age,
                    popularity_global,
                    times_sold,
                    store_a,
                    store_b,
                    store_c,
                    text_blob
                FROM products
                WHERE product_id = :product_id
            """
            result = conn.execute(text(sql), {"product_id": product_id}).mappings().first()
        else:
            # Busca por nome (case-insensitive, exact match)
            sql = """
                SELECT 
                    product_id,
                    name,
                    segment,
                    category,
                    type,
                    franchise,
                    min_age,
                    popularity_global,
                    times_sold,
                    store_a,
                    store_b,
                    store_c,
                    text_blob
                FROM products
                WHERE LOWER(name) = LOWER(:name)
                LIMIT 1
            """
            result = conn.execute(text(sql), {"name": product_name}).mappings().first()
        
        return dict(result) if result else None


# ---------- Função 3: get_cooccurrence_neighbors ----------

def get_cooccurrence_neighbors(product_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Encontra produtos frequentemente comprados junto com o produto dado.
    
    Args:
        product_id: ID do produto de referência
        limit: Número máximo de produtos a retornar
    
    Returns:
        Lista de produtos ordenados por frequência de co-ocorrência
    """
    sql = """
        SELECT 
            p.product_id,
            p.name,
            p.segment,
            p.franchise,
            p.min_age,
            p.popularity_global,
            c.cooccurrence_count
        FROM product_cooccurrence c
        JOIN products p ON p.product_id = c.product_id_2
        WHERE c.product_id_1 = :product_id
        ORDER BY c.cooccurrence_count DESC
        LIMIT :limit
    """
    
    with engine.connect() as conn:
        rows = conn.execute(
            text(sql), 
            {"product_id": product_id, "limit": limit}
        ).mappings().all()
        return [dict(r) for r in rows]


# ---------- Função 4: find_similar_products (Placeholder) ----------

def find_similar_products(product_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Encontra produtos similares baseado em características.
    
    NOTA: Esta é uma versão placeholder que usa co-occurrence como proxy.
    Na Fase 2, será substituída por vector similarity (embeddings).
    
    Args:
        product_id: ID do produto de referência
        limit: Número máximo de produtos similares
    
    Returns:
        Lista de produtos similares
    """
    # Por agora, usa co-occurrence como proxy de similaridade
    return get_cooccurrence_neighbors(product_id, limit)


# ---------- Função 5: get_product_by_name_fuzzy ----------

def get_product_by_name_fuzzy(name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Busca produtos por nome (fuzzy matching).
    Útil quando o user menciona um jogo mas não sabe o nome exato.
    
    Args:
        name: Nome parcial do produto
        limit: Número máximo de resultados
    
    Returns:
        Lista de produtos que correspondem ao pattern
    """
    sql = """
        SELECT 
            product_id,
            name,
            segment,
            franchise,
            min_age,
            popularity_global
        FROM products
        WHERE name ILIKE :pattern
        ORDER BY popularity_global DESC
        LIMIT :limit
    """
    
    with engine.connect() as conn:
        rows = conn.execute(
            text(sql), 
            {"pattern": f"%{name}%", "limit": limit}
        ).mappings().all()
        return [dict(r) for r in rows]


# ---------- Teste das Funções ----------

if __name__ == "__main__":
    print("=== Testing recsys/tools.py ===\n")
    
    # Test 1: search_products
    print("1. Search products for kids at Store A:")
    results = search_products(store="Store A", max_age=7, limit=3)
    for r in results:
        print(f"  - {r['name']} (Age: {r['min_age']}+)")
    
    # Test 2: get_product_details
    print("\n2. Get details of product ID 1:")
    details = get_product_details(product_id=1)
    if details:
        print(f"  - {details['name']}")
        print(f"  - Franchise: {details['franchise']}")
        print(f"  - Stores: A={details['store_a']}, B={details['store_b']}, C={details['store_c']}")
    
    # Test 3: get_cooccurrence_neighbors
    print("\n3. Products bought with product ID 1:")
    neighbors = get_cooccurrence_neighbors(product_id=1, limit=3)
    for n in neighbors:
        print(f"  - {n['name']} (co-occurrence: {n['cooccurrence_count']})")
    
    # Test 4: fuzzy search
    print("\n4. Fuzzy search for 'Mario':")
    fuzzy = get_product_by_name_fuzzy("Mario", limit=3)
    for f in fuzzy:
        print(f"  - {f['name']}")
    
    print("\n=== All tests passed! ===")
