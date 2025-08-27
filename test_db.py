import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

db_config = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

try:
    conn = mysql.connector.connect(**db_config)
    print("Conexión exitosa!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")