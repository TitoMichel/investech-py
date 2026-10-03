import os
from dotenv import load_dotenv
import mysql.connector

# Força leitura do .env no diretório atual
loaded = load_dotenv()
print(f"O arquivo .env foi carregado? {loaded}")

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORDS")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
database = os.getenv("DB_NAME")

print(f"Tentando conectar com:")
print(f"Host: {host}:{port}")
print(f"User: {user}")
print(f"Pass: {'*' * len(password) if password else '(vazio)'}")
print(f"DB:   {database}")

try:
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    print("\n Conexão bem-sucedida!")
    conn.close()
except Exception as e:
    print(f"\n Erro de conexão: {e}")