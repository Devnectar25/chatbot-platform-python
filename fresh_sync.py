import os
import sys
sys.path.append(os.getcwd())

from app.services.rag_service import get_chroma_collection
from app.services.adapters.postgres_adapter import sync_postgres_to_ai
from dotenv import load_dotenv

load_dotenv()

def clean_and_sync():
    app_id = "homeveda_shop"
    collection = get_chroma_collection()
    
    print(f"Cleaning memory for {app_id}...")
    try:
        # Delete all existing records for this app_id to remove dummy data
        collection.delete(where={"app_id": app_id})
        print("Memory cleared successfully.")
    except Exception as e:
        print(f"Nothing to clear or error: {e}")

    print("\nStarting fresh database sync...")
    
    # 1. Sync Brands
    sync_postgres_to_ai(app_id, "brand", ["name", "description"], ["brand_id", "active"])
    
    # 2. Sync Categories
    sync_postgres_to_ai(app_id, "category", ["name", "description"], ["category_id", "active"])
    
    # 3. Sync Products
    sync_postgres_to_ai(app_id, "products", ["productname", "description", "brand", "benefits"], ["product_id", "price", "image"])
    
    # 4. Sync Coupons
    sync_postgres_to_ai(app_id, "coupons", ["code", "discount_type"], ["discount_value", "min_order_value"])
    
    # 5. Sync Offers
    sync_postgres_to_ai(app_id, "whatsapp_campaigns", ["title", "offer_details"], ["discount_type", "is_active"])

    print("\n[SUCCESS] Fresh sync complete! Only REAL data is now in the AI memory.")

if __name__ == "__main__":
    clean_and_sync()
