import sys
import os

# Add part2 root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from sqlalchemy import text
from src.config.database import engine

def main():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            print("Ligação ao Postgres bem sucedida!")
            print("Versão:", version)
    except Exception as e:
        print("Erro a ligar ao Postgres:")
        print(e)

if __name__ == "__main__":
    main()
