import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        url = os.getenv("POSTGRES_URL")
        if not url:
            raise ValueError("POSTGRES_URL não configurada no .env")
        _engine = create_engine(url)
    return _engine


def execute_query(sql: str) -> pd.DataFrame:
    stripped = sql.strip()
    first_word = stripped.split()[0].upper() if stripped else ""
    if first_word not in ("SELECT", "WITH"):
        raise ValueError(
            f"Apenas queries SELECT ou WITH são permitidas. Recebido: {first_word}"
        )

    engine = _get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)
