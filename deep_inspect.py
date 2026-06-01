import os
import sys
sys.path.append(os.getcwd())

from app.services.rag_service import get_chroma_collection
from dotenv import load_dotenv

load_dotenv()

def deep_inspect():
    app_id = "homeveda_shop"
    collection = get_chroma_collection()
    
    print(f"Inspecting memory for {app_id}...")
    results = collection.get(where={"app_id": app_id})
    
    count = len(results['ids'])
    print(f"Total records found for {app_id}: {count}")
    
    if count > 0:
        print("\nSample records:")
        for i in range(min(5, count)):
            print(f"- ID: {results['ids'][i]}")
            print(f"  Content: {results['documents'][i][:100]}...")
    
    # If there are records that look like dummy data (from sync_everything.py or earlier), delete them
    # Real records have IDs like 'homeveda_shop_brand_0'
    # Dummy records might have IDs from 'dummy_database.json' which are numeric strings or similar
    
    print("\nAttempting to wipe EVERYTHING for this app_id again...")
    collection.delete(where={"app_id": app_id})
    print("Wipe complete.")
    
    # Double check
    results2 = collection.get(where={"app_id": app_id})
    print(f"Records remaining after wipe: {len(results2['ids'])}")

if __name__ == "__main__":
    deep_inspect()
