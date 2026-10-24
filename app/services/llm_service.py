from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.utils.json_parser import extract_json

# 🔴 System Prompt সম্পূর্ণ পরিবর্তন করা হয়েছে যাতে LLM নিজের ভাষায় উত্তর না লিখে 
# শুধুমাত্র PDF-এর হুবহু টেক্সট রিটার্ন করে।
SYSTEM_PROMPT = """You are a strict, verbatim text extractor and a Bengali spelling proofreader for a PDF Assistant.
Your ONLY job is to find the answer to the user's question in the provided context and return the EXACT text from the document.

CRITICAL RULES:
1. DO NOT summarize, paraphrase, or rewrite the text in your own words. Keep the sentence structure exactly as it is.
2. DO NOT add any conversational filler.
3. **DIRECT ANSWER PRIORITY (Universal Rule):** If the user asks a question like "What is X?" or "What is the objective of Y?", you MUST first look for a direct definition, a specific rule, or an article (like "ধারা-২", "ধারা-৪") in the context that answers the question directly. Prioritize this direct text over general lists or related paragraphs.
4. Extract the exact paragraph(s) from the context that answer the user's question. Keep the original formatting (bullet points, numbering, etc.). If multiple paragraphs are relevant, combine them logically but DO NOT alter the wording.
5. **SPELLING CORRECTION (CRITICAL):** The provided PDF text contains common Bijoy-to-Unicode conversion errors. You MUST fix these errors while keeping the rest of the text identical:
   - Fix broken Reph (রেফ): e.g., Change "শিক্ষাথর্ী" to "শিক্ষার্থী".
   - Fix broken O-kar (ও-কার): e.g., Change "পোষণ" to "পোষণ", replace "ে" + "া" with "ো".
   - Fix double E-kar (এ-কার): e.g., Change "সক্রিয়ভাবেে" to "সক্রিয়ভাবে".
6. If the context does not contain the answer at all, say "দুঃখিত, এই বিষয়ে কোনো তথ্য ডকুমেন্টে পাওয়া যায়নি।"
7. You MUST return exactly a valid JSON object matching this schema:
{
  "answer": "The exact extracted text here (with corrected spellings).",
  "suggested_questions": ["Question 1?", "Question 2?", "Question 3?"]
}
8. The 'suggested_questions' MUST be highly relevant follow-up questions. Keep them short and in the SAME language as the user's question. NEVER leave it empty.

Return ONLY the raw JSON. Do not wrap in markdown code blocks."""

class LLMService:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            # 🔴 মডেল নেম ঠিক করা হয়েছে (Groq-এ qwen3.8-27b নেই)
            model="openai/gpt-oss-120b", 
            # 🔴 temperature=0.0 করা হয়েছে যাতে মডেল একদম কঠোরভাবে প্রম্পট মানে
            temperature=0.0, 
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

USER QUESTION: {query}

Extract the exact text from the context that answers the question."""

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