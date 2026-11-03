from qdrant_client import QdrantClient, models
from app.config import settings


class QdrantService:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            cloud_inference=True,
            timeout=60.0,
        )
        self.collection = settings.COLLECTION_NAME
        self.model = settings.EMBEDDING_MODEL

    def search_context(self, query: str, limit: int = 10) -> str:
        try:
            clean_query = query.strip()
            if not clean_query:
                return ""

            # ১. Exact Keyword / Phrase Search (hybrid)
            exact_hits = []
            try:
                scroll_res, _ = self.client.scroll(
                    collection_name=self.collection,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="text",
                                match=models.MatchText(text=clean_query),
                            )
                        ]
                    ),
                    limit=3,
                )
                exact_hits = scroll_res
            except Exception:
                pass

            # ২. Semantic Vector Search
            vector_hits = self.client.query_points(
                collection_name=self.collection,
                query=models.Document(
                    text=f"query: {clean_query}",
                    model=self.model,
                ),
                limit=limit,
            ).points

            # ৩. Combine + dedupe
            seen_ids = set()
            combined = []
            for hit in exact_hits:
                if hit.id not in seen_ids:
                    seen_ids.add(hit.id)
                    combined.append(hit)
            for hit in vector_hits:
                if hit.id not in seen_ids:
                    seen_ids.add(hit.id)
                    combined.append(hit)

            if not combined:
                return ""

            # ৪. LLM-এর জন্য context arrange
            parts = []
            for hit in combined[:limit]:
                text = hit.payload.get("text", "").strip()
                if text:
                    parts.append(text)

            return "\n\n---\n\n".join(parts)

        except Exception as e:
            print(f"[Qdrant Error] {e}")
            return ""


qdrant_service = QdrantService()