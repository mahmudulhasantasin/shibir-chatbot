import os
import hashlib
import glob
import time
import sys
import fitz  # PyMuPDF
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient, models

# প্রজেক্টের রুট ডিরেক্টরি সেট করা (যাতে app.utils ইমপোর্ট করা যায়)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

# ✅ বিজয় টু ইউনিকোড কনভার্টার ইমপোর্ট
from app.utils.bijoy_converter import convert_bijoy_to_unicode

env_path = os.path.join(base_dir, ".env")
load_dotenv(env_path)

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "shibir-member"
VECTOR_SIZE = 384 # intfloat/multilingual-e5-small

if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("[ERROR] QDRANT_URL or QDRANT_API_KEY not found in .env file!")

client = QdrantClient(
    url=QDRANT_URL, 
    api_key=QDRANT_API_KEY, 
    cloud_inference=True,
    timeout=120.0
)

def generate_chunk_id(text: str) -> str:
    """প্রতিটি চাঙ্কের জন্য ইউনিক MD5 হ্যাশ আইডি"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def setup_collection():
    """পুরনো কালেকশন ডিলিট করে নতুন পরিষ্কার কালেকশন তৈরি করে"""
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        print(f"[INFO] Deleted existing (corrupted) collection: {COLLECTION_NAME}")
        
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE, 
            distance=models.Distance.COSINE
        )
    )
    print(f"[SUCCESS] Created new clean collection: {COLLECTION_NAME}")

def ingest_documents():
    documents_dir = os.path.join(base_dir, "documents")
    pdf_files = glob.glob(os.path.join(documents_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"[WARNING] No PDF files found in: {documents_dir}")
        return

    print(f"[INFO] Found {len(pdf_files)} PDF files. Starting processing...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, 
        chunk_overlap=200,
        separators=["\n\n", "\n", "।", ".", " ", ""]
    )

    all_points = []

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"\n[INFO] Reading: {filename}")
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                raw_text = page.get_text("text")
                
                if not raw_text or not raw_text.strip():
                    continue

                # ✅ টেক্সট এক্সট্রাক্ট করে বিজয় থেকে ইউনিকোডে কনভার্ট করা হচ্ছে
                # (এই ফাংশনটি ইংরেজি এবং আরবি টেক্সটকে অক্ষত রাখবে)
                page_text = convert_bijoy_to_unicode(raw_text)

                chunks = text_splitter.split_text(page_text)
                
                for chunk in chunks:
                    chunk_id = generate_chunk_id(chunk)
                    
                    point = models.PointStruct(
                        id=chunk_id,
                        vector=models.Document(
                            text=f"passage: {chunk}", 
                            model="intfloat/multilingual-e5-small"
                        ),
                        payload={
                            "text": chunk,
                            "source": filename,
                            "page": page_num + 1
                        }
                    )
                    all_points.append(point)
                
                if (page_num + 1) % 50 == 0:
                    print(f"   ... Processed {page_num + 1}/{total_pages} pages")
            
            doc.close()
                    
        except Exception as e:
            print(f"[ERROR] Failed to process {filename}: {e}")

    if not all_points:
        print("[WARNING] No text chunks were generated.")
        return

    print(f"\n[INFO] Total {len(all_points)} chunks will be uploaded to Qdrant...")

    # ✅ Qdrant API Timeout এড়াতে ব্যাচ সাইজ ৫০ রাখা হলো
    batch_size = 50
    
    for i in range(0, len(all_points), batch_size):
        batch = all_points[i:i+batch_size]
        try:
            client.upsert(collection_name=COLLECTION_NAME, points=batch)
            print(f"   [SUCCESS] Uploaded: {min(i+batch_size, len(all_points))} / {len(all_points)}")
            time.sleep(0.5) 
        except Exception as e:
            print(f"   [ERROR] Batch upload failed: {e}")
            print("   [RETRY] Waiting 5 seconds before retrying...")
            time.sleep(5)
            try:
                client.upsert(collection_name=COLLECTION_NAME, points=batch)
                print(f"   [SUCCESS on RETRY] Uploaded: {min(i+batch_size, len(all_points))} / {len(all_points)}")
            except Exception as retry_e:
                print(f"   [FATAL] Failed again after retry: {retry_e}")

    print(f"\n[SUCCESS] All data successfully saved to Qdrant!")

if __name__ == "__main__":
    print("="*50)
    print("PDF Ingestion Script started")
    print("="*50)
    
    setup_collection()
    ingest_documents()
    
    print("\n[DONE] Process complete. You can now run the backend.")