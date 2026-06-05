import os
from fastapi import FastAPI, Request
from app.api.routes import router

# Removed async lifespan warmup to support Vercel serverless startup
app = FastAPI(title="Multi-Tenant Chatbot API")

@app.middleware("http")
async def clean_env_middleware(request: Request, call_next):
    # Clean environment variables from copy-paste errors (like KEY=value instead of just value)
    for k, v in list(os.environ.items()):
        if v:
            cleaned = v.strip().strip("'\"")
            if cleaned.startswith(f"{k}="):
                cleaned = cleaned[len(k)+1:].strip().strip("'\"")
            if cleaned != v:
                os.environ[k] = cleaned
    return await call_next(request)

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Chatbot AI Service is running!"}
