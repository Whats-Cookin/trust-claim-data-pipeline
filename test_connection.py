import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Get the DATABASE_URI from .env
database_url = os.getenv('DATABASE_URI')
print(f"Attempting to connect with: {database_url}")

try:
    # Try connecting with psycopg2
    conn = psycopg2.connect(
        dbname="claim",
        user="emos",
        password="12",
        host="localhost",
        port="5432"
    )
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {str(e)}")