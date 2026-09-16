# HireSense AI — Candidate Screening Demo

A real web page wired directly to your actual Module 1 (resume parser) and
Module 2 (roadmap generator) code, built for the HR-facing workflow: bulk
upload resumes, get a ranked shortlist, select or reject candidates, and
auto-generate a rejection message + personalized roadmap for anyone not
selected.

## How it works

1. **Bulk upload** — drop in multiple resumes (PDF or .txt) at once.
2. **Instant screening** — for every resume, the real Module 1 parser
   extracts their profile, a role is auto-detected from their resume
   text, and their skills are scored against that role. **This step
   makes zero AI calls** - it's pure parsing and matching, so it's
   instant no matter how many resumes you upload.
3. **Ranked table** — candidates appear sorted by match score. If the
   auto-detected role looks wrong for someone, just change it in the
   dropdown on their row - the score recalculates instantly (still no
   AI call).
4. **Select or Reject** — click "Select" to mark a candidate as chosen
   (no AI involved). Click "Reject" and **that's** the one moment the
   real Module 2 roadmap generator runs - it builds their personalized
   roadmap and a ready-to-send rejection message explaining why and
   what to improve.

This staged design (parsing/scoring first, AI only on reject) is
deliberate: it means uploading 10 or 20 resumes at once is always safe
and instant, and you only spend API calls on candidates HR is actually
about to send a message to - which also keeps you comfortably under
Gemini's free-tier rate limit even with a big batch.

## One-time setup

```powershell
pip install -r requirements.txt
```

## Setting your Gemini API key

**Temporary (current terminal session only):**
```powershell
$env:GEMINI_API_KEY="your_actual_key_here"
```

**Permanent (every new terminal):**
```powershell
setx GEMINI_API_KEY "your_actual_key_here"
```
(then close and reopen your terminal)

If no key is set, roadmap generation still works but returns the same
mock/template responses your other test scripts use when `MOCK_MODE` is
on - useful for testing the flow without spending API quota.

## Running it

```powershell
python app.py
```

Check the terminal - it tells you whether `MOCK_MODE` is ON or OFF. Make
sure it says OFF before your demo.

Then open:
```
http://127.0.0.1:5000
```

## Demo script for Saturday

1. Have 3-5 sample resumes ready (mix of strong and weak matches makes
   the ranking more convincing).
2. Upload them all at once - point out this happens instantly, no
   waiting, because no AI is involved yet.
3. Show the ranked table - point out the auto-detected role per
   candidate, and demonstrate overriding one role in the dropdown to
   show the score updates live.
4. Click "Select" on a strong candidate - instant, no AI call.
5. Click "Reject" on a weaker candidate - this is the one moment you'll
   see a short loading state while the real roadmap generates. Show the
   resulting roadmap and the ready-to-send rejection message.
6. If you want to reject a second candidate right after, that's fine -
   each reject is only ~4 API calls, well under the 15/minute free-tier
   limit unless you reject many candidates within the same minute.

## Known limitation worth mentioning if asked

Resumes with complex multi-column layouts can still occasionally have
minor text-ordering issues from PDF extraction - this is a general,
known limitation of plain-text PDF extraction, not specific to this
tool. Straightforward single- or simple two-column resumes parse
cleanly.

## Folder structure

```
frontend/
  app.py                     <- Flask server: bulk analyze, rescore,
                                 select, reject endpoints
  requirements.txt
  templates/index.html
  static/style.css
  static/script.js
  backend_modules/           <- your real Module 1 + Module 2 code,
                                 unchanged, plus demo-support files:
      target_jobs.py            (skill-gap scoring + role auto-detection)
      profile_adapter.py        (Module 1 profile -> Module 2 profile shape)
      fast_pipeline.py          (parallel prompt calls for speed)
      rejection_message.py      (turns a roadmap into a sendable message)
```

None of your original Module 1 or Module 2 files were modified beyond
the `section_splitter.py` fix (handles letter-spaced PDF headers) and
the skill-matching fix in `target_jobs.py` (handles merged/jumbled
skill text from multi-column PDFs) - both found and fixed from testing
against your real resume. Everything else is copied in as-is.
