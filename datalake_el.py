import io
import os

import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Configurações do DataLake
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME", "datalake_ecommerce")

if not all([S3_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
    raise ValueError("Variáveis S3_ENDPOINT_URL, AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY são obrigatórias no .env")

# Criar cliente S3
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# --- Teste de conexão: listar arquivos no bucket ---
response = s3.list_objects(Bucket=BUCKET_NAME)
arquivos = [obj["Key"] for obj in response["Contents"]]
print("Arquivos encontrados no DataLake:")
print(arquivos)

from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Variável DATABASE_URL é obrigatória no .env")

# Criar engine de conexão com o PostgreSQL
engine = create_engine(DATABASE_URL)

# --- Salvar dados no PostgreSQL ---
TABELAS = ["produtos", "clientes", "vendas", "preco_competidores"]

dataframes = {}

# --- FOR 1: Baixar cada tabela do DataLake ---
for tabela in TABELAS:
    print(f"Baixando {tabela}.parquet do DataLake...")

    file_key = f"{tabela}.parquet"

    response = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
    parquet_bytes = response["Body"].read()

    dataframes[tabela] = pd.read_parquet(io.BytesIO(parquet_bytes))

    print(f"{tabela}: {len(dataframes[tabela])} linhas carregadas")

# --- FOR 2: Salvar cada tabela no PostgreSQL ---
for tabela, df in dataframes.items():
    print(f"Salvando {tabela} no PostgreSQL...")

    df.to_sql(
        tabela,
        engine,
        if_exists="replace",
        index=False,
    )

    print(f" {tabela}: {len(df)} linhas salvas no banco")

# --- FOR 3: Verificar se os dados foram salvos corretamente ---
print("\n Verificação final:")
for tabela in TABELAS:
    df_verificacao = pd.read_sql_query(f"SELECT COUNT(*) as total FROM {tabela}", engine)
    total = df_verificacao["total"].iloc[0]
    print(f"  {tabela}: {total} linhas no banco")

# Fechar conexão
engine.dispose()
