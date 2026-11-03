# app/utils/answer_guard.py
"""
Extractive-answer guarantee:
  LLM যা return করুক, final answer অবশ্যই context-এর সাথে সামঞ্জস্যপূর্ণ/substring হতে হবে।
  না হলে None → caller raw paragraph fallback করবে।
"""
import re


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def verify_extractive(answer: str, context: str) -> str | None:
    if not answer or not context:
        return None

    a = answer.strip()
    c = context.strip()

    # 1. Perfect verbatim match
    if a in c:
        return a

    # 2. Normalized whitespace match (space/newline variation)
    norm_a = normalize(a)
    norm_c = normalize(c)
    if norm_a in norm_c:
        return a

    # 3. Multiline check: যদি answer-এর একাধিক পয়েন্ট/লাইনের অধিকাংশ context-এ থাকে
    a_lines = [line.strip() for line in a.split("\n") if len(line.strip()) > 8]
    if len(a_lines) > 1:
        matched = sum(1 for line in a_lines if normalize(line) in norm_c)
        if matched / len(a_lines) >= 0.70:
            return a

    # 4. Context block containment
    for block in c.split("\n\n"):
        block = block.strip()
        if block and (a in block or norm_a in normalize(block)):
            return a

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
        return a if best_score >= 0.85 else best

    return None
