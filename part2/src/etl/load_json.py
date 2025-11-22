import sys
import os
import json
import pandas as pd

# Add part2 root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.config.database import engine

# 2. Caminho para o JSON (relative to this script or fixed)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "../../data/dataset.json")

def main():
    # 3. Ler o ficheiro JSON
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # data é um dicionário com chaves "Console", "Games", "Accessories"
    rows = []

    for segment, items in data.items():
        # segment = "Console", "Games" ou "Accessories"
        for item in items:
            row = item.copy()
            row["segment"] = segment  # marca de onde veio
            rows.append(row)

    # 4. Converter para DataFrame
    df = pd.DataFrame(rows)

    print("Pré-visualização do DataFrame de produtos:")
    print(df.head())

    # 5. Normalizar nomes das colunas (tirar espaços, pôr em minúsculas)
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # 6. Converter release_date em datetime (se existir)
    if "release_date" in df.columns:
        df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    # 7. Opcional: garantir que colunas de lojas existem sempre
    for col in ["store_a", "store_b", "store_c"]:
        if col not in df.columns:
            df[col] = None

    # 8. Gravar no Postgres numa tabela staging chamada products_raw
    with engine.begin() as conn:
        df.to_sql(
            "products_raw",
            conn,
            if_exists="replace",
            index=False,
        )

    print("Tabela products_raw carregada com sucesso na base de dados.")

if __name__ == "__main__":
    main()
