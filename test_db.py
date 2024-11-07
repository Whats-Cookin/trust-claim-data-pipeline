import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def test_connection():
    try:
        DATABASE_URI = os.getenv('DATABASE_URI')
        
        conn = psycopg2.connect(DATABASE_URI)
        
        cur = conn.cursor()
        
        cur.execute('SELECT version();')
        
        version = cur.fetchone()
        print("Connected to PostgreSQL:")
        print(version)
        
        cur.close()
        conn.close()
        print("Connection test successful!")
        
    except Exception as e:
        print("Connection failed:")
        print(str(e))

if __name__ == "__main__":
    test_connection()
