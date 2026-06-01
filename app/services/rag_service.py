import json
import chromadb
import ollama
import os
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

# Global cache for the multilingual embedding function to prevent re-loading weights on every request
MULTILINGUAL_EF = None

def get_chroma_collection():
    global MULTILINGUAL_EF
    # Use absolute path so it works regardless of which directory the server is launched from
    _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _chroma_path = os.path.join(_base_dir, "chroma_db")
    client = chromadb.PersistentClient(path=_chroma_path)
    print(f"[CHROMA] Using DB at: {_chroma_path}")
    
    if MULTILINGUAL_EF is None:
        print("Initializing Multilingual Embedding Function...")
        MULTILINGUAL_EF = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
    
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

    print(f"[{time.strftime('%H:%M:%S')}] Step 2: Generating streaming response from Ollama (qwen2:1.5b)...")
    print(f"--- DEBUG CONTEXT START ---\n{context}\n--- DEBUG CONTEXT END ---")
    
    prompt = f"""
    You are the "Official Homeveda AI Assistant", a professional and helpful expert on Ayurvedic health and products.
    
    CRITICAL INSTRUCTIONS:
    1. Your primary knowledge source is the provided CONTEXT. 
    2. If the CONTEXT contains information related to the USER QUESTION, you MUST use it to answer.
    3. If the CONTEXT is empty or irrelevant, politely inform the user that you don't have that specific information in your database but offer to help with general Ayurvedic queries.
    4. RESPOND ENTIRELY IN THE LANGUAGE: '{language}'.
    5. Be warm, professional, and concise.
    6. Do NOT mention internal terms like "CONTEXT" or "DATABASE" to the user.
    7. Provide ONLY the final response text.
    8. IMPORTANT: Do NOT use markdown image syntax like `![]()`. The system handles images separately.

    CONTEXT FROM HOMEVEDA DATABASE:
    {context}

    USER QUESTION:
    {user_question}
    """

    # 1. Generate the AI response
    stream = ollama.generate(
        model='qwen2:1.5b',
        prompt=prompt,
        stream=True
    )
    
    full_text = ""
    chunk_count = 0
    for chunk in stream:
        if chunk_count == 0:
            print(f"[{time.strftime('%H:%M:%S')}] First chunk received from Ollama!")
        chunk_count += 1
        full_text += chunk['response']
        clean_chunk = chunk['response'].replace('![]()', '').replace('![]', '').replace('()', '')
        yield clean_chunk
    
    print(f"[{time.strftime('%H:%M:%S')}] Generation finished. Total chunks: {chunk_count}")
    print(f"--- DEBUG FULL RESPONSE START ---\n{full_text}\n--- DEBUG FULL RESPONSE END ---")

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
    
    # 2. Warm up Ollama (qwen2:1.5b)
    try:
        ollama.generate(model='qwen2:1.5b', prompt='ping', keep_alive='5m')
        print("Models warmed up successfully!")
    except Exception as e:
        print(f"Ollama warm-up failed: {e}")
