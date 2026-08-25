# agent/connection.py

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DATABASE_HOST"),
        port=os.getenv("DATABASE_PORT"),
        database=os.getenv("DATABASE_NAME"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        cursor_factory=RealDictCursor
        )

#checking db connection

if __name__ == "__main__":
    conn = None
    try:
        print("Trying to connect")
        conn = get_connection()
        print("Connection succesful")

        with conn.cursor() as cur:
            cur.execute("SELECT 1 as test_column;")
            result = cur.fetchone()
            print(f"Test query result: {result['test_column']}")

    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
    except Exception as e:
        print(f"An unexpected error occured: {e}")
    finally:
        if conn:
            conn.close()
            print("Connection closed")