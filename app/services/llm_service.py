from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.utils.json_parser import extract_json

SYSTEM_PROMPT = """You are an intelligent PDF Assistant for a member portal. 
Your task is to answer the user's question STRICTLY based on the provided context from the PDF documents.

CRITICAL RULES:
1. Do NOT use any outside knowledge. If the answer is not in the context, say "I could not find this information in the provided documents."
2. Do NOT include any greetings or conversational filler.
3. You MUST return exactly a valid JSON object matching this schema:
{
  "answer": "Your detailed answer here (Markdown allowed)",
  "suggested_questions": ["Question 1?", "Question 2?", "Question 3?"]
}
4. The 'suggested_questions' MUST be highly relevant follow-up questions based on the context. Keep them short and in the SAME language as the user's question.
If you cannot find the answer, leave 'suggested_questions' as an empty array [].

Return ONLY the raw JSON. Do not wrap in markdown code blocks."""

class LLMService:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model="qwen/qwen3.8-27b", # অথবা llama-3.3-70b-versatile
            temperature=0.1,
            max_tokens=2000
        )

    async def generate_answer(self, query: str, context: str) -> dict:
        if not context:
            return {
                "answer": "দুঃখিত, আপনার প্রশ্নের সাথে সম্পর্কিত কোনো তথ্য ডকুমেন্টে পাওয়া যায়নি।",
                "suggested_questions": []
            }

        human_prompt = f"""CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION: {query}"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=human_prompt)
            ])
            
            raw_text = response.content if isinstance(response.content, str) else str(response.content)
            parsed_data = extract_json(raw_text)

            if not parsed_data or "answer" not in parsed_data:
                return {
                    "answer": raw_text, # Fallback if JSON fails
                    "suggested_questions": []
                }

            return {
                "answer": parsed_data.get("answer", ""),
                "suggested_questions": parsed_data.get("suggested_questions", [])
            }

        except Exception as e:
            print(f"[LLM Error] {e}")
            return {
                "answer": "সার্ভারে একটি সমস্যা হয়েছে। দয়া করে আবার চেষ্টা করুন।",
                "suggested_questions": []
            }

llm_service = LLMService()