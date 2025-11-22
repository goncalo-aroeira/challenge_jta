import sys
import os
import pandas as pd

# Add part2 root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.config.database import engine


def load_raw_tables():
    """Lê as tabelas *_raw do Postgres para DataFrames pandas."""
    products_raw = pd.read_sql_table("products_raw", engine)
    solo_raw = pd.read_sql_table("product_solo_sales_raw", engine)
    coocc_raw = pd.read_sql_table("product_cooccurrence_raw", engine)

    return products_raw, solo_raw, coocc_raw


def build_products_table(products_raw: pd.DataFrame) -> pd.DataFrame:
    """Cria a tabela final de products com product_id e feature engineering."""

    df = products_raw.copy()

    # Normalizar colunas esperadas
    expected_cols = [
        "name",
        "segment",
        "category",
        "type",
        "franchise",
        "min_age",
        "times_sold",
        "store_a",
        "store_b",
        "store_c",
        "release_date",
    ]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    # Converter tipos básicos
    # Preencher NaN nas lojas com 0
    for col in ["store_a", "store_b", "store_c"]:
        df[col] = df[col].fillna(0).astype(int)

    # times_sold: se estiver NaN, usar soma das lojas
    if "times_sold" in df.columns:
        df["times_sold"] = df["times_sold"].fillna(
            df[["store_a", "store_b", "store_c"]].sum(axis=1)
        ).astype(int)
    else:
        df["times_sold"] = df[["store_a", "store_b", "store_c"]].sum(axis=1).astype(int)

    # min_age: se NaN, pôr 0 (ou outro default)
    df["min_age"] = df["min_age"].fillna(0).astype(int)

    # release_date já deve vir como datetime do load_products.py,
    # mas garantimos:
    if "release_date" in df.columns:
        df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    # Criar product_id determinístico (ordenando por name)
    df = df.sort_values("name").reset_index(drop=True)
    df.insert(0, "product_id", df.index + 1)

    # Feature engineering 1: popularidade global
    max_total = df["times_sold"].max()
    if max_total > 0:
        df["popularity_global"] = df["times_sold"] / max_total
    else:
        df["popularity_global"] = 0.0

    # Feature engineering 2: popularidade por loja
    for col in ["store_a", "store_b", "store_c"]:
        max_store = df[col].max()
        if max_store > 0:
            df[f"popularity_{col}"] = df[col] / max_store
        else:
            df[f"popularity_{col}"] = 0.0

    # Feature engineering 3: bucket de idades
    def age_to_bucket(age: int) -> str:
        if age <= 3:
            return "0-3"
        elif age <= 7:
            return "4-7"
        elif age <= 12:
            return "8-12"
        elif age <= 16:
            return "13-16"
        else:
            return "17+"

    df["age_bucket"] = df["min_age"].apply(age_to_bucket)

    # Feature engineering 4: flag de "family friendly"
    df["family_friendly"] = (df["min_age"] <= 7).astype(int)

    # Feature engineering 5: franchise normalizada
    df["franchise_clean"] = (
        df["franchise"]
        .fillna("")
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # Feature engineering 6: text_blob para LLM / embeddings
    def make_text_blob(row):
        parts = []

        # Nome e segmento
        name = row.get("name", "")
        segment = row.get("segment", "")
        category = row.get("category", "")
        ptype = row.get("type", "")
        franchise = row.get("franchise", "")
        min_age = row.get("min_age", None)

        if name:
            parts.append(f"{name} is a {segment.lower()} product.")

        if category:
            parts.append(f"Category: {category}.")
        if ptype:
            parts.append(f"Type: {ptype}.")
        if franchise:
            parts.append(f"Franchise: {franchise}.")

        if min_age is not None:
            parts.append(f"Recommended minimum age: {min_age}.")

        # Popularidade simples em linguagem natural
        pop = row.get("popularity_global", 0)
        if pop >= 0.8:
            parts.append("This product is very popular.")
        elif pop >= 0.4:
            parts.append("This product has moderate popularity.")
        else:
            parts.append("This product has lower popularity.")

        return " ".join(parts)

    df["text_blob"] = df.apply(make_text_blob, axis=1)

    return df


def build_solo_sales_table(solo_raw: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
    """Mapeia product_name -> product_id para criar product_solo_sales."""
    name_to_id = dict(zip(products_df["name"], products_df["product_id"]))

    df = solo_raw.copy()
    df["product_id"] = df["product_name"].map(name_to_id)
    df = df.dropna(subset=["product_id"]).copy()
    df["product_id"] = df["product_id"].astype(int)

    df_final = df[["product_id", "solo_sales"]].copy()
    return df_final


def build_cooccurrence_table(coocc_raw: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
    """Mapeia product_1, product_2 -> product_id_1, product_id_2."""

    name_to_id = dict(zip(products_df["name"], products_df["product_id"]))

    df = coocc_raw.copy()
    df["product_id_1"] = df["product_1"].map(name_to_id)
    df["product_id_2"] = df["product_2"].map(name_to_id)

    # Remover pares que não encontraram ID
    df = df.dropna(subset=["product_id_1", "product_id_2"]).copy()
    df["product_id_1"] = df["product_id_1"].astype(int)
    df["product_id_2"] = df["product_id_2"].astype(int)

    df_final = df[["product_id_1", "product_id_2", "count"]].copy()
    df_final.rename(columns={"count": "cooccurrence_count"}, inplace=True)

    return df_final


def add_graph_features(products_df: pd.DataFrame, coocc_df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona features simples de grafo (num_neighbors, total_cooccurrence) à tabela de products."""
    df = products_df.copy()

    # Agrupar por product_id_1
    agg = (
        coocc_df.groupby("product_id_1")["cooccurrence_count"]
        .agg(num_neighbors="count", total_cooccurrence="sum")
    )

    df = df.merge(
        agg,
        how="left",
        left_on="product_id",
        right_index=True,
    )

    df["num_neighbors"] = df["num_neighbors"].fillna(0).astype(int)
    df["total_cooccurrence"] = df["total_cooccurrence"].fillna(0).astype(int)

    return df


def write_final_tables(products_df, solo_df, coocc_df):
    """Grava as tabelas finais no Postgres, substituindo se já existirem."""
    with engine.begin() as conn:
        products_df.to_sql("products", conn, if_exists="replace", index=False)
        solo_df.to_sql("product_solo_sales", conn, if_exists="replace", index=False)
        coocc_df.to_sql("product_cooccurrence", conn, if_exists="replace", index=False)


def main():
    print("A ler tabelas raw do Postgres...")
    products_raw, solo_raw, coocc_raw = load_raw_tables()

    print("A construir tabela products com feature engineering...")
    products_df = build_products_table(products_raw)

    print("A construir tabela de co-ocorrência com IDs...")
    coocc_df = build_cooccurrence_table(coocc_raw, products_df)

    print("A adicionar graph features (num_neighbors, total_cooccurrence) a products...")
    products_df = add_graph_features(products_df, coocc_df)

    print("A construir tabela de solo_sales com IDs...")
    solo_df = build_solo_sales_table(solo_raw, products_df)

    print("A gravar tabelas finais no Postgres...")
    write_final_tables(products_df, solo_df, coocc_df)

    print("✅ Processo concluído. Tabelas finais criadas: products, product_solo_sales, product_cooccurrence")


if __name__ == "__main__":
    main()
