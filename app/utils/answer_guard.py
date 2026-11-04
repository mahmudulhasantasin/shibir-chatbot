# app/utils/answer_guard.py
"""
Extractive-answer guarantee:
  LLM যা return করুক, final answer অবশ্যই context-এর সাথে সামঞ্জস্যপূর্ণ/substring হতে হবে।
  না হলে None → caller raw paragraph fallback করবে।
"""
import re


def normalize(text: str) -> str:
    """সব বাড়তি স্পেস এবং নিউলাইনকে একটি স্পেসে রূপান্তর করে"""
    return re.sub(r"\s+", " ", text).strip()


def clean_for_match(text: str) -> str:
    """মার্কডাউন, পাংচুয়েশন এবং বাড়তি স্পেস বাদ দিয়ে শুধু শব্দগুলো আলাদা করে"""
    # মার্কডাউন রিমুভ (**, *, #, `)
    text = re.sub(r'[\*#`]', '', text)
    # শুধু বাংলা, ইংরেজি অক্ষর এবং সংখ্যা রাখা
    text = re.sub(r'[^\w\s\u0980-\u09FF]', ' ', text)
    return normalize(text).lower()


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


def apply_bold_highlights(s: str) -> str:
    """
    নির্দিষ্ট গুরুত্বপূর্ণ বিষয়গুলোকে **বোল্ড** মার্কডাউন ফরম্যাট করে
    """
    if not s:
        return s

    # নুকতাযুক্ত ডিকম্পোজড বর্ণকে স্ট্যান্ডার্ড ফর্মে আনা
    s = s.replace('\u09af\u09bc', 'য়').replace('\u09a1\u09bc', 'ড়').replace('\u09a2\u09bc', 'ঢ়')

    # ১. দফা (১ম দফা-, ২য় দফা, ৫ম দফা ইত্যাদি)
    s = re.sub(r'(?<!\*\*)([১-৯][০-৯]*(?:ম|য়|য়|র্থ|ষ্ঠ|তম)?\s*দফা[-–—:]?)\s*', r'**\1** ', s)

    # ২. ধারা (ধারা-১, ধারা-৪, ধারা ১২ ইত্যাদি)
    s = re.sub(r'(?<!\*\*)(ধারা[-–—\s]*[০-৯\d]+[:：]?)', r'**\1**', s)

    # ৩. সিকোয়েন্সিয়াল শব্দ
    seq_words = r'(?:প্রথমত|দ্বিতীয়ত|দ্বিতিয়ত|তৃতীয়ত|তৃতীয়ত|চতুর্থত|পঞ্চমত|ষষ্ঠত|সপ্তমত|অষ্টমত|নবমত|দশমত|প্রথমাংশে|দ্বিতীয়াংশে|দ্বিতীয়াংশে)'
    s = re.sub(r'(?<!\*\*)(?<![\w\u0980-\u09FF])(' + seq_words + r'[:：]?)', r'**\1**', s)

    # ৪. লেবেল ও কীওয়ার্ড
    labels = r'(?:প্রশ্ন|উত্তরঃ?|উত্তর|লক্ষ্য|উদ্দেশ্য|কর্তব্য|দায়িত্ব|দায়িত্ব|শর্তাবলী|শর্ত|বৈশিষ্ট্য|যোগ্যতা|বিঃদ্রঃ|উল্লেখ্য|মূল কথা হলো|মূল পয়েন্ট|সাবপয়েন্ট|যথা|সংজ্ঞা)'
    s = re.sub(r'(?<!\*\*)(?<![\w\u0980-\u09FF])(' + labels + r'[:：])', r'**\1**', s)

    # ৫. লাইনের শুরুতে নাম্বারিং (১. বা ১। বা ক. বা (ক) বা (১))
    s = re.sub(r'(?m)^(\s*)([০-৯\d]+[।\.])(?!\*)(\s*)', r'\1**\2**\3', s)
    s = re.sub(r'(?m)^(\s*)([ক-হ][।\.])(?!\*)(\s*)', r'\1**\2**\3', s)
    s = re.sub(r'(?m)^(\s*)(\([০-৯\dক-হ]+\))(?!\*)(\s*)', r'\1**\2**\3', s)

    # ৬. কমন ইংরেজি শব্দ
    s = re.sub(r'(?<![\*\w])(BCS|GPA[-–\s]*5|PDF|AI|Shibir)(?![\*\w])', r'**\1**', s)

    # ডুপ্লিকেট বোল্ড ফিক্স (**** -> **)
    s = re.sub(r'\*{4,}', '**', s)

    return s


def verify_extractive(answer: str, context: str) -> str | None:
    if not answer or not context:
        return None

    a = answer.strip()
    c = context.strip()

    def finalize(result: str) -> str:
        """Return result after stripping leading question line, formatting lines, and applying bold styling."""
        stripped = strip_question_heading(result)
        formatted = format_clean_lines(stripped)
        return apply_bold_highlights(formatted)

    # ১. পারফেক্ট সাবস্ট্রিং ম্যাচ (100% হুবহু)
    if a in c:
        return finalize(a)

    # ২. মার্কডাউন ও পাংচুয়েশন বাদ দিয়ে শব্দ-ভিত্তিক ম্যাচ
    clean_a = clean_for_match(a)
    clean_c = clean_for_match(c)

    if not clean_a:
        return None

    # যদি মার্কডাউন বাদ দেওয়ার পরও পুরো টেক্সট কন্টেক্সটে থাকে
    if clean_a in clean_c:
        return finalize(a)

    # ৩. শব্দের মিল (Word Overlap) - সবচেয়ে শক্তিশালী চেক
    # উত্তরের শব্দগুলো যদি ৮৫% এর বেশি কন্টেক্সটে থাকে, তবে সেটা সঠিক উত্তর
    a_words = set(clean_a.split())
    c_words = set(clean_c.split())

    if not a_words:
        return None

    overlap = a_words.intersection(c_words)
    overlap_ratio = len(overlap) / len(a_words)

    if overlap_ratio >= 0.85:
        return finalize(a)

    # ৪. লাইন-ভিত্তিক ম্যাচ (যদি ৮৫% শব্দ না মেলে, তবে লাইন ধরে চেক করি)
    a_lines = [line.strip() for line in a.split("\n") if len(line.strip()) > 8]
    if len(a_lines) > 1:
        norm_c = normalize(c)
        matched = sum(1 for line in a_lines if clean_for_match(line) in clean_c)
        if matched / len(a_lines) >= 0.70:
            return finalize(a)

    # ৫. কন্টেক্সটের ব্লক ধরে ওভারল্যাপ চেক (Fallback)
    best_block = None
    best_score = 0.0
    for block in c.split("\n\n"):
        block = block.strip()
        if len(block) < 20:
            continue
        clean_block = clean_for_match(block)
        b_words = set(clean_block.split())
        score = len(a_words & b_words) / max(len(a_words), 1)
        if score > best_score:
            best_score = score
            best_block = block

    if best_block and best_score >= 0.75:
        return finalize(best_block)

    print(f"[GUARD FAILED] Answer did not match context. Overlap: {overlap_ratio:.2f}")
    return None