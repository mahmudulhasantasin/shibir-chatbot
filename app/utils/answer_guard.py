# app/utils/answer_guard.py
"""
Extractive-answer guarantee:
  LLM যা return করুক, final answer অবশ্যই context-এর সাথে সামঞ্জস্যপূর্ণ/substring হতে হবে।
  না হলে None → caller raw paragraph fallback করবে।
"""
import re


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# Q-heading patterns: "৪।", "৪.", "৪)", "Q4.", "১২।" ইত্যাদি সহ পুরো প্রশ্নের লাইন
_Q_PREFIX = re.compile(
    r"^[\d০-৯]+[।.\)]\s*[^\n]{5,150}\?\s*\n?",
)


def strip_question_heading(text: str) -> str:
    """
    উত্তরের শুরুতে প্রশ্নের লাইন থাকলে (যেমন "৪। পাঁচ দফা কর্মসূচীর নাম কি?") সেটা বাদ দাও।
    """
    stripped = _Q_PREFIX.sub("", text.strip(), count=1).strip()
    return stripped if stripped else text.strip()


def format_clean_lines(s: str) -> str:
    """
    এক লাইনে লেগে থাকা দফা বা পয়েন্টগুলোকে আলাদা আলাদা লাইনে সুন্দরভাবে ফরম্যাট করে।
    যেমন: ১ম দফা... ২য় দফা... ৩য় দফা...
    """
    if not s:
        return s

    # ১. Ordinals like ১ম দফা, ২য় দফা, ৩য় দফা, ৪র্থ দফা, ৫ম দফা
    s = re.sub(r'(?<!\n)\s*([১-৯][০-৯]*(?:ম|য়|য়|র্থ|ষ্ঠ|তম)?\s*দফা[-–—\s])', r'\n\1', s)
    # ২. বাংলা সংখ্যা পয়েন্ট (১. ২. বা ১। ২।)
    s = re.sub(r'(?<!\n)\s+(?=[০-৯]+[।\.])', r'\n', s)
    # ৩. ইংরেজি সংখ্যা পয়েন্ট (1. 2. ইত্যাদি)
    s = re.sub(r'(?<!\n)\s+(?=\d+[।\.])', r'\n', s)
    # ৪. অতিরিক্ত লাইনব্রেক পরিষ্কার
    s = re.sub(r'\n{3,}', '\n\n', s)

    return s.strip()


def verify_extractive(answer: str, context: str) -> str | None:
    if not answer or not context:
        return None

    a = answer.strip()
    c = context.strip()

    def finalize(result: str) -> str:
        """Return result after stripping leading question line and formatting lines."""
        stripped = strip_question_heading(result)
        return format_clean_lines(stripped)

    # 1. Perfect verbatim match
    if a in c:
        return finalize(a)

    # 2. Normalized whitespace match (space/newline variation)
    norm_a = normalize(a)
    norm_c = normalize(c)
    if norm_a in norm_c:
        return finalize(a)

    # 3. Multiline check: যদি answer-এর একাধিক পয়েন্ট/লাইনের অধিকাংশ context-এ থাকে
    a_lines = [line.strip() for line in a.split("\n") if len(line.strip()) > 8]
    if len(a_lines) > 1:
        matched = sum(1 for line in a_lines if normalize(line) in norm_c)
        if matched / len(a_lines) >= 0.70:
            return finalize(a)

    # 4. Context block containment
    for block in c.split("\n\n"):
        block = block.strip()
        if block and (a in block or norm_a in normalize(block)):
            return finalize(a)

    # 5. Best overlapping block (Jaccard >= 0.70)
    a_words = set(norm_a.split())
    if not a_words:
        return None

    best, best_score = None, 0.0
    for block in c.split("\n\n"):
        block = block.strip()
        if len(block) < 20:
            continue
        bw = set(normalize(block).split())
        score = len(a_words & bw) / max(len(a_words), 1)
        if score > best_score:
            best_score, best = score, block

    if best and best_score >= 0.70:
        result = a if best_score >= 0.85 else best
        return finalize(result)

    return None
