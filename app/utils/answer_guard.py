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


def apply_bold_highlights(s: str) -> str:
    """
    নির্দিষ্ট গুরুত্বপূর্ণ বিষয়গুলোকে **বোল্ড** মার্কডাউন ফরম্যাট করে:
    ১. সিকোয়েন্সিয়াল শব্দ (প্রথমত:, দ্বিতীয়ত:, প্রথমাংশে: ইত্যাদি)
    ২. ধারা বা আর্টিকেল নম্বর (ধারা-১, ধারা-৪ ইত্যাদি)
    ৩. দফা বা ফেজ (১ম দফা-, ২য় দফা ইত্যাদি)
    ৪. নাম্বারিং ও বুলেট (১. / ২. / ১। / ২। / ক. / (ক) ইত্যাদি)
    ৫. কি-ওয়ার্ড বা লেবেল (প্রশ্ন:, উত্তর:, লক্ষ্য:, উদ্দেশ্য:, ইত্যাদি)
    ৬. গুরুত্বপূর্ণ ইংরেজি শব্দ বা সংক্ষিপ্ত রূপ (BCS, GPA-5, PDF, AI, Shibir)
    """
    if not s:
        return s

    # নুকতাযুক্ত ডিকম্পোজড বর্ণকে স্ট্যান্ডার্ড ফর্মে আনা
    s = s.replace('\u09af\u09bc', 'য়').replace('\u09a1\u09bc', 'ড়').replace('\u09a2\u09bc', 'ঢ়')

    # ১. দফা (১ম দফা-, ২য় দফা, ৫ম দফা ইত্যাদি)
    s = re.sub(r'(?<!\*\*)([১-৯][০-৯]*(?:ম|য়|য়|র্থ|ষ্ঠ|তম)?\s*দফা[-–—:]?)\s*', r'**\1** ', s)

    # ২. ধারা (ধারা-১, ধারা-৪, ধারা ১২ ইত্যাদি)
    s = re.sub(r'(?<!\*\*)(ধারা[-–—\s]*[০-৯\d]+[:：]?)', r'**\1**', s)

    # ৩. সিকোয়েন্সিয়াল শব্দ (প্রথমত:, দ্বিতীয়ত:, প্রথমাংশে: ইত্যাদি)
    seq_words = r'(?:প্রথমত|দ্বিতীয়ত|দ্বিতিয়ত|তৃতীয়ত|তৃতীয়ত|চতুর্থত|পঞ্চমত|ষষ্ঠত|সপ্তমত|অষ্টমত|নবমত|দশমত|প্রথমাংশে|দ্বিতীয়াংশে|দ্বিতীয়াংশে)'
    s = re.sub(r'(?<!\*\*)(?<![\w\u0980-\u09FF])(' + seq_words + r'[:：]?)', r'**\1**', s)

    # ৪. লেবেল ও কীওয়ার্ড (প্রশ্ন:, উত্তর:, লক্ষ্য:, উদ্দেশ্য:, ইত্যাদি)
    labels = r'(?:প্রশ্ন|উত্তরঃ?|উত্তর|লক্ষ্য|উদ্দেশ্য|কর্তব্য|দায়িত্ব|দায়িত্ব|শর্তাবলী|শর্ত|বৈশিষ্ট্য|যোগ্যতা|বিঃদ্রঃ|উল্লেখ্য|মূল কথা হলো|মূল পয়েন্ট|সাবপয়েন্ট|যথা|সংজ্ঞা)'
    s = re.sub(r'(?<!\*\*)(?<![\w\u0980-\u09FF])(' + labels + r'[:：])', r'**\1**', s)

    # ৫. লাইনের শুরুতে নাম্বারিং (১. বা ১। বা ক. বা (ক) বা (১))
    s = re.sub(r'(?m)^(\s*)([০-৯\d]+[।\.])(?!\*)(\s*)', r'\1**\2**\3', s)
    s = re.sub(r'(?m)^(\s*)([ক-হ][।\.])(?!\*)(\s*)', r'\1**\2**\3', s)
    s = re.sub(r'(?m)^(\s*)(\([০-৯\dক-হ]+\))(?!\*)(\s*)', r'\1**\2**\3', s)

    # ৬. কমন ইংরেজি শব্দ/সংক্ষিপ্ত রূপ (BCS, GPA-5, PDF, AI, Shibir)
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
