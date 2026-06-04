import sys
import os

# Override sqlite3 with pysqlite3 for ChromaDB to run on Vercel
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    print("pysqlite3 override successful!")
except Exception as e:
    print(f"pysqlite3 override failed: {e}")

# Add the project root to python path so it can import 'app' module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.main import app
except Exception as e:
    import traceback
    print("CRITICAL IMPORT ERROR IN APP MAIN:")
    traceback.print_exc()
    raise e
