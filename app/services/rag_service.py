import json
# import ollama
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

import time

# Define custom embedding function using the already installed google-generativeai SDK
class GeminiEmbeddingFunction:
    @staticmethod
    def name() -> str:
        return "gemini-embedding"

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self(input)

    def __call__(self, input: list[str]) -> list[list[float]]:
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            print("WARNING: GOOGLE_GEMINI_API_KEY or GEMINI_API_KEY not found in environment variables!")
        
        print(f"[GEMINI] Generating embeddings for {len(input)} documents...")
        
        # Split input into chunks of 50 to avoid Gemini API batch limit (100) and rate limits
        chunk_size = 50
        all_embeddings = []
        
        for i in range(0, len(input), chunk_size):
            chunk = input[i:i + chunk_size]
            print(f"[GEMINI] Embedding chunk {i//chunk_size + 1}/{(len(input)-1)//chunk_size + 1} (size: {len(chunk)})...")
            
            max_retries = 5
            retry_delay = 20  # seconds
            
            for attempt in range(max_retries):
                try:
                    response = genai.embed_content(
                        model="models/gemini-embedding-001",
                        content=chunk,
                        task_type="retrieval_document"
                    )
                    all_embeddings.extend(response['embedding'])
                    break
                except Exception as e:
                    # If we hit a rate limit (429), sleep and retry
                    if "429" in str(e) and attempt < max_retries - 1:
                        print(f"[GEMINI] Rate limit hit (429). Retrying in {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay += 20  # Incremental backoff
                    else:
                        raise e
            
            # Sleep briefly between successful chunks to avoid hitting rate limits
            if i + chunk_size < len(input):
                print("[GEMINI] Sleeping for 3 seconds to avoid rate limits...")
                time.sleep(3)
                
        return all_embeddings

# Global cache for the embedding function
MULTILINGUAL_EF = None

def get_chroma_collection():
    global MULTILINGUAL_EF
    # Use absolute path so it works regardless of which directory the server is launched from
    _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _chroma_path = os.path.join(_base_dir, "chroma_db")
    
    if os.getenv("VERCEL") == "1":
        _tmp_chroma_path = "/tmp/chroma_db"
        if not os.path.exists(_tmp_chroma_path):
            print(f"[VERCEL] Copying ChromaDB from {_chroma_path} to {_tmp_chroma_path}...")
            import shutil
            try:
                shutil.copytree(_chroma_path, _tmp_chroma_path, dirs_exist_ok=True)
                print("[VERCEL] Copy completed successfully.")
            except Exception as copy_err:
                print(f"[VERCEL ERROR] Failed to copy ChromaDB: {copy_err}")
        _chroma_path = _tmp_chroma_path

    # Lazy import to avoid loading heavy modules on startup
    import chromadb
    client = chromadb.PersistentClient(path=_chroma_path)
    print(f"[CHROMA] Using DB at: {_chroma_path}")
    
    if MULTILINGUAL_EF is None:
        print("Initializing Gemini Embedding Function (Custom)...")
        MULTILINGUAL_EF = GeminiEmbeddingFunction()
    
    collection = client.get_or_create_collection(
        name="chatbot_knowledge_v3", 
        embedding_function=MULTILINGUAL_EF
    )
    return collection

def ingest_raw_documents(app_id: str, documents: list, metadatas: list, ids: list):
    """
    Universal Ingestion API: 
    Accepts standardized text chunks and stores them in ChromaDB.
    """
    collection = get_chroma_collection()
    
    print(f"Ingesting {len(documents)} records for app: {app_id} into AI memory...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    return {"status": "success", "message": f"Successfully ingested {len(documents)} records."}

def ingest_dummy_data(app_id: str):
    print(f"Loading dummy data for app: {app_id}...")
    try:
        with open('data/dummy_database.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        return {"status": "error", "message": "Dummy data file not found."}

    documents = []
    metadatas = []
    ids = []

    for item in data:
        content = f"Question: {item['question']}\nAnswer: {item['answer']}"
        documents.append(content)
        metadatas.append({"app_id": app_id, "category": item.get('category', 'General')})
        ids.append(item['id'])

    return ingest_raw_documents(app_id, documents, metadatas, ids)

def generate_chat_response(app_id: str, user_question: str, language: str = "en-IN"):
    collection = get_chroma_collection()

    import time
    start_time = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Step 1: Searching ChromaDB for: {user_question}...")
    results = collection.query(
        query_texts=[user_question],
        n_results=3,
        where={"app_id": app_id}
    )
    search_time = time.time() - start_time
    print(f"[{time.strftime('%H:%M:%S')}] Search completed in {search_time:.2f}s")
    
    if not results['documents'] or not results['documents'][0]:
        context = "No relevant context found in the database."
    else:
        # Join all found context snippets
        context = "\n---\n".join(results['documents'][0])

    print(f"[{time.strftime('%H:%M:%S')}] Step 2: Streaming response from Ollama is disabled (WhatsApp focus).")
    yield "Ollama chatbot is currently disabled. Please use the WhatsApp chatbot route."

    # 2. Extract and Inject Image/Price directly (Bypassing LLM filters)
    # We only take from the MOST relevant snippet (the first one) to avoid mismatch
    # Threshold check: Only inject if the match is strong enough (distance < 1.3)
    try:
        distance = results['distances'][0][0] if results['distances'] and results['distances'][0] else 999
        print(f"[{time.strftime('%H:%M:%S')}] Top match distance: {distance:.4f}")
        
        # Don't inject images for very short conversational queries or weak matches
        conversational_words = {'thanks', 'thank', 'hi', 'hello', 'hey', 'welcome', 'bye'}
        is_conversational = user_question.lower().strip() in conversational_words or len(user_question.split()) < 2
        
        if distance < 1.3 and not is_conversational:
            top_snippet = results['documents'][0][0] if results['documents'] and results['documents'][0] else ""
            image_url = ""
            price_val = ""
            for line in top_snippet.split('\n'):
                if line.startswith('image:'):
                    image_url = line.replace('image:', '').strip()
                if line.startswith('price:'):
                    price_val = line.replace('price:', '').strip()
            
            if image_url and image_url != "":
                yield f"\n\nIMAGE_URL: {image_url}"
            if price_val and price_val != "":
                yield f"\nPRICE: {price_val}"
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Skipping image injection (Match too weak or conversational query).")
            
    except Exception as e:
        print(f"Injection Error: {e}")

def warmup_models():
    print("Pre-loading models for zero-latency first response...")
    # 1. Warm up the Multilingual Embedding Model
    get_chroma_collection()
    
    # 2. Warm up Ollama (Disabled)
    # try:
    #     ollama.generate(model='qwen2:1.5b', prompt='ping', keep_alive='5m')
    #     print("Models warmed up successfully!")
    # except Exception as e:
    #     print(f"Ollama warm-up failed: {e}")
