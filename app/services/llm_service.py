from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.utils.json_parser import extract_json
from app.utils.bijoy_converter import convert_bijoy_to_unicode

SYSTEM_PROMPT = """You are a strict, verbatim Bengali text extractor for a PDF Assistant.
Your ONLY job is to find the exact answer to the user's question from the provided CONTEXT and return the EXACT text from the document without modifying the wording.

CRITICAL RULES:
1. DO NOT summarize, paraphrase, shorten, or rewrite the text in your own words. Keep the original sentence structure and words 100% identical to the context.
2. DO NOT add any introductory or concluding conversational filler (e.g., "ডকুমেন্ট অনুযায়ী উত্তর নিচে দেওয়া হলো:").
3. **DIRECT & COMPLETE ANSWER PRIORITY:** 
   - If the user asks for a specific question, rule, or article (like "ধারা-২", "ধারা-৪", "প্রথম দফা কর্মসূচীর কাজ কয়টি ও কি কি?"), find the exact matching heading/question in the context and extract its FULL answer.
   - NEVER truncate numbered lists or bullet points. If an answer has multiple points (১, ২, ৩...) or sub-sections (ক, খ, গ), you MUST include every single point verbatim.
   - If the full answer spans across two chunks in the context, merge them seamlessly in the right numerical order.
4. **Formatting:** Keep original numbering (১., ২., ৩. or ক., খ., গ.) and line breaks (\n) clean and readable.
5. **SPELLING & ARTIFACT CORRECTION:** Only fix broken Bijoy-to-Unicode font conversion errors while keeping the actual words identical:
   - Fix broken conjuncts: "সুসম্পনড়ব" -> "সুসম্পন্ন", "প্রশড়ব" -> "প্রশ্ন", "বিভিনড়ব" -> "বিভিন্ন", "অক্ষুনড়ব" -> "অক্ষুণ্ণ", "আলণ্টাহ" / "আলাহ" -> "আল্লাহ", "উলিখিত" -> "উল্লিখিত", "সিদ্ধাড়" -> "সিদ্ধান্ত"।
   - Fix broken Reph (রেফ), O-kar ("ে" + "া" -> "ো"), and double E-kar ("েে" -> "ে").
6. If the provided context does not contain the answer at all, return exactly:
   "দুঃখিত, এই বিষয়ে কোনো তথ্য ডকুমেন্টে পাওয়া যায়নি।"
7. You MUST return ONLY a valid JSON object matching this exact schema:
{
  "answer": "The exact, complete extracted text here with proper line breaks.",
  "suggested_questions": ["প্রাসঙ্গিক প্রশ্ন ১?", "প্রাসঙ্গিক প্রশ্ন ২?", "প্রাসঙ্গিক প্রশ্ন ৩?"]
}
8. The 'suggested_questions' MUST be 3 short, direct questions taken directly from other topics/questions visible in the provided CONTEXT (in Bengali). NEVER leave it empty if an answer is found."""


class LLMService:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model="openai/gpt-oss-120b",
            temperature=0.0,
            max_tokens=3500
        )

    async def generate_answer(self, query: str, context: str) -> dict:
        if not context or not context.strip():
            return {
                "answer": "দুঃখিত, আপনার প্রশ্নের সাথে সম্পর্কিত কোনো তথ্য ডকুমেন্টে পাওয়া যায়নি।",
                "suggested_questions": []
            }

        # ইউজারের প্রশ্ন ও কন্টেক্সট ক্লিন করে নেওয়া হচ্ছে যাতে ভাঙা শব্দের কারণে মিসম্যাচ না হয়
        clean_query = convert_bijoy_to_unicode(query.strip())
        clean_context = convert_bijoy_to_unicode(context)

        human_prompt = f"""CONTEXT FROM DOCUMENTS:
{clean_context}

USER QUESTION: {clean_query}

Extract the exact and complete text from the context that answers the question. Return valid JSON only."""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=human_prompt)
            ])
            
            raw_text = response.content if isinstance(response.content, str) else str(response.content)
            parsed_data = extract_json(raw_text)

            if not parsed_data or "answer" not in parsed_data:
                return {
                    "answer": convert_bijoy_to_unicode(raw_text),
                    "suggested_questions": []
                }

            # ফাইনাল আউটপুটে কোনো ভাঙা অক্ষর থাকলে তা আবারও ক্লিন করা হচ্ছে
            final_answer = convert_bijoy_to_unicode(parsed_data.get("answer", "").strip())
            suggested = parsed_data.get("suggested_questions", [])

            return {
                "answer": final_answer,
                "suggested_questions": suggested if isinstance(suggested, list) else []
            }

        except Exception as e:
            print(f"[LLM Error] {e}")
            return {
                "answer": "সার্ভারে একটি সমস্যা হয়েছে। দয়া করে আবার চেষ্টা করুন।",
                "suggested_questions": []
            }

llm_service = LLMService()