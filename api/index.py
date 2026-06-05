import sys
import os

# Clean environment variables from copy-paste errors (like KEY=value instead of just value)
for _k, _v in list(os.environ.items()):
    if _v:
        _cleaned = _v.strip().strip("'\"")
        if _cleaned.startswith(f"{_k}="):
            _cleaned = _cleaned[len(_k)+1:].strip().strip("'\"")
        if _cleaned != _v:
            print(f"[ENV_CLEAN] Cleaned environment variable: {_k}")
            os.environ[_k] = _cleaned

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
