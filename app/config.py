import os
from dotenv import load_dotenv
from pydantic import BaseModel

# .env ফাইল লোড করা (রুট ডিরেক্টরি থেকে)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)

class Settings(BaseModel):
    QDRANT_URL: str = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "") # অপশনাল
    
    COLLECTION_NAME: str = "shibir-member"
    VECTOR_SIZE: int = 384
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-small"

settings = Settings()

if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
    raise ValueError("❌ QDRANT_URL অথবা QDRANT_API_KEY .env ফাইলে নেই!")