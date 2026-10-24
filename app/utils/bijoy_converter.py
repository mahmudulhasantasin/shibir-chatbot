# app/utils/bijoy_converter.py

import unicodeconverter as uc
import re

def convert_bijoy_to_unicode(text: str) -> str:
    if not text:
        return text
    
    lines = text.split('\n')
    converted_lines = []
    bijoy_triggers = set('‡†ƒŠ‰wxyz|[]_')
    
    for line in lines:
        if not line.strip():
            converted_lines.append(line)
            continue
        
        if any('\u0600' <= c <= '\u06FF' for c in line):
            converted_lines.append(line)
            continue
        
        trigger_count = sum(1 for c in line if c in bijoy_triggers)
        
        if trigger_count < 2:
            converted_lines.append(line)
        else:
            try:
                # ১. মূল কনভার্শন
                converted = uc.convert_bijoy_to_unicode(line)
                
                # ২. কিছু সাধারণ ভুল অটো-ফিক্স করা (Post-processing)
                converted = converted.replace("¯‥", "স্ক")
                converted = converted.replace("িি", "ি")
                converted = converted.replace("ে", "ে") # fix double e-kar
                converted = converted.replace("র্ী", "র্ী")
                converted = converted.replace("\u200b", "") # remove zero-width space
                
                # কিছু অদ্ভুত আর্টিফ্যাক্ট ফিক্স
                converted = converted.replace("পরিি", "পরি")
                converted = converted.replace("বিন্রম", "বিনম্র")
                
                converted_lines.append(converted)
            except Exception:
                converted_lines.append(line)
    
    return '\n'.join(converted_lines)