import sys
import os
import pandas as pd

# Add part2 root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.config.database import engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, "../../data/Nintendo_Cooccurrence_Matrix.xlsx")

def main():
    # 1. Ler a matriz de co-ocorrência
    df_matrix = pd.read_excel(EXCEL_PATH, index_col=0)

    # 2. Diagonal → solo_sales
    coocc_long = df_matrix.stack().reset_index()
    coocc_long.columns = ["product_1", "product_2", "count"]

    solo_sales = coocc_long[coocc_long["product_1"] == coocc_long["product_2"]].copy()
    solo_sales = solo_sales[["product_1", "count"]]
    solo_sales.columns = ["product_name", "solo_sales"]

    # 3. Co-ocorrências (sem diagonal, sem zeros)
    coocc_edges = coocc_long[coocc_long["product_1"] != coocc_long["product_2"]].copy()
    coocc_edges = coocc_edges[coocc_edges["count"] > 0].copy()

    # Simplificar para uma só entrada por par (não-direcional)
    coocc_edges["product_min"] = coocc_edges[["product_1", "product_2"]].min(axis=1)
    coocc_edges["product_max"] = coocc_edges[["product_1", "product_2"]].max(axis=1)
    coocc_undirected = (
        coocc_edges
        .groupby(["product_min", "product_max"], as_index=False)["count"]
        .sum()
    )
    coocc_undirected.rename(
        columns={"product_min": "product_1", "product_max": "product_2"},
        inplace=True,
    )

    # 4. Gravar para tabelas temporárias no Postgres (por agora só com nomes)
    with engine.begin() as conn:
        coocc_undirected.to_sql(
            "product_cooccurrence_raw",
            conn,
            if_exists="replace",
            index=False,
        )
        solo_sales.to_sql(
            "product_solo_sales_raw",
            conn,
            if_exists="replace",
            index=False,
        )

    print("Dados de co-ocorrência e solo_sales carregados (tabelas *_raw).")

if __name__ == "__main__":
    main()
