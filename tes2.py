import os
import re

base_dir = os.path.dirname(os.path.abspath(__file__))

def advanced_clean_text(text: str) -> str:
    if not text:
        return text

    # ১. কমন ডুপ্লিকেট শব্দ ফিক্স (যেমন: বাংলাদেশংলাদেশ -> বাংলাদেশ, বিষয়সমুহষয়সমুহ -> বিষয়সমূহ)
    # একই শব্দের পুনরাবৃত্তি রোধ করা
    text = re.sub(r'(\b[\u0980-\u09FF]{3,})\1+', r'\1', text)

    # ২. অতিরিক্ত ডুপ্লিকেট দাড়ি (。。), কমা (、、), বা বিরামচিহ্ন ফিক্স
    text = re.sub(r'।\s*।', '।', text)
    text = re.sub(r',{2,}', ',', text)
    text = re.sub(r'\.{2,}', '.', text)

    # ৩. বিজয়ের গার্বেজ প্যাটার্ন বা এনকোডিং মিসম্যাচ রিমুভ (যেমন: Kg©c×wZ, m~iv evKviv ইত্যাদি)
    # যেসব লাইনে অপ্রয়োজনীয় টিল্ড (~) বা অদ্ভুত ইংরেজি ক্যারেক্টার এবং বিজয় কোড মিশে আছে সেগুলোকে ক্লিন করা
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # যদি লাইনে অতিরিক্ত অদ্ভুত গার্বেজ ট্রিগার থাকে যা বাংলার সাথে যায় না
        if re.search(r'[~#\$%\^&\*\(\)_+={}\[\]|\\:;<>\?]/{2,}', line):
            continue
            
        # ভাঙা শব্দ বা কমন বিজয়ের শব্দ ম্যাপিং ফিক্স
        line = line.replace("Kg©c×wZ", "কর্মপদ্ধতি")
        line = line.replace("m~iv", "সূরা")
        line = line.replace("evKviv", "বাকারা")
        line = line.replace("AvqvZ", "আয়াত")
        line = line.replace("dwRjZ", "ফজিলত")
        line = line.replace("bvgKiY", "নামকরণ")
        line = line.replace("wji", "হলো")
        
        # ডুপ্লিকেট কার ফিক্স (যেমন: কালেকশনে জোড়া লেগে যাওয়া কার)
        line = re.sub(r'িি', 'ি', line)
        line = re.sub(r'ুু', 'ু', line)
        line = re.sub(r'াা', 'া', line)
        
        # অতিরিক্ত স্পেস রিমুভ করা
        line = re.sub(r'[ \t]+', ' ', line).strip()
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

def clean_markdown_files():
    input_dir = os.path.join(base_dir, "cleaned_texts") # অথবা আপনার যে ফোল্ডারে ফাইল আছে
    output_dir = os.path.join(base_dir, "fully_cleaned_texts")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(input_dir):
        print(f"[ERROR] ফোল্ডার পাওয়া যায়নি: {input_dir}. আগে টেক্সট এক্সট্রাক্ট করে নিন।")
        return

    files = [f for f in os.listdir(input_dir) if f.endswith('.md')]
    
    if not files:
        print(f"[WARNING] কোনো .md ফাইল পাওয়া যায়নি: {input_dir}")
        return

    for filename in files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        print(f"[INFO] ক্লিন করা হচ্ছে: {filename}...")
        
        with open(input_path, "r", encoding="utf-8") as f:
            raw_content = f.read()
            
        # ক্লিনিং ফাংশন চালানো
        cleaned_content = advanced_clean_text(raw_content)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_content)
            
        print(f"[SUCCESS] সেভ হয়েছে: {output_path}")

if __name__ == "__main__":
    clean_markdown_files()