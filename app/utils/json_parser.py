import json
import re

def extract_json(text: str) -> dict:
    """LLM-এর রেসপন্স থেকে JSON বের করার রোবাস্ট ফাংশন"""
    if not text:
        return {}
    
    # Markdown কোড ব্লক রিমুভ করা
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    
    try:
        # strict=False দেওয়া হলো যাতে নিউলাইন থাকলেও ক্র্যাশ না করে
        return json.loads(text, strict=False)
    except Exception:
        # যদি পুরো টেক্সট JSON না হয়, তবে { } এর ভেতরের অংশ বের করার চেষ্টা
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                return json.loads(match.group(0), strict=False)
            except Exception:
                pass
    return {}