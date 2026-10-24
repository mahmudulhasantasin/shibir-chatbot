from qdrant_client import QdrantClient, models
from app.config import settings

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

    def search_context(self, query: str, limit: int = 6) -> str: # limit 2 theke 1 koro
        try:
            search_result = self.client.query_points(
                collection_name=self.collection,
                query=models.Document(
                    text=f"query: {query}",
                    model=self.model
                ),
                limit=limit
            ).points

            if not search_result:
                return ""

            # চাঙ্কগুলোকে একসাথে জোড়া লাগানো
            context_parts = []
            for hit in search_result:
                page = hit.payload.get("page", "Unknown")
                text = hit.payload.get("text", "")
                context_parts.append(f"[Page {page}]\n{text}")

            return "\n\n---\n\n".join(context_parts)
        except Exception as e:
            print(f"[Qdrant Error] {e}")
            return ""

qdrant_service = QdrantService()