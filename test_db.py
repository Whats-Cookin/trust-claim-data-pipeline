import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def test_connection():
    try:
        # Get the DATABASE_URI from .env
        DATABASE_URI = os.getenv('DATABASE_URI')
        
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URI)
        
        # Create a cursor
        cur = conn.cursor()
        
        # Execute a test query
        cur.execute('SELECT version();')
        
        # Fetch the result
        version = cur.fetchone()
        print("Connected to PostgreSQL:")
        print(version)
        
        # Close cursor and connection
        cur.close()
        conn.close()
        print("Connection test successful!")
        
    except Exception as e:
        print("Connection failed:")
        print(str(e))

if __name__ == "__main__":
    test_connection()
