import pdfplumber

pdf_path = "sample_resume.pdf"

with pdfplumber.open(pdf_path) as pdf:
    total_pages = len(pdf.pages)
    all_text = ""
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            all_text += text + "\n"

with open("resume_01.txt", "w", encoding="utf-8") as f:
    f.write(all_text)

char_count = len(all_text)
word_count = len(all_text.split())

print("Resume Loaded Successfully")
print(f"Pages: {total_pages}")
print(f"Characters Extracted: {char_count:,}")
print(f"Words Extracted: {word_count:,}")
print("Output Saved: resume_01.txt")