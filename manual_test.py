import os
import sys
sys.path.append(os.getcwd())

from app.services.rag_service import get_chroma_collection
from dotenv import load_dotenv

load_dotenv()

def manual_query_test():
    app_id = "homeveda_production_final"
    collection = get_chroma_collection()
    
    # Test 1: Search for 'brand'
    print("\n--- TEST 1: Searching for 'brand' ---")
    res1 = collection.query(query_texts=["brand"], n_results=5, where={"app_id": app_id})
    print(f"Results found: {len(res1['documents'][0])}")
    for doc in res1['documents'][0]:
        print(f"  Match: {doc[:100]}...")

    # Test 2: Search for 'Himalaya'
    print("\n--- TEST 2: Searching for 'Himalaya' ---")
    res2 = collection.query(query_texts=["Himalaya"], n_results=1, where={"app_id": app_id})
    print(f"Results found: {len(res2['documents'][0])}")
    for doc in res2['documents'][0]:
        print(f"  Match: {doc[:100]}...")

    # Test 3: Get ALL records
    print("\n--- TEST 3: Getting ALL records ---")
    all_res = collection.get(where={"app_id": app_id})
    print(f"Total records in DB for {app_id}: {len(all_res['ids'])}")
    for i in range(min(5, len(all_res['ids']))):
        print(f"- {all_res['ids'][i]}: {all_res['documents'][i][:50]}")

if __name__ == "__main__":
    manual_query_test()
