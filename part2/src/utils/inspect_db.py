import sys
import os

# Add part2 root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from sqlalchemy import inspect, text
from src.config.database import engine

inspector = inspect(engine)

print("📌 Tabelas existentes:")
tables = inspector.get_table_names()
for t in tables:
    print(" -", t)

# Mostrar estrutura
if "product_cooccurrence_raw" in tables:
    print("\n📌 Estrutura de product_cooccurrence_raw:")
    columns = inspector.get_columns("product_cooccurrence_raw")
    for col in columns:
        print(col)

    # Ver algumas linhas
    print("\n📌 Primeiras linhas do product_cooccurrence_raw:")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM product_cooccurrence_raw LIMIT 10")).all()
        for r in rows:
            print(r)
