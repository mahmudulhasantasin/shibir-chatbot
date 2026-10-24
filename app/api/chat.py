from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.qdrant_service import qdrant_service
from app.services.llm_service import llm_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    suggested_questions: list[str]

@router.post("/ask", response_model=ChatResponse)
async def ask_pdf_bot(payload: ChatRequest):
    query = payload.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # ১. Qdrant থেকে কনটেক্সট বের করা
    context = qdrant_service.search_context(query)

    # ২. LLM দিয়ে উত্তর জেনারেট করা
    result = await llm_service.generate_answer(query, context)

    return ChatResponse(
        answer=result["answer"],
        suggested_questions=result["suggested_questions"]
    )