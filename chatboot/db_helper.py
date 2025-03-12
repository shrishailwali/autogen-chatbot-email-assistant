# db_helper.py

import psycopg2
from config import POSTGRES_CONFIG

def connect_to_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_CONFIG["host"],
            port=POSTGRES_CONFIG["port"],
            database=POSTGRES_CONFIG["database"],
            user=POSTGRES_CONFIG["user"],
            password=POSTGRES_CONFIG["password"]
        )
        return conn
    except Exception as e:
        print("Error connecting to database:", e)
        return None

def execute_query(query):
    if not query.strip():
        return "Error: Empty query received."
    conn = connect_to_db()
    if conn is None:
        return "Database connection failed."
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            if query.strip().lower().startswith("select"):
                result = cursor.fetchall()
                return result
            else:
                conn.commit()
                return "Query executed successfully."
    except Exception as e:
        return f"Error executing query: {e}"
    finally:
        conn.close()
