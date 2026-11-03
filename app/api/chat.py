from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.qdrant_service import qdrant_service
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str

# ★ শুধু answer থাকবে
class ChatResponse(BaseModel):
    answer: str

@router.post("/ask", response_model=ChatResponse)
async def ask_pdf_bot(payload: ChatRequest):
    query = payload.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    context = qdrant_service.search_context(query)
    result = await llm_service.generate_answer(query, context)

    return ChatResponse(answer=result["answer"])