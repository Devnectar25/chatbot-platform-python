import psycopg2
import os
from decimal import Decimal
from app.services.rag_service import ingest_raw_documents

def sync_postgres_to_ai(app_id: str, table_name: str, text_columns: list, metadata_columns: list = []):
    """
    Connects to PostgreSQL, fetches records from a specific table,
    and ingests them into the AI Vector Database.
    """
    try:
        # Establish connection using environment variables
        conn = psycopg2.connect(
            host=os.getenv("PGHOST"),
            port=os.getenv("PGPORT"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            database=os.getenv("PGDATABASE")
        )
        cur = conn.cursor()
        
        # Build query
        all_cols = text_columns + metadata_columns
        query = f"SELECT {', '.join(all_cols)} FROM {table_name}"
        
        print(f"Fetching data from PostgreSQL table: {table_name}...")
        cur.execute(query)
        rows = cur.fetchall()
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, row in enumerate(rows):
            # Combine text columns into a single document string
            doc_parts = []
            for i, col in enumerate(text_columns):
                doc_parts.append(f"{col}: {row[i]}")
            
            content = "\n".join(doc_parts)
            
            # Extract metadata
            meta = {"app_id": app_id, "source": f"postgres_{table_name}"}
            for i, col in enumerate(metadata_columns):
                val = row[len(text_columns) + i]
                # Maximum safety: only allow str, int, float, bool
                if val is None:
                    meta[col] = "" 
                elif isinstance(val, (str, int, float, bool)):
                    meta[col] = val
                else:
                    meta[col] = str(val)
            
            documents.append(content)
            metadatas.append(meta)
            ids.append(f"{app_id}_{table_name}_{idx}")
            
        cur.close()
        conn.close()
        
        # Ingest into AI memory
        return ingest_raw_documents(app_id, documents, metadatas, ids)
        
    except Exception as e:
        print(f"PostgreSQL Sync Error: {e}")
        return {"status": "error", "message": str(e)}
