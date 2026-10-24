from qdrant_client import QdrantClient, models
from app.config import settings
from app.utils.bijoy_converter import convert_bijoy_to_unicode

class QdrantService:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            cloud_inference=True,
            timeout=60.0
        )
        self.collection = settings.COLLECTION_NAME
        self.model = settings.EMBEDDING_MODEL

    def search_context(self, query: str, limit: int = 6) -> str:
        try:
            # ইউজার যদি PDF থেকে সরাসরি ভাঙা টেক্সট কপি করে পেস্ট করে, সেটিও ক্লিন করে নেওয়া হবে
            clean_query = convert_bijoy_to_unicode(query.strip())

            # ১. Exact Keyword / Phrase Search (ডিরেক্ট ম্যাচ খোঁজার জন্য)
            exact_hits = []
            try:
                scroll_res, _ = self.client.scroll(
                    collection_name=self.collection,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="text",
                                match=models.MatchText(text=clean_query)
                            )
                        ]
                    ),
                    limit=3
                )
                exact_hits = scroll_res
            except Exception:
                pass

            # ২. Semantic Vector Search
            vector_hits = self.client.query_points(
                collection_name=self.collection,
                query=models.Document(
                    text=f"query: {clean_query}",
                    model=self.model
                ),
                limit=limit
            ).points

            # ৩. ডিরেক্ট ম্যাচ এবং ভেক্টর ম্যাচ একত্র করা (ডুপ্লিকেট বাদ দিয়ে)
            seen_ids = set()
            combined_results = []

            for hit in exact_hits:
                if hit.id not in seen_ids:
                    seen_ids.add(hit.id)
                    combined_results.append(hit)

            for hit in vector_hits:
                if hit.id not in seen_ids:
                    seen_ids.add(hit.id)
                    combined_results.append(hit)

            if not combined_results:
                return ""

            # ৪. চাঙ্কগুলোকে LLM-এর জন্য সুন্দরভাবে সাজানো
            context_parts = []
            for hit in combined_results[:limit]:
                source = hit.payload.get("source", "Document")
                page = hit.payload.get("page", "Unknown")
                text = hit.payload.get("text", "")
                context_parts.append(f"\n{text}")

            return "\n\n---\n\n".join(context_parts)

        except Exception as e:
            print(f"[Qdrant Error] {e}")
            return ""

qdrant_service = QdrantService()