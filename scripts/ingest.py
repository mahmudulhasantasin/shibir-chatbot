# scripts/ingest.py
"""
Full OCR pipeline:
  PDF → page image (300 DPI) → OCR → per-page txt → chunk → Qdrant
Collection name: "shibir-member" (same as before)
"""
import os
import sys
import time
import asyncio
import hashlib
import re
from pathlib import Path

import fitz  # PyMuPDF
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---- chrome_lens_py (OCR engine) ----
try:
    from chrome_lens_py import LensAPI
except ImportError:
    LensAPI = None
    print("⚠️  chrome_lens_py not installed. Run: pip install chrome_lens_py")

# ---- paths / env ----
base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))
load_dotenv(base_dir / ".env")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = "shibir-member"
VECTOR_SIZE = 384
EMBED_MODEL = "intfloat/multilingual-e5-small"

DOCUMENTS_DIR = base_dir / "documents"
OCR_DIR = DOCUMENTS_DIR / "ocr_output"
OCR_DIR.mkdir(parents=True, exist_ok=True)

if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("[ERROR] QDRANT_URL or QDRANT_API_KEY missing in .env")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    cloud_inference=True,
    timeout=180.0,
)


# =====================================================
# 1) OCR & Text Cleaning
# =====================================================
def clean_ocr_text(text: str) -> str:
    """OCR থেকে আসা এলোমেলো লাইন ব্রেক এবং বুলেট পয়েন্টগুলো ঠিক করে"""
    if not text:
        return text
    
    # ১. বুলেট পয়েন্টের (•, *, -) আগে নতুন লাইন যোগ করা
    text = re.sub(r'(?<!\n)\s*([•\*])\s*', r'\n\1 ', text)
    
    # ২. বাংলা সংখ্যার (১. ২. ৩. বা ১। ২।) আগে নতুন লাইন যোগ করা
    text = re.sub(r'(?<!\n)\s+(?=[০-৯]+[।\.])', '\n', text)
    
    # ৩. ইংরেজি সংখ্যার (1. 2. 3.) আগে নতুন লাইন যোগ করা
    text = re.sub(r'(?<!\n)\s+(?=\d+\.\s)', '\n', text)
    
    # ৪. অতিরিক্ত স্পেস বা খালি লাইন পরিষ্কার করা
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()


def render_page(doc, i: int, dpi: int = 300) -> Path:
    """Render page i (0-indexed) to PNG at given DPI."""
    page = doc[i]
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    out = OCR_DIR / f"page_{i + 1:03d}.png"
    pix.save(str(out))
    return out


async def ocr_page(api, img_path: Path) -> str:
    """
    Run OCR on a single page image.
    'bn' code on Chrome Lens handles mixed Bangla + Arabic + English.
    """
    try:
        res = await api.process_image(image_path=str(img_path), ocr_language="bn")
        return (res.get("ocr_text") or "").strip()
    except Exception as e:
        print(f"   [OCR FAIL] {img_path.name}: {e}")
        return ""


async def ocr_pdf(pdf_path: Path) -> list[dict]:
    """OCR every page. Returns [{'page': n, 'text': str}, ...]."""
    doc = fitz.open(pdf_path)
    api = LensAPI()
    pages = []

    for i in range(len(doc)):
        txt_path = OCR_DIR / f"page_{i + 1:03d}.txt"
        
        # ★ CACHE LOGIC: যদি txt ফাইল আগেই থাকে, তবে আর OCR করবে না, সোজা পড়ে নেবে
        if txt_path.exists():
            raw_text = txt_path.read_text(encoding="utf-8")
            text = clean_ocr_text(raw_text)
            txt_path.write_text(text, encoding="utf-8") 
            print(f"   [CACHE+CLEAN] page {i + 1:03d}/{len(doc):03d}  ({len(text)} chars)")
        else:
            img = render_page(doc, i)
            raw_text = await ocr_page(api, img)
            text = clean_ocr_text(raw_text)
            txt_path.write_text(text, encoding="utf-8")
            print(f"   [OCR+CLEAN] page {i + 1:03d}/{len(doc):03d}  ({len(text)} chars)")
            
        pages.append({"page": i + 1, "text": text})

    doc.close()
    return pages


# =====================================================
# 2) Document reconstruction
# =====================================================
def reconstruct(pages: list[dict]):
    """Join pages with '\\n\\n' and build offset → page map."""
    full, offsets, cur = [], [], 0
    for p in pages:
        offsets.append((cur, p["page"]))
        full.append(p["text"])
        cur += len(p["text"]) + 2
    return "\n\n".join(full), offsets


def page_at(offsets, pos: int) -> int:
    page = 1
    for off, p in offsets:
        if pos >= off:
            page = p
        else:
            break
    return page


# =====================================================
# 3) Chunking
# =====================================================
def chunk_all(full_text: str, offsets):
    # ★ এখানে চাঙ্ক সাইজ ৮০০০ করা হয়েছে যাতে লম্বা লিস্টও একসাথে থাকে
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=8000,     # ★ ৩০০০ থেকে বাড়িয়ে ৮০০০ করা হলো
        chunk_overlap=1000,  # ★ ৫০০ থেকে বাড়িয়ে ১০০০ করা হলো
        keep_separator=True,
        separators=[
            "\nধারা-",
            "\nপ্রশ্ন", "\nউত্তর",
            "\n\n", "\n", "। ", " ", "",
        ],
    )

    chunks, search_pos = [], 0
    for idx, ch in enumerate(splitter.split_text(full_text)):
        ch = ch.strip()
        if not ch:
            continue
        found = full_text.find(ch[:60], search_pos)
        if found != -1:
            search_pos = found
        chunks.append({
            "text": ch,
            "page": page_at(offsets, search_pos),
            "idx": idx,
        })
    return chunks


# =====================================================
# 4) Qdrant
# =====================================================
def setup_collection():
    """Delete old collection (dirty data) and recreate with text index."""
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
        print(f"[SETUP] Deleted old collection: {COLLECTION}")

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE,
            distance=models.Distance.COSINE,
        ),
    )
    # ★ টেক্সট ইনডেক্স
    client.create_payload_index(
        collection_name=COLLECTION,
        field_name="text",
        field_schema=models.TextIndexParams(
            type="text",
            tokenizer=models.TokenizerType.MULTILINGUAL,
            min_token_len=2,
            lowercase=True,
        ),
    )
    # ★ নতুন যোগ করা সোর্স এবং চাঙ্ক ইনডেক্স (পরের চাঙ্ক খুঁজতে কাজে লাগবে)
    client.create_payload_index(
        collection_name=COLLECTION,
        field_name="source",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=COLLECTION,
        field_name="chunk_index",
        field_schema=models.PayloadSchemaType.INTEGER,
    )
    print(f"[SETUP] Fresh collection ready with indexes: {COLLECTION}")


def make_id(source: str, idx: int, text: str) -> str:
    return hashlib.md5(f"{source}_{idx}_{text}".encode("utf-8")).hexdigest()


# =====================================================
# 5) Main
# =====================================================
async def main():
    pdfs = sorted(DOCUMENTS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"[ERROR] No PDFs found in: {DOCUMENTS_DIR}")
        return

    print(f"[INFO] Found {len(pdfs)} PDF(s)")
    setup_collection()

    all_points = []

    for pdf in pdfs:
        print(f"\n[PDF] {pdf.name}")
        pages = await ocr_pdf(pdf)
        full, offsets = reconstruct(pages)
        chunks = chunk_all(full, offsets)
        print(f"   → {len(chunks)} chunks from {len(pages)} pages")

        for ch in chunks:
            all_points.append(
                models.PointStruct(
                    id=make_id(pdf.name, ch["idx"], ch["text"]),
                    vector=models.Document(
                        text=f"passage: {ch['text']}",
                        model=EMBED_MODEL,
                    ),
                    payload={
                        "text": ch["text"],
                        "source": pdf.name,
                        "page": ch["page"],
                        "chunk_index": ch["idx"],
                    },
                )
            )

    if not all_points:
        print("[WARNING] No chunks generated.")
        return

    print(f"\n[UPLOAD] {len(all_points)} points → {COLLECTION}")
    batch = 50
    for i in range(0, len(all_points), batch):
        client.upsert(collection_name=COLLECTION, points=all_points[i:i + batch])
        print(f"   [OK] {min(i + batch, len(all_points))}/{len(all_points)}")
        time.sleep(0.4)

    print(f"\n[SUCCESS] All data saved to Qdrant.")


if __name__ == "__main__":
    asyncio.run(main())