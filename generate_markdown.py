import os
import sys
import re
import fitz
import unicodeconverter as uc

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

from app.utils.bijoy_converter import clean_unicode_artifacts

def is_bijoy_font(fontname):
    fn = fontname.lower()
    return 'bijoy' in fn or 'sutonny' in fn

# Specific word & phrase fixes for common Bijoy / DTP font anomalies
DIRECT_REPLACEMENTS = {
    'æ': 'ু',
    'š¿': 'ন্ত্র',
    'š': 'ন্ত',
    'Í': 'ন্ত',
    '¿': '?',
    '¡': '্ব',
    '¥': 'ম্ম',
    '¦': '্ব',
    'Ð': 'ণ্ড',
    '\U00100099': '•',
    '‘': '‘',
    '’': '’',
    '“': '“',
    '”': '”',
    'Ñ': '-',
    
    # Common broken ligatures
    'সুসম্পনড়ব': 'সুসম্পন্ন',
    'সম্পনড়ব': 'সম্পন্ন',
    'অক্ষুনড়ব': 'অক্ষুণ্ণ',
    'বিভিনড়ব': 'বিভিন্ন',
    'ছিনড়ব': 'ছিন্ন',
    'অবিচ্ছিনড়ব': 'অবিচ্ছিন্ন',
    'প্রশড়ব': 'প্রশ্ন',
    'উনড়বত': 'উন্নত',
    'উনড়বতি': 'উন্নতি',
    'স্বাস্থ্যোনড়বতি': 'স্বাস্থ্যোন্নতি',
    'নিমড়বমানের': 'নিম্নমানের',
    'প্রতিপনড়ব': 'প্রতিপন্ন',
    'সুনড়বাহ': 'সুন্নাহ',
    'জাহানড়বাম': 'জাহান্নাম',
    'জানড়বাত': 'জান্নাত',
    'মারাতড়বক': 'মারাত্মক',
    'আতড়ব': 'আত্ম',
    'সংক্রাড়': 'সংক্রান্ত',
    'সিদ্ধাড়': 'সিদ্ধান্ত',
    'চক্রাড়': 'চক্রান্ত',
    'অত্যড়': 'অত্যন্ত',
    'পর্যড়': 'পর্যন্ত',
    'চূড়াড়': 'চূড়ান্ত',
    'জীবড়': 'জীবন্ত',
    'প্রাণবড়': 'প্রাণবন্ত',
    'অনড়': 'অনন্ত',
    'জ্বলন্ড': 'জ্বলন্ত',
    'চিরল্ডন': 'চিরন্তন',
    'সড়ন': 'সন্তান',
    'সাড়না': 'সান্ত্বনা',
    'আলাহ': 'আল্লাহ',
    'আলণ্টাহ': 'আল্লাহ',
    'আলণ্ডাহ': 'আল্লাহ',
    'আল-াহ': 'আল্লাহ',
    'আলাহর': 'আল্লাহর',
    'আলণ্টাহর': 'আল্লাহর',
    'আল-াহর': 'আল্লাহর',
    'রাসূলুলাহ': 'রাসূলুল্লাহ',
    'আব্দুলাহ': 'আব্দুল্লাহ',
    'উলিখিত': 'উল্লিখিত',
    'উলেখ': 'উল্লেখ',
    'উলেখ্য': 'উল্লেখ্য',
    'সংরনাণ': 'সংরক্ষণ',
    'প্রশিণাণ': 'প্রশিক্ষণ',
    'নড়ব': 'ন্ন',
    'ব¯ু‘': 'বস্তু',
    'সং¯‥ৃতি': 'সংস্কৃতি',
    'সং¯পর্শে': 'সংস্পর্শে',
    '¯ড়বাতকোত্তর': 'স্নাতকোত্তর',
    'সহ¯্রাধিক': 'সহস্রাধিক',
    '¯্রষ্টা': 'স্রষ্টা',
    'ে¯্লাগান': 'স্লোগান',
    'ধর্মপšী’': 'ধর্মপন্থী',
    'অšর্Íদৃষ্টি': 'অন্তর্দৃষ্টি',
    'স¤পর্কে': 'সম্পর্কে',
    'স¤প্রসারিত': 'সম্প্রসারিত',
    'স¤প্রদায়': 'সম্প্রদায়',
    'স¤প্রদায়ের': 'সম্প্রদায়ের',
    'স¤্রাট': 'সম্রাট',
    'আ¤্রকাননে': 'আম্রকাননে',
    'সম¥েলন': 'সম্মেলন',
    'সূক্ষè': 'সূক্ষ্ম',
    'তীক্ষè': 'তীক্ষ্ণ',
    'উল¬েখ': 'উল্লেখ',
    'উল¬েখ্য': 'উল্লেখ্য',
    'প্ল¬েটো': 'প্লেটো',
    'ন¤িড়বরূপ': 'নিম্নরূপ',
    'পািÐত্যের': 'পাণ্ডিত্য',
    'আহŸান': 'আহ্বান',
    'আহŸানে': 'আহ্বানে',
    'রিন্নাহ': 'জিন্নাহ',
    'কংগে্রস': 'কংগ্রেস',
    'ডিগি্র': 'ডিগ্রি',
    'পে্রসিডেন্ট': 'প্রেসিডেন্ট',
    'শে্রষ্ঠত্ব': 'শ্রেষ্ঠত্ব',
    'শে্রণীবিন্যাস': 'শ্রেণীবিন্যাস',
    'ব¯ু': 'বস্তু',
    'কতর্ৃক': 'কর্তৃক',
    'প্র্রাথনা': 'প্রার্থনা',
    'পর্রামশ': 'পরামর্শ',
    'শামসুন্নাহামসুন্নাহারর সাথে': 'শামসুন্নাহারের সাথে',
    'শামসুন্নাহামসুন্নাহার': 'শামসুন্নাহার',
    'শামসুন্নাহারামসুন্নাহার': 'শামসুন্নাহার',
    'স্নাতকসম্পন্নকরেন': 'স্নাতক সম্পন্ন করেন',
    'অধ্যক্ষহিসেবে': 'অধ্যক্ষ হিসেবে',
    'নাজিল করেন।ন।': 'নাজিল করেন।',
    'করেন।ন।': 'করেন।',
    'হয়।।': 'হয়।',
}

def fix_misplaced_ref(text):
    # Pattern: র্ followed by consonant and kar: র্([ক-হ])([ািীুূৃেৈোৌ])
    # Bijoy typing order artifact: e.g. র্নিযাতন -> নির্যাতন, র্পূণভাবে -> পূর্ণভাবে, র্দীঘদিন -> দীর্ঘদিন
    return re.sub(r'র্([ক-হড়ঢ়য়])([ািীুূৃেৈোৌ])', r'\1\2র্', text)

def clean_duplicated_words(text):
    def fix_word(m):
        w = m.group(0)
        for k in range(len(w) // 2, 0, -1):
            suf = w[-k:]
            pref = w[:-k]
            if pref.endswith(suf):
                return pref
        return w
    return re.sub(r'[\u0980-\u09FF]+', fix_word, text)

def clean_tokens(line):
    tokens = line.split()
    if not tokens:
        return line
    i = 0
    new_tokens = []
    punct = '।,;:!?()\"\'[]{}'
    while i < len(tokens):
        curr = tokens[i]
        
        # Check two-word phrase repeat first
        if i + 3 < len(tokens):
            phrase1 = curr + ' ' + tokens[i+1]
            phrase2 = tokens[i+2] + ' ' + tokens[i+3]
            p1_clean = phrase1.strip(punct)
            p2_clean = phrase2.strip(punct)
            if p1_clean.endswith(p2_clean) or p1_clean.replace('য', 'য়').endswith(p2_clean.replace('য', 'য়')):
                new_tokens.append(curr)
                new_tokens.append(tokens[i+1])
                i += 4
                continue

        # Check single-token repeat / suffix repeat
        if i + 1 < len(tokens):
            nxt = tokens[i+1]
            c_clean = curr.strip(punct)
            n_clean = nxt.strip(punct)
            
            # Exact duplicate word
            if c_clean == n_clean and len(c_clean) >= 2:
                new_tokens.append(curr)
                i += 2
                continue
            
            # nxt is suffix of c_clean
            if n_clean and (c_clean.endswith(n_clean) or c_clean.replace('য', 'য়').endswith(n_clean.replace('য', 'য়'))):
                new_tokens.append(curr)
                i += 2
                continue

            # c_clean starts with n_clean (e.g. 'সহায়িকায সহায়িকা', 'শাখান শাখা', 'সমাধানযার সমাধান')
            if len(n_clean) >= 3 and c_clean.startswith(n_clean):
                new_tokens.append(nxt)
                i += 2
                continue

        new_tokens.append(curr)
        i += 1
    return ' '.join(new_tokens)

def clean_line_text(line):
    if not line.strip():
        return ''
    line = clean_unicode_artifacts(line)
    for k, v in DIRECT_REPLACEMENTS.items():
        if k in line:
            line = line.replace(k, v)
    line = fix_misplaced_ref(line)
    line = clean_duplicated_words(line)
    line = clean_tokens(line)
    # clean multiple punctuations
    line = re.sub(r'।\s*।+', '।', line)
    line = re.sub(r'([।?!])\1+', r'\1', line)
    line = re.sub(r'\s+', ' ', line).strip()
    return line

def format_markdown_headings(lines, page_num):
    """Adds markdown structure (headings, lists, blockquotes)"""
    formatted = []
    
    for line in lines:
        if not line.strip():
            continue
            
        # Detect Question lines like: '১। এই বই এর ভূমিকায়...', 'ধারা-৬: ...'
        if re.match(r'^[০-৯0-9]+[।|]\s*', line) or re.match(r'^ধারা-[০-৯0-9]+', line):
            formatted.append(f"\n**{line}**\n")
        # Detect Book Titles like: '১. কর্মপদ্ধতি', '২. সংবিধান'
        elif re.match(r'^[০-৯0-9]+\.\s+[^\d]', line) and len(line) < 60 and ('লেখক' in lines[min(lines.index(line)+1, len(lines)-1)] if line in lines else False):
            formatted.append(f"\n### {line}\n")
        # Detect Major Sections
        elif line in ['বইসমুহ', 'উলুমুল কুরআন', 'উলুমুল হাদীস', 'ইলমুত তাজবীদ', 'মাসয়ালা-মাসায়েল', 'মাসনূন দুয়া', 'শানে নুযুল', 'কতিপয় মনীষীর সংক্ষিপ্ত জীবনী', 'দিবস সমূহ ও যুদ্ধের ঘটনা সমূহ', 'বিবিধ']:
            formatted.append(f"\n# {line}\n")
        # Detect Person Name in biography section (only if short and no digits/dates)
        elif len(line) < 45 and not any(c.isdigit() for c in line) and ('রহঃ' in line or 'রাহিঃ' in line or line.startswith('শহীদ ')):
            formatted.append(f"\n## {line}\n")
        # Detect Subheadings
        elif line in ['ব্যক্তিগত জীবন', 'রাজনৈতিক জীবন', 'কর্মজীবন', 'রচনাবলী', 'সংবিধান কি?', 'সংবিধান শব্দের অর্থ :', 'সংজ্ঞা :', 'সংবিধানের উপাদান :', 'সংবিধানের প্রকারভেদ :', 'সংবিধানের শে্রণীবিন্যাস :']:
            formatted.append(f"\n#### {line}\n")
        # Bullet lines
        elif line.startswith('* ') or line.startswith('• '):
            formatted.append(f"- {line[2:]}")
        else:
            formatted.append(line)
            
    return '\n'.join(formatted)

def extract_page_markdown(page, page_num):
    blocks = page.get_text('dict')['blocks']
    
    # Check if this page has two columns
    left_count = 0
    right_count = 0
    for b in blocks:
        if 'lines' in b:
            for l in b['lines']:
                for s in l['spans']:
                    if s['text'].strip():
                        if s['bbox'][0] < 280 and s['bbox'][2] < 310:
                            left_count += 1
                        elif s['bbox'][0] > 290:
                            right_count += 1
    has_two_cols = (left_count > 15 and right_count > 15)

    block_items = []
    for bi, b in enumerate(blocks):
        if 'lines' not in b:
            continue
        bbox = b['bbox']
        # Footer page number check (y > 805)
        if bbox[1] > 805:
            continue
        
        if not has_two_cols:
            col_id = 0
        else:
            if bbox[3] < 85: # Header
                col_id = 0
            elif bbox[0] < 300 and bbox[2] <= 310:
                col_id = 1 # Left column
            elif bbox[0] >= 300:
                col_id = 2 # Right column
            else:
                col_id = 0
        block_items.append((col_id, bbox[1], bbox[0], b))
        
    block_items.sort(key=lambda x: (x[0], x[1], x[2]))
    
    page_lines = []
    for col_id, by, bx, b in block_items:
        b_spans = []
        for l in b['lines']:
            for s in l['spans']:
                raw_txt = s['text']
                if not raw_txt:
                    continue
                font = s['font']
                txt = raw_txt
                
                # Check original spacing
                had_lead_space = raw_txt.startswith(' ')
                had_trail_space = raw_txt.endswith(' ')
                
                if txt.strip() == 'μ':
                    txt = 'ক্র'
                elif txt.strip() == '¶':
                    txt = 'র্য'
                elif is_bijoy_font(font):
                    clean_txt = txt.strip()
                    if clean_txt.endswith('‡') or clean_txt.endswith('†'):
                        clean_txt = clean_txt[:-1]
                    try:
                        if clean_txt:
                            txt = uc.convert_bijoy_to_unicode(clean_txt)
                        else:
                            txt = ''
                    except Exception:
                        words = clean_txt.split(' ')
                        conv_words = []
                        for w in words:
                            try:
                                conv_words.append(uc.convert_bijoy_to_unicode(w))
                            except Exception:
                                conv_words.append(w)
                        txt = ' '.join(conv_words)
                        
                    if had_lead_space and not txt.startswith(' '):
                        txt = ' ' + txt
                    if had_trail_space and not txt.endswith(' '):
                        txt = txt + ' '
                        
                b_spans.append((s['bbox'][1], s['bbox'][0], s['bbox'][3], s['bbox'][2], txt))
        
        if not b_spans:
            continue
            
        b_spans.sort(key=lambda s: (s[0], s[1]))
        lines_grouped = []
        curr_line = []
        curr_y = None
        
        for s in b_spans:
            sy0, sx0, sy1, sx1, stxt = s
            if curr_y is None:
                curr_y = sy0
                curr_line.append(s)
            elif abs(sy0 - curr_y) <= 3.5:
                curr_line.append(s)
            else:
                lines_grouped.append(curr_line)
                curr_line = [s]
                curr_y = sy0
        if curr_line:
            lines_grouped.append(curr_line)
            
        bengali_kars = set('ািীুূৃেৈোৌ্ঁংঃ')
        for line_spans in lines_grouped:
            line_spans.sort(key=lambda s: s[1])
            line_str = ''
            for idx, sp in enumerate(line_spans):
                sp_txt = sp[4]
                if idx > 0:
                    prev_x1 = line_spans[idx-1][3]
                    curr_x0 = sp[1]
                    gap = curr_x0 - prev_x1
                    
                    need_space = True
                    if not line_str or not sp_txt:
                        need_space = False
                    elif line_str.endswith(' ') or sp_txt.startswith(' '):
                        need_space = False
                    elif sp_txt[0] in bengali_kars:
                        need_space = False
                    elif line_str.endswith('্'):
                        need_space = False
                    elif (line_str.endswith('এইচআরড') and sp_txt.startswith('ি')) or \
                         (line_str.endswith('ছাত্রশি') and sp_txt.startswith('বির')) or \
                         (line_str.endswith('আয়া') and sp_txt.startswith('ত')) or \
                         (line_str.endswith('ঈমা') and sp_txt.startswith('ন')) or \
                         (line_str.endswith('য') and sp_txt.startswith('ারা')) or \
                         (line_str.endswith('সূরা আ') and sp_txt.startswith('ল')):
                        need_space = False
                    elif gap < 4.0:
                        need_space = False
                        
                    if need_space:
                        line_str += ' '
                line_str += sp_txt
            
            cleaned = clean_line_text(line_str)
            if cleaned:
                page_lines.append(cleaned)
                
    return format_markdown_headings(page_lines, page_num)

def convert_pdf_to_md():
    pdf_path = os.path.join(base_dir, "documents", "সদস্য সহায়িকা.pdf")
    output_docs_path = os.path.join(base_dir, "documents", "সদস্য সহায়িকা.md")
    output_cleaned_path = os.path.join(base_dir, "cleaned_texts", "সদস্য সহায়িকা.md")
    output_fully_cleaned_path = os.path.join(base_dir, "fully_cleaned_texts", "সদস্য সহায়িকা.md")
    
    print(f"[INFO] Opening {pdf_path}...")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"[INFO] Total pages: {total_pages}")
    
    full_markdown = []
    
    for page_num in range(1, total_pages + 1):
        page = doc[page_num - 1]
        page_md = extract_page_markdown(page, page_num)
        
        full_markdown.append(f"\n\n--- Page {page_num} ---\n\n{page_md}")
        if page_num % 10 == 0 or page_num == total_pages:
            print(f"[INFO] Processed page {page_num}/{total_pages}...")
            
    doc.close()
    
    final_text = "".join(full_markdown).strip()
    
    # Save to documents/
    with open(output_docs_path, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"[SUCCESS] Saved: {output_docs_path}")
    
    # Also update cleaned_texts/ and fully_cleaned_texts/
    os.makedirs(os.path.dirname(output_cleaned_path), exist_ok=True)
    with open(output_cleaned_path, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"[SUCCESS] Updated: {output_cleaned_path}")
    
    os.makedirs(os.path.dirname(output_fully_cleaned_path), exist_ok=True)
    with open(output_fully_cleaned_path, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"[SUCCESS] Updated: {output_fully_cleaned_path}")

if __name__ == "__main__":
    convert_pdf_to_md()
