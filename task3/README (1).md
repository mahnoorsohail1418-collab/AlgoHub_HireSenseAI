# Resume Text Extraction — extract_text.py

## What this script does
This script takes a PDF resume, opens it, reads through all the pages, and
pulls out all the text from it. Then it saves that text into a `.txt` file
so I can use it later for cleaning and section detection. It also prints
out a few quick stats at the end — how many pages it read, how many
characters it pulled out, and how many words.

This is my **Task 3** for the resume parsing project. I used the
`pdfplumber` library to do the extraction, since I tested it against two
other libraries (PyMuPDF and pdfminer.six) in Task 2, and pdfplumber gave
the cleanest, most accurately ordered text out of the three. That
comparison is in `Library_Comparison.pdf`.

## What you need before running it
- Python installed on your computer
- The `pdfplumber` library

If you don't have pdfplumber yet, install it by running this in cmd:
```
python -m pip install pdfplumber
```

## Where to put your files
Put `extract_text.py` and your resume PDF in the same folder. By default
the script looks for a file called `sample_resume.pdf` — so either rename
your PDF to that, or open the script and change the `pdf_path` line at the
top to whatever your file is actually named.

## How to run it
1. Open Command Prompt (cmd).
2. Go into the folder where your script and PDF are, for example:
   ```
   cd C:\Users\mahno\Documents\resume_parser_project
   ```
3. Run the script:
   ```
   python extract_text.py
   ```

## What it prints when it works
```
Resume Loaded Successfully
Pages: 2
Characters Extracted: 6,540
Words Extracted: 1,032
Output Saved: resume_01.txt
```

## Where the output goes
The extracted text gets saved into a file called `resume_01.txt`, in the
same folder as the script. You can open it with Notepad to see the raw
text that was pulled out of the resume — this is what the next steps
(cleaning the text, then finding sections like Education/Experience) will
be built on top of.

## Things I noticed / limitations
- If the PDF has more than one resume in it (like the sample file I used,
  which had 17 example resumes in one PDF), the script will pull text from
  **every single page**, not just one resume.
- If a resume is a scanned image or a photo instead of real selectable
  text, this script won't be able to read it — it would need OCR for that,
  which isn't part of this script yet.
- Resumes with fancy multi-column designs might come out with the text in
  a slightly different order than how it looks visually on the page.
