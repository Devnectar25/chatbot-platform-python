import os
import sys
# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.services.adapters.postgres_adapter import sync_postgres_to_ai
from dotenv import load_dotenv

load_dotenv()

def sync_all():
    print("Starting full database sync to AI memory...")
    
    app_id = "homeveda_shop"
    
    # 1. Sync Brands
    print("\n--- Syncing Brands ---")
    sync_postgres_to_ai(
        app_id=app_id,
        table_name="brand",
        text_columns=["name", "description"],
        metadata_columns=["brand_id", "active"]
    )
    
    # 2. Sync Categories
    print("\n--- Syncing Categories ---")
    sync_postgres_to_ai(
        app_id=app_id,
        table_name="category",
        text_columns=["name", "description"],
        metadata_columns=["category_id", "active"]
    )
    
    # 3. Sync Products
    print("\n--- Syncing Products ---")
    sync_postgres_to_ai(
        app_id=app_id,
        table_name="products",
        text_columns=["productname", "description", "brand", "shortdescription", "benefits", "ingredients"],
        metadata_columns=["product_id", "price", "image", "instock"]
    )
    
    # 4. Sync Coupons
    print("\n--- Syncing Coupons ---")
    sync_postgres_to_ai(
        app_id=app_id,
        table_name="coupons",
        text_columns=["code", "discount_type"],
        metadata_columns=["discount_value", "min_order_value", "expiry_date", "active"]
    )
    
    # 5. Sync Offers (WhatsApp Campaigns)
    print("\n--- Syncing Offers ---")
    sync_postgres_to_ai(
        app_id=app_id,
        table_name="whatsapp_campaigns",
        text_columns=["title", "offer_details", "festival_message"],
        metadata_columns=["discount_type", "discount_value", "is_active"]
    )

    print("\n[SUCCESS] Full sync complete! Your AI Chatbot now knows everything about your Brands, Products, Coupons, and Offers.")

if __name__ == "__main__":
    sync_all()
