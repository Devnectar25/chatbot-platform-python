import os
import sys
sys.path.append(os.getcwd())

import psycopg2
from app.services.rag_service import ingest_raw_documents, get_chroma_collection
from dotenv import load_dotenv

load_dotenv()

def ultimate_sync():
    app_id = "homeveda_production_final"
    collection = get_chroma_collection()
    
    # Clear again to be safe
    collection.delete(where={"app_id": app_id})
    
    conn = psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
        database=os.getenv("PGDATABASE")
    )
    cur = conn.cursor()
    
    # 1. Sync Brands with BOOSTED text
    print("Syncing Brands with Boost...")
    cur.execute("SELECT name, description FROM brand")
    brands = cur.fetchall()
    documents = []
    metadatas = []
    ids = []
    for idx, row in enumerate(brands):
        # We add "Homeveda Brand" explicitly to the text so search hits it
        content = f"Homeveda Partner Brand Name: {row[0]}\nDescription: {row[1]}"
        documents.append(content)
        metadatas.append({"app_id": app_id, "type": "brand"})
        ids.append(f"{app_id}_brand_{idx}")
    
    ingest_raw_documents(app_id, documents, metadatas, ids)
    
    # 2. Sync Categories
    print("Syncing Categories...")
    cur.execute("SELECT name, description FROM category")
    cats = cur.fetchall()
    documents, metadatas, ids = [], [], []
    for idx, row in enumerate(cats):
        content = f"Homeveda Product Category: {row[0]}\nDescription: {row[1]}"
        documents.append(content)
        metadatas.append({"app_id": app_id, "type": "category"})
        ids.append(f"{app_id}_cat_{idx}")
    ingest_raw_documents(app_id, documents, metadatas, ids)

    # 3. Sync Coupons
    print("Syncing Coupons...")
    cur.execute("SELECT code, discount_type, discount_value FROM coupons")
    coupons = cur.fetchall()
    documents, metadatas, ids = [], [], []
    for idx, row in enumerate(coupons):
        content = f"Homeveda Discount Coupon Code: {row[0]}\nType: {row[1]}\nValue: {row[2]}"
        documents.append(content)
        metadatas.append({"app_id": app_id, "type": "coupon"})
        ids.append(f"{app_id}_coupon_{idx}")
    ingest_raw_documents(app_id, documents, metadatas, ids)

    # 4. Sync Products
    print("Syncing Products...")
    cur.execute("""
        SELECT productname, brand, description, shortdescription, benefits, price, image, rating
        FROM products WHERE active = true
    """)
    products = cur.fetchall()
    documents, metadatas, ids = [], [], []
    for idx, row in enumerate(products):
        name, brand, desc, short_desc, benefits, price, image, rating = row
        content = (
            f"Homeveda Product Name: {name or ''}\n"
            f"Brand: {brand or ''}\n"
            f"Description: {short_desc or desc or ''}\n"
            f"Benefits: {benefits or ''}\n"
            f"Price: {price or ''}\n"
            f"Rating: {rating or ''}"
        )
        meta = {"app_id": app_id, "type": "product"}
        if image:
            meta["image"] = str(image)
        if price:
            meta["price"] = str(price)
        documents.append(content)
        metadatas.append(meta)
        ids.append(f"{app_id}_product_{idx}")
    ingest_raw_documents(app_id, documents, metadatas, ids)

    # 5. Sync Offers (WhatsApp Campaigns)
    print("Syncing Offers...")
    cur.execute("SELECT title, offer_details, festival_message, discount_type, discount_value FROM whatsapp_campaigns WHERE is_active = true")
    offers = cur.fetchall()
    documents, metadatas, ids = [], [], []
    for idx, row in enumerate(offers):
        title, details, festival, dtype, dvalue = row
        content = (
            f"Homeveda Current Offer: {title or ''}\n"
            f"Details: {details or ''}\n"
            f"Festival: {festival or ''}\n"
            f"Discount: {dtype or ''} - {dvalue or ''}"
        )
        documents.append(content)
        metadatas.append({"app_id": app_id, "type": "offer"})
        ids.append(f"{app_id}_offer_{idx}")
    if documents:
        ingest_raw_documents(app_id, documents, metadatas, ids)

    cur.close()
    conn.close()
    print("\n[SUCCESS] Ultimate Sync Complete - Brands, Categories, Products, Coupons, Offers!")

if __name__ == "__main__":
    ultimate_sync()
