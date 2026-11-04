from qdrant_client import QdrantClient, models
from app.config import settings


def is_list_query(query: str) -> bool:
    """প্রশ্নটি কি লিস্ট চাইছে নাকি সাধারণ প্রশ্ন"""
    list_keywords = [
        "কি কি", "কী কী", "কয়টি", "কতটি", "কয়টা", "নাম কি",
        "বৈশিষ্ট্য", "গুলোর", "গুলির", "লিস্ট", "তালিকা",
        "প্রকার", "ধরন", "দফা", "ধারা"
    ]
    return any(kw in query for kw in list_keywords)


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

    def search_context(self, query: str, limit: int = 3) -> str:
        try:
            clean_query = query.strip()
            if not clean_query:
                return ""

            # ★ ০. প্রশ্নের ধরন বুঝে বাজেট ঠিক করা
            is_list = is_list_query(clean_query)
            if is_list:
                MAX_CONTEXT_CHARS = 14000
                MAX_CHUNKS = 3
            else:
                MAX_CONTEXT_CHARS = 7000
                MAX_CHUNKS = 1

            print(f"[CONTEXT PLAN] is_list={is_list}, max_chars={MAX_CONTEXT_CHARS}, max_chunks={MAX_CHUNKS}")

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

            # ★ ৪. Context Expansion (শুধুমাত্র লিস্ট প্রশ্নের জন্য পরের চাঙ্কগুলো আনবো)
            expanded_hits = list(combined)
            
            if combined and is_list:
                top_hit = combined[0]
                source = top_hit.payload.get("source", "")
                current_idx = top_hit.payload.get("chunk_index", 0)
                
                for offset in [1, 2]:  # লিস্টের ধারাবাহিকতা রক্ষার জন্য +1 এবং +2
                    neighbor_idx = current_idx + offset
                    
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

            # ৫. সিরিয়ালি সাজানো (Sort by chunk_index)
            expanded_hits.sort(key=lambda x: x.payload.get("chunk_index", 0))

            # ডুপ্লিকেট রিমুভ করা
            final_hits = []
            final_seen = set()
            for h in expanded_hits:
                if h.id not in final_seen:
                    final_seen.add(h.id)
                    final_hits.append(h)

            # ★ ৬. ক্যারেক্টার বাজেটের ভেতরে কন্টেক্সট তৈরি (যাতে 413 Error না আসে)
            parts = []
            total_chars = 0
            for hit in final_hits[:MAX_CHUNKS]:
                text = hit.payload.get("text", "").strip()
                if not text:
                    continue
                if total_chars + len(text) > MAX_CONTEXT_CHARS and parts:
                    print(f"[CONTEXT CAP] Reached {total_chars} chars, stopping.")
                    break
                parts.append(text)
                total_chars += len(text)

            print(f"[CONTEXT BUILT] {len(parts)} chunks, {total_chars} chars total")
            return "\n\n---\n\n".join(parts)

        except Exception as e:
            print(f"[Qdrant Error] {e}")
            return ""


qdrant_service = QdrantService()