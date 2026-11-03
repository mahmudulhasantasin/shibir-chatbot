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

    def search_context(self, query: str, limit: int = 4) -> str:
        try:
            clean_query = query.strip()
            if not clean_query:
                return ""

            # ১. Exact Keyword / Phrase Search
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
                    limit=2,
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

            # ★ ৪. Context Expansion (শুধুমাত্র পরের +1 এবং +2 চাঙ্ক আনবো, আগের -1 বাদ দিলাম)
            expanded_hits = list(combined)
            
            if combined: 
                top_hit = combined[0]
                source = top_hit.payload.get("source", "")
                current_idx = top_hit.payload.get("chunk_index", 0)
                
                for offset in [1, 2]:  # ★ -1 বাদ, শুধু পরের ২টি চাঙ্ক খুঁজবো
                    neighbor_idx = current_idx + offset
                    
                    # চেক করা: এই চাঙ্কটা কি লিস্টে আগেই আছে?
                    if any(h.payload.get("source") == source and h.payload.get("chunk_index") == neighbor_idx for h in expanded_hits):
                        continue

                    try:
                        neighbor_res, _ = self.client.scroll(
                            collection_name=self.collection,
                            scroll_filter=models.Filter(
                                must=[
                                    models.FieldCondition(key="source", match=models.MatchValue(value=source)),
                                    models.FieldCondition(key="chunk_index", match=models.MatchValue(value=neighbor_idx)),
                                ]
                            ),
                            limit=1,
                        )
                        if neighbor_res:
                            expanded_hits.append(neighbor_res[0])
                            print(f"[CONTEXT EXPANSION] Fetched chunk {neighbor_idx} from {source}")
                    except Exception as e:
                        print(f"[CONTEXT EXPANSION ERROR] {e}")

            # ★ ৫. সিরিয়ালি সাজানো (Sort by chunk_index)
            expanded_hits.sort(key=lambda x: x.payload.get("chunk_index", 0))

            # ডুপ্লিকেট রিমুভ করা
            final_hits = []
            final_seen = set()
            for h in expanded_hits:
                if h.id not in final_seen:
                    final_seen.add(h.id)
                    final_hits.append(h)

            # ★ ৬. সর্বোচ্চ ৫টি চাঙ্ক রাখবো (Groq API-এর টোকেন লিমিট বাঁচাতে)
            final_hits = final_hits[:5]

            # ৭. LLM-এর জন্য context arrange
            parts = []
            for hit in final_hits:
                text = hit.payload.get("text", "").strip()
                if text:
                    parts.append(text)

            return "\n\n---\n\n".join(parts)

        except Exception as e:
            print(f"[Qdrant Error] {e}")
            return ""


qdrant_service = QdrantService()