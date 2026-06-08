import os
import json
import uuid
import sys
import traceback
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.services.rag_service import ingest_raw_documents, get_chroma_collection

def sync_faqs():
    APP_ID = "devnectar_production"
    
    faqs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faqs.json")
    print(f"Reading {faqs_path}")
    
    with open(faqs_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        
    documents = []
    metadatas = []
    ids = []
    
    for idx, item in enumerate(data):
        q = item.get("question", "")
        a = item.get("answer", "")
        content = f"Question: {q}\nAnswer: {a}"
        documents.append(content)
        metadatas.append({"app_id": APP_ID, "type": "faq"})
        ids.append(str(uuid.uuid4()))
        
    print(f"Ingesting {len(documents)} FAQs into Chroma DB...")
    
    try:
        res = ingest_raw_documents(APP_ID, documents, metadatas, ids)
        print("Done:", res)
    except Exception as e:
        print("An error occurred during ingest:", e)
        traceback.print_exc()

if __name__ == "__main__":
    sync_faqs()
