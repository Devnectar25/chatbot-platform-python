from fastapi import FastAPI
from app.api.routes import router

# Removed async lifespan warmup to support Vercel serverless startup
app = FastAPI(title="Multi-Tenant Chatbot API")

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Chatbot AI Service is running!"}
