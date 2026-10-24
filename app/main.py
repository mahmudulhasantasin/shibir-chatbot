from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router

app = FastAPI(title="Shibir PDF Chatbot API") # ✅ এই লাইনটা থাকতে হবে

# CORS সেটআপ
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Backend is running perfectly!"}