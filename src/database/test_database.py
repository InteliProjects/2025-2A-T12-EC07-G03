from sqlalchemy import create_engine
import pandas as pd

# String de conexão
engine = create_engine("postgresql+psycopg2://admin:admin123@localhost:5434/SyncTelemetry")

# Ler uma tabela direto pro pandas
df = pd.read_sql("SELECT * FROM processed_data LIMIT 10;", engine)
print(df)

"""
Vamos usar esse exemplo na API de treinamento e de previsão para pegar os dados processados
Também vamos usar no serviço de processamento de dados. Pega do lake, processa, joga nessa tabela
"""
