import re


def clean_text(raw_text):
    """
    Takes raw extracted resume text and cleans it up:
    - removes extra blank lines
    - collapses multiple spaces into one
    - removes unwanted symbols
    - normalizes line breaks
    - keeps the text still readable (doesn't merge separate lines together)
    """
    # Normalize different line break styles (Windows \r\n, old Mac \r) into \n
    text = raw_text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove common unwanted symbols that show up from PDF extraction
    # (keeps normal punctuation like . , - / | @ : and letters/numbers)
    text = re.sub(r'[^\w\s.,\-\/|@:()&%+#\'"]', '', text)

    # Collapse multiple spaces/tabs into a single space (but not newlines)
    text = re.sub(r'[ \t]+', ' ', text)

    # Remove trailing spaces at the end of each line
    lines = [line.strip() for line in text.split('\n')]

    # Remove blank lines (this also collapses multiple blank lines into none)
    cleaned_lines = [line for line in lines if line != '']

    # Join everything back with single newlines between each real line
    cleaned_text = '\n'.join(cleaned_lines)

    return cleaned_text


if __name__ == "__main__":
    input_file = "resume_01.txt"
    output_file = "resume_01_cleaned.txt"

    with open(input_file, "r", encoding="utf-8") as f:
        raw_text = f.read()

    cleaned = clean_text(raw_text)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(cleaned)

    print("Text Cleaned Successfully")
    print(f"Original Characters: {len(raw_text):,}")
    print(f"Cleaned Characters: {len(cleaned):,}")
    print(f"Output Saved: {output_file}")
