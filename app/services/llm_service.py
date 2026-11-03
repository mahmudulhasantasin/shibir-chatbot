from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.config import settings
from app.utils.json_parser import extract_json
from app.utils.answer_guard import verify_extractive

SYSTEM_PROMPT = """You are a STRICT verbatim extractor for a Bengali PDF assistant.

Your ONLY job: locate the specific passage in the CONTEXT that answers the user's question and return it EXACTLY as it appears in the CONTEXT.

ABSOLUTE RULES:
1. **NO REWRITING:** NEVER paraphrase, summarize, translate, fix spellings, or fix OCR errors. The output MUST be a literal substring of the CONTEXT.
2. **DISTINGUISH COLLECTIVE VS ORDINAL (CRITICAL):**
   - 'পাঁচ দফা' means the entire 5-point program (১ম দফা, ২য় দফা, ৩য় দফা, ৪র্থ দফা, ৫ম দফা)।
   - 'পঞ্চম দফা' means ONLY the 5th point (৫ম দফা)।
   - If the user asks about 'পাঁচ দফা' or the overall program, NEVER confuse it with 'পঞ্চম দফা'. Return the complete 5-point program section.
3. **COMPLETE LISTS, CLEAN START & STOP CONDITION (CRITICAL):**
   - If the answer is a list (১, ২, ৩... or ক, খ, গ...), return ALL points verbatim. Do not truncate the list halfway.
   - **CLEAN START:** If the CONTEXT contains previous questions or paragraphs before the actual answer, IGNORE THEM. Start your extraction ONLY from the exact question heading (e.g., "যোগাযোগকারীর/ দায়ীর বৈশিষ্ট্যগুলো কি কি?") or directly from the list heading (e.g., "১৩ টি বৈশিষ্ট্য:"). DO NOT include previous questions or unrelated text.
   - **STOP CONDITION:** You must STOP extracting the exact moment a NEW QUESTION starts (e.g., "১৩। ক্রমান্বয়ে কর্মী পর্যায়ে নিয়ে আসা বলতে কি বোঝায়?"). Do NOT include the new question or its answer.
4. **ONLY THE EXACT ANSWER:** Do not return unrelated articles or unnecessary context. Extract only the relevant passage.
5. **NO FILLER:** DO NOT add any intro, outro, or conversational filler ("উত্তর নিচে দেওয়া হলো:", "ডকুমেন্ট অনুযায়ী:")।
6. **NO ANSWER FALLBACK:** If the answer is NOT present in the context, return exactly: "দুঃখিত, এই বিষয়ে কোনো তথ্য ডকুমেন্টে পাওয়া যায়নি।"
7. **FORMAT:** Return ONLY valid JSON:
{
  "answer": "…verbatim extracted text here…"
}
"""

# ★ সবচেয়ে স্মার্ট মডেলটি সবার আগে রাখা হলো
MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]


class LLMService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY

    async def _invoke_llm(self, messages):
        last_exception = None
        for model_name in MODELS:
            try:
                llm = ChatGroq(
                    api_key=self.api_key,
                    model=model_name,
                    temperature=0.0,
                    max_tokens=3500,
                )
                return await llm.ainvoke(messages)
            except Exception as e:
                last_exception = e
                print(f"[LLM Warning] Model {model_name} failed: {e}. Trying fallback...")
                continue
        raise last_exception or RuntimeError("All LLM models failed.")

    async def generate_answer(self, query: str, context: str) -> dict:
        if not context or not context.strip():
            return {
                "answer": "দুঃখিত, আপনার প্রশ্নের সাথে সম্পর্কিত কোনো তথ্য ডকুমেন্টে পাওয়া যায়নি।"
            }

        # ★ Safety Check: Groq API Limit (Max 8000 tokens) এড়াতে কন্টেক্সট ছোট করা
        MAX_CHARS = 16000  
        if len(context) > MAX_CHARS:
            print(f"[WARNING] Context too large ({len(context)} chars). Truncating to {MAX_CHARS} chars.")
            context = context[:MAX_CHARS]

        human_prompt = f"""CONTEXT:
{context}

USER QUESTION: {query}

Extract the exact verbatim text from CONTEXT that answers the question.
Return valid JSON only with the 'answer' key."""

        try:
            response = await self._invoke_llm([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=human_prompt),
            ])

            raw = response.content if isinstance(response.content, str) else str(response.content)
            parsed = extract_json(raw) or {}

            candidate = (parsed.get("answer") or "").strip()

            # যদি ডকুমেন্টে তথ্য না থাকে এবং LLM দুঃখিত/তথ্য পাওয়া যায়নি বলে
            if not candidate or any(phrase in candidate for phrase in ["পাওয়া যায়নি", "তথ্য নেই", "দুঃখিত"]):
                return {
                    "answer": candidate or "দুঃখিত, এই বিষয়ে কোনো তথ্য ডকুমেন্টে পাওয়া যায়নি।"
                }

            # ★ CORE GUARANTEE — verbatim check
            verified = verify_extractive(candidate, context)

            if verified is None:
                # ★ আগের মতো first_block (ভুল টেক্সট) না দিয়ে সরাসরি মেসেজ দেওয়া হলো
                print("[WARNING] Verification failed. LLM might have hallucinated.")
                return {
                    "answer": "দুঃখিত, সঠিক উত্তরটি খুঁজে পাওয়া যায়নি। দয়া করে প্রশ্নটি অন্যভাবে করুন।"
                }

            return {
                "answer": verified
            }

        except Exception as e:
            print(f"[LLM Error] {e}")
            return {
                "answer": "সার্ভারে একটি সমস্যা হয়েছে। দয়া করে আবার চেষ্টা করুন।"
            }


llm_service = LLMService()