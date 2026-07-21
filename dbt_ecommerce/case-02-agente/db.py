import os
import re

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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


_DML_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|CREATE|ALTER|GRANT|REVOKE|COPY|VACUUM|ANALYZE)\b",
    re.IGNORECASE,
)


def execute_query(sql: str) -> pd.DataFrame:
    stripped = sql.strip()
    first_word = stripped.split()[0].upper() if stripped else ""
    if first_word not in ("SELECT", "WITH"):
        raise ValueError(
            f"Apenas queries SELECT ou WITH são permitidas. Recebido: {first_word}"
        )
    if _DML_KEYWORDS.search(stripped):
        match = _DML_KEYWORDS.search(stripped)
        raise ValueError(
            f"Operação não permitida detectada na query: {match.group().upper()}"
        )

    engine = _get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)
