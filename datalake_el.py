import io 
import boto3 
import pandas as pd

# Configurações do DataLake
S3_ENDPOINT_URL = "https://esdsshhyyibytjqyxype.storage.supabase.co/storage/v1/s3"
AWS_REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "fd3fb7bb055a50caa8febe009a90e027"
AWS_SECRET_ACCESS_KEY = "4c66298bfde7942353713153d41b55a3b65b14bb97093a0c71be58e6b0ab39a7"
BUCKET_NAME = "datalake_ecommerce"

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

# Configurações do PostgreSQL (Supabase)
DATABASE_URL = "postgresql+psycopg2://postgres:Ironmain2025%24@db.esdsshhyyibytjqyxype.supabase.co:6543/postgres"

# Criar engine de conexão com o PostgreSQL
engine = create_engine(DATABASE_URL)

# --- Salvar dados no PostgreSQL ---
# Lista com os nomes das 4 tabelas que vamos carregar
TABELAS = ["produtos", "clientes", "vendas", "preco_competidores"]

# Dicionário vazio onde vamos guardar os DataFrames
# Chave = nome da tabela, Valor = DataFrame com os dados
dataframes = {}

# --- FOR 1: Baixar cada tabela do DataLake ---
for tabela in TABELAS:
    print(f"Baixando {tabela}.parquet do DataLake...")

    # Montar o nome do arquivo: "produtos" → "produtos.parquet"
    file_key = f"{tabela}.parquet"

    # Baixar o arquivo do S3 (mesmo código da PARTE 1.A, mas com variável)
    response = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
    parquet_bytes = response["Body"].read()

    # Converter bytes → DataFrame e guardar no dicionário
    dataframes[tabela] = pd.read_parquet(io.BytesIO(parquet_bytes))

    print(f"{tabela}: {len(dataframes[tabela])} linhas carregadas")

# --- FOR 2: Salvar cada tabela no PostgreSQL ---
for tabela, df in dataframes.items():
    print(f"Salvando {tabela} no PostgreSQL...")

    df.to_sql(
        tabela,                # Nome da tabela no banco
        engine,                # Engine de conexão
        if_exists="replace",   # Substituir se existir
        index=False,           # Não salvar índice do pandas
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
