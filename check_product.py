import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_product():
    try:
        conn = psycopg2.connect(
            host=os.getenv("PGHOST"),
            port=os.getenv("PGPORT"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            database=os.getenv("PGDATABASE")
        )
        cur = conn.cursor()
        query = "SELECT productname, image, price FROM products WHERE productname ILIKE '%Zandu Dantveer%'"
        cur.execute(query)
        row = cur.fetchone()
        print(f"Product Data: {row}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_product()
