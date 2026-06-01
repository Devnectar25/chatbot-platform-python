import os
from app.services.adapters.postgres_adapter import sync_postgres_to_ai

def run_full_homeveda_sync():
    app_id = "homeveda_shop"
    
    print(f"--- Starting Full Sync for {app_id} ---")
    
    # 1. Sync Products (The core knowledge)
    print("\n[1/4] Syncing Products...")
    sync_postgres_to_ai(
        app_id=app_id,
        table_name="products",
        text_columns=["productname", "description", "benefits", "ingredients", "usage", "directions", "supports", "price", "image"],
        metadata_columns=["brand", "instock", "rating"]
    )
    
    # 2. Sync FAQs
    print("\n[2/4] Syncing FAQs...")
    sync_postgres_to_ai(
        app_id=app_id,
        table_name="faqs",
        text_columns=["question", "answer"],
        metadata_columns=["category"]
    )
    
    # 3. Sync Health Tips
    print("\n[3/4] Syncing Health Tips...")
    sync_postgres_to_ai(
        app_id=app_id,
        table_name="health_tips",
        text_columns=["title", "content"],
        metadata_columns=["category", "author"]
    )
    
    # 4. Sync Custom Knowledge
    print("\n[4/4] Syncing Custom Chatbot Knowledge...")
    sync_postgres_to_ai(
        app_id=app_id,
        table_name="chatbot_knowledge",
        text_columns=["query_pattern", "answer"],
        metadata_columns=["intent", "keywords"]
    )
    
    print(f"\n--- Full Sync Complete for {app_id}! ---")

if __name__ == "__main__":
    run_full_homeveda_sync()
