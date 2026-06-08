import google.generativeai as genai
import os
import time
from dotenv import load_dotenv
from .rag_service import get_chroma_collection

load_dotenv()

# Setup Gemini lazily inside the response handler
model = None

APP_ID = "devnectar_production"

# Keywords that indicate the user wants a full list
LIST_KEYWORDS = {
    "brand": "brand",
    "brands": "brand",
    "category": "category",
    "categories": "category",
    "coupon": "coupon",
    "coupons": "coupon",
    "offer": "offer",
    "offers": "offer",
    "discount": "coupon",
    "product": "product",
    "products": "product",
    "top rated": "product",
    "best product": "product",
    "best products": "product",
    "top product": "product",
    "recommend": "product",
    "available product": "product",
}

def get_all_by_type(collection, record_type: str) -> str:
    """Fetch ALL records of a specific type directly (for list queries)."""
    try:
        results = collection.get(where={"$and": [{"app_id": APP_ID}, {"type": record_type}]})
        if results and results["documents"]:
            print(f"[DIRECT FETCH] Found {len(results['documents'])} records of type '{record_type}'")
            return "\n---\n".join(results["documents"])
    except Exception as e:
        print(f"[DIRECT FETCH ERROR] {e}")
    return ""

def generate_whatsapp_response(user_question: str, language: str = "en-IN"):
    """
    WhatsApp specific response generator using Google Gemini.
    Returns a dict with 'text' and 'image_url'.
    """
    global model
    if model is None:
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-flash-lite-latest')
            
    if model is None:
        print("[ERROR] Gemini Model is not initialized. GOOGLE_GEMINI_API_KEY is missing!")
        return {"text": "Error: Chatbot configuration is incomplete. Please ensure that GOOGLE_GEMINI_API_KEY is configured in your project environment variables.", "image_url": ""}

    question_lower = user_question.lower()

    # Define conversational intents
    GREETINGS = {"hi", "hii", "hiii", "hello", "hey", "heyy", "namaste", "good morning", "good afternoon", "good evening", "greetings"}
    THANKS = {"thanks", "thank you", "ty", "appreciate it", "great", "awesome", "perfect", "ok", "okay"}
    FAREWELLS = {"bye", "goodbye", "see ya", "talk later"}
    
    clean_q = question_lower.strip().rstrip("!?.")
    
    # Check if this is a purely conversational input
    is_greeting = any(word in clean_q.split() for word in GREETINGS)
    is_thanks = any(word in clean_q.split() for word in THANKS) or "thank you" in clean_q
    is_farewell = any(word in clean_q.split() for word in FAREWELLS)
    
    is_conversational = (is_greeting or is_thanks or is_farewell) and not any(k in question_lower for k in LIST_KEYWORDS)

    if is_conversational:
        print(f"[CONVERSATIONAL INTENT DETECTED] Processing '{clean_q}' as clean conversation.")
        prompt = f"""You are the Official devNectar WhatsApp Assistant.
devNectar is a professional software development firm.

STRICT RULES:
1. Respond politely, warmly, and concisely to the user's input.
2. Keep the conversation natural, friendly, and very brief.
3. If the user said thanks, acknowledge it warmly (e.g. "You're welcome! Let me know if you need anything else.").

USER CONVERSATIONAL INPUT: {user_question}

Answer:"""
        ai_text = "I'm sorry, I encountered an error. Please try again."
        try:
            response = model.generate_content(prompt)
            ai_text = response.text.strip()
        except Exception as e:
            print(f"Gemini Error: {e}")
            
        ai_text = ai_text.encode('ascii', errors='ignore').decode('ascii')
        print(f"[AI_GEN CONVERSATIONAL] Response: {ai_text}")
        return {"text": ai_text, "image_url": ""}

    # --- STANDARD RAG PATH FOR PRODUCT / SEARCH QUERIES ---
    collection = get_chroma_collection()
    context = ""

    # --- FAST PATH: Detect list queries and fetch directly ---
    detected_type = None
    for keyword, record_type in LIST_KEYWORDS.items():
        if keyword in question_lower:
            detected_type = record_type
            break

    if detected_type:
        print(f"[SMART SEARCH] Detected list query for type: '{detected_type}' - using direct fetch")
        context = get_all_by_type(collection, detected_type)

    # --- FALLBACK: Standard semantic search ---
    if not context:
        safe_q = user_question.encode('ascii', 'ignore').decode('ascii')
        print(f"[{time.strftime('%H:%M:%S')}] Standard semantic search for: {safe_q}")
        try:
            # First check how many records exist for this app
            all_records = collection.get(where={"app_id": APP_ID})
            total_count = len(all_records["ids"]) if all_records["ids"] else 0
            safe_n = min(5, max(1, total_count))
            print(f"[SEARCH] Total records available: {total_count}, fetching top {safe_n}")

            results = collection.query(
                query_texts=[user_question],
                n_results=safe_n,
                where={"app_id": APP_ID}
            )
            if results["documents"] and results["documents"][0]:
                context = "\n---\n".join(results["documents"][0])
        except Exception as e:
            print(f"[SEARCH ERROR] {e}")
            context = ""

    if not context:
        context = "No specific data found. Answer from your general devNectar knowledge."

    safe_context = context[:300].encode('ascii', 'ignore').decode('ascii')
    print(f"--- CONTEXT ---\n{safe_context}...\n--- END CONTEXT ---")

    # Build Prompt
    prompt = f"""You are the Official devNectar WhatsApp Assistant.
devNectar is a professional software development firm.

STRICT RULES:
1. Use the CONTEXT below to answer.
2. Never say "I don't have information" if the CONTEXT has relevant data.
3. Keep responses concise and WhatsApp-friendly (use bullet points or numbered lists when listing items).
4. Never mention "CONTEXT" or "DATABASE" to the user.
5. Do NOT use markdown image syntax.

CONTEXT:
{context}

USER QUESTION: {user_question}

Answer:"""

    # Ask Gemini
    ai_text = "I'm sorry, I encountered an error. Please try again."
    try:
        response = model.generate_content(prompt)
        ai_text = response.text.strip()
    except Exception as e:
        print(f"Gemini Error: {e}")

    # Inject price from context if found
    image_url = ""
    for line in context.split("\n"):
        if line.lower().startswith("image:"):
            image_url = line.split(":", 1)[1].strip()
            break

    # Sanitize output to prevent Windows charmap encoding crashes
    ai_text = ai_text.encode('ascii', errors='ignore').decode('ascii')

    print(f"[AI_GEN] Response: {ai_text[:200]}")
    return {"text": ai_text, "image_url": image_url}
