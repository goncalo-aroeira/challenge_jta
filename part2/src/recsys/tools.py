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
