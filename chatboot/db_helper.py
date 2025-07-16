import psycopg2
from config import POSTGRES_CONFIG

def connect_to_db():
    """
    Establish a connection to the PostgreSQL database using credentials from config.

    Returns:
        psycopg2.extensions.connection: A new database connection if successful.
        None: If the connection could not be established.

    Raises:
        psycopg2.DatabaseError: If the connection attempt fails due to DB issues.
    """
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
    """
    Execute a SQL query on the PostgreSQL database.

    This function:
      1. Validates that the query string is not empty.
      2. Opens a new database connection.
      3. Executes the query:
         - Returns fetched rows if it's a SELECT.
         - Commits and returns a status message otherwise.
      4. Closes the connection.

    Args:
        query (str): The SQL statement to be executed.

    Returns:
        list[tuple]: Resulting rows for SELECT queries.
        str: A status message for non-SELECT queries or error cases.

    Raises:
        psycopg2.DatabaseError: If query execution fails due to DB issues.
    """
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
