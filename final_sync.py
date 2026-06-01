import os
import sys
sys.path.append(os.getcwd())

from app.services.adapters.postgres_adapter import sync_postgres_to_ai
from dotenv import load_dotenv

load_dotenv()

def final_sync():
    # Use a brand new, unique ID to ensure zero interference
    app_id = "homeveda_production_final"
    
    print(f"Starting FINAL sync for {app_id}...")
    
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

    print(f"\n[SUCCESS] Final sync complete for {app_id}!")

if __name__ == "__main__":
    final_sync()
