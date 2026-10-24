import os
import re
import hashlib
import glob
import time
import sys
import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient, models

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from app.utils.bijoy_converter import convert_bijoy_to_unicode

env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "shibir-member"
VECTOR_SIZE = 384  # intfloat/multilingual-e5-small

if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("[ERROR] QDRANT_URL or QDRANT_API_KEY not found in .env file!")

client = QdrantClient(
    url=QDRANT_URL, 
    api_key=QDRANT_API_KEY, 
    cloud_inference=True,
    timeout=120.0
)

def generate_chunk_id(source: str, index: int, text: str) -> str:
    """ইউনিক MD5 হ্যাশ আইডি"""
    raw = f"{source}_{index}_{text}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def setup_collection():
    """পুরনো কালেকশন ডিলিট করে নতুন কালেকশন ও টেক্সট ইনডেক্স তৈরি করে"""
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        print(f"[INFO] Deleted existing collection: {COLLECTION_NAME}")
        
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE, 
            distance=models.Distance.COSINE
        )
    )
    # ✅ ডিরেক্ট টেক্সট সার্চের (Exact Match) জন্য Full-Text Index তৈরি করা হচ্ছে
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="text",
        field_schema=models.TextIndexParams(
            type="text",
            tokenizer=models.TokenizerType.MULTILINGUAL,
            min_token_len=2,
            lowercase=True
        )
    )
    print(f"[SUCCESS] Created new clean collection with Text Index: {COLLECTION_NAME}")

def ingest_documents():
    documents_dir = os.path.join(base_dir, "documents")
    pdf_files = glob.glob(os.path.join(documents_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"[WARNING] No PDF files found in: {documents_dir}")
        return

    print(f"[INFO] Found {len(pdf_files)} PDF files. Starting processing...")

    # ✅ প্রশ্নোত্তর ও ধারার সীমানা অক্ষুণ্ণ রেখে চাঙ্কিং করার কাস্টম সেপারেটর
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=300,
        separators=[
            "\nধারা-", 
            "\n১।", "\n২।", "\n৩।", "\n৪।", "\n৫।", "\n৬।", "\n৭।", "\n৮।", "\n৯।",
            "\n\n", 
            "\n", 
            "। ", 
            " ", 
            ""
        ],
        keep_separator=True
    )

    all_points = []

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"\n[INFO] Reading: {filename}")
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # ১. পুরো PDF-এর টেক্সট একসাথে জোড়া লাগানো হচ্ছে যাতে পাতার মাঝখানে উত্তর কেটে না যায়
            full_doc_text = []
            page_char_offsets = []  # কোন ক্যারেক্টার কত নম্বর পাতায় তা ট্র্যাক করার জন্য
            current_offset = 0

            for page_num in range(total_pages):
                raw_text = doc[page_num].get_text("text")
                if not raw_text or not raw_text.strip():
                    continue

                # পাতার নিচে থাকা শুধু পৃষ্ঠা নম্বর যেমন (3), ( 12 ) মুছে ফেলা হচ্ছে যাতে উত্তর না ভাঙে
                cleaned_page = convert_bijoy_to_unicode(raw_text)
                cleaned_page = re.sub(r"\n\s*\(?\s*[০-৯0-9]+\s*\)?\s*$", "", cleaned_page.strip())

                page_char_offsets.append((current_offset, page_num + 1))
                full_doc_text.append(cleaned_page)
                current_offset += len(cleaned_page) + 2  # +2 for "\n\n"

            combined_text = "\n\n".join(full_doc_text)
            chunks = text_splitter.split_text(combined_text)

            # প্রতিটি চাঙ্কের আনুমানিক পেজ নম্বর বের করা ও পয়েন্ট তৈরি করা
            search_pos = 0
            for idx, chunk in enumerate(chunks):
                chunk = chunk.strip()
                if not chunk:
                    continue

                pos = combined_text.find(chunk[:50], search_pos)
                if pos != -1:
                    search_pos = pos

                page_no = 1
                for offset, p_num in page_char_offsets:
                    if pos >= offset:
                        page_no = p_num
                    else:
                        break

                chunk_id = generate_chunk_id(filename, idx, chunk)
                
                point = models.PointStruct(
                    id=chunk_id,
                    vector=models.Document(
                        text=f"passage: {chunk}", 
                        model="intfloat/multilingual-e5-small"
                    ),
                    payload={
                        "text": chunk,
                        "source": filename,
                        "page": page_no,
                        "chunk_index": idx
                    }
                )
                all_points.append(point)
            
            print(f"   ... Extracted {len(chunks)} clean chunks from {total_pages} pages.")
            doc.close()
                    
        except Exception as e:
            print(f"[ERROR] Failed to process {filename}: {e}")

    if not all_points:
        print("[WARNING] No text chunks were generated.")
        return

    print(f"\n[INFO] Total {len(all_points)} chunks will be uploaded to Qdrant...")

    batch_size = 50
    for i in range(0, len(all_points), batch_size):
        batch = all_points[i:i+batch_size]
        try:
            client.upsert(collection_name=COLLECTION_NAME, points=batch)
            print(f"   [SUCCESS] Uploaded: {min(i+batch_size, len(all_points))} / {len(all_points)}")
            time.sleep(0.5) 
        except Exception as e:
            print(f"   [ERROR] Batch upload failed: {e}. Retrying in 5s...")
            time.sleep(5)
            client.upsert(collection_name=COLLECTION_NAME, points=batch)
            print(f"   [SUCCESS on RETRY] Uploaded: {min(i+batch_size, len(all_points))} / {len(all_points)}")

    print(f"\n[SUCCESS] All data successfully saved to Qdrant!")

if __name__ == "__main__":
    setup_collection()
    ingest_documents()