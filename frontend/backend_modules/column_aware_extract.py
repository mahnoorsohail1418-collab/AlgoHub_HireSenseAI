"""
column_aware_extract.py

Frontend demo support file - NOT part of the original Module 1/2 task list.

WHY THIS EXISTS:
Plain pdfplumber.extract_text() reads words in a rough top-to-bottom
order based on vertical position alone. On a single-column resume this
is fine. On a two-column resume (common in modern templates - a sidebar
of skills/contact info next to a main content column), it can pull text
from both columns out of order relative to each other - a skill list in
a left sidebar might get read before or after a section header it
doesn't actually belong to, because the header sits in a different
column at a similar height on the page.

This was found directly from testing real resumes for this project. One
resume's actual "SKILLS" heading and its technical skill list ended up
on opposite sides of a column split, so extract_text() emitted the skill
list BEFORE its own header - section_splitter.py then filed those
skills under whatever section was still open at that point, and the
real "skills" section came out empty.

HOW THIS FIXES IT:
Uses each word's actual (x, y) position on the page (from
page.extract_words()) instead of relying on naive reading order:
  1. Groups words into visual lines by their vertical position.
  2. For each line, checks whether there's one unusually large
     horizontal gap between words - much bigger than normal word
     spacing - which signals a column gutter rather than a pause
     between two words in the same sentence.
  3. Lines with that gap get split into a left segment and a right
     segment. Consecutive split lines are treated as one "column
     block": ALL of the left column's lines are emitted first (top to
     bottom), then all of the right column's lines - rather than
     alternating line by line, which is what scrambles a sidebar
     against a header at a similar height.
  4. Lines without a big gap (i.e. normal single-column lines, like
     the resume's name/contact block or a full-width paragraph) are
     emitted as-is, unchanged.

This is a heuristic, not a full layout engine - it won't perfectly
handle every possible resume design, but it directly fixes the real
column-order problem found in testing, without touching how single-
column resumes are read (which already worked correctly).
"""

LINE_TOLERANCE = 3.0          # points; words within this vertical distance are "the same line"
MIN_GUTTER_WIDTH = 40.0       # points; gaps smaller than this are just normal word spacing
GUTTER_RATIO = 3.0            # the gap must be at least this many times the line's median word-gap


def _group_into_lines(words: list) -> list:
    """Groups words with near-identical 'top' values into visual lines."""
    words = sorted(words, key=lambda w: (round(w["top"]), w["x0"]))
    lines = []
    current_line = []
    current_top = None

    for w in words:
        if current_top is None or abs(w["top"] - current_top) <= LINE_TOLERANCE:
            current_line.append(w)
            current_top = w["top"] if current_top is None else current_top
        else:
            lines.append(current_line)
            current_line = [w]
            current_top = w["top"]
    if current_line:
        lines.append(current_line)

    return lines


def _split_line_on_gutter(line_words: list):
    """
    Returns (left_words, right_words) if this line has a genuine column
    gutter, or (None, None) if it's a normal single-segment line.
    """
    if len(line_words) < 2:
        return None, None

    line_words = sorted(line_words, key=lambda w: w["x0"])
    gaps = [line_words[i + 1]["x0"] - line_words[i]["x1"] for i in range(len(line_words) - 1)]

    max_gap = max(gaps)
    max_idx = gaps.index(max_gap)
    other_gaps = gaps[:max_idx] + gaps[max_idx + 1:]
    median_other = sorted(other_gaps)[len(other_gaps) // 2] if other_gaps else 1.0

    is_gutter = max_gap >= MIN_GUTTER_WIDTH and max_gap >= GUTTER_RATIO * max(median_other, 1.0)
    if not is_gutter:
        return None, None

    return line_words[:max_idx + 1], line_words[max_idx + 1:]


CHIP_GAP_THRESHOLD = 8.0      # points; gaps this wide between words on the same line mean
                               # separate "chip" items (e.g. skill pills), not one phrase


def _line_text(words: list) -> str:
    """
    Joins words on a line back into text. Most resume templates render
    skills as individual visual "chips" (Python, C++, KNN, SVM...) with
    real padding around each one but no comma in the underlying text -
    extracted naively, "Python" and "C++" would run together as
    "Python C++" indistinguishable from an actual two-word phrase like
    "Machine Learning". Measured directly against real resumes: normal
    prose/phrase gaps between words are ~2-4pt; separate chip items are
    ~25-30pt apart - a wide, reliable margin. A gap above this threshold
    (but still well under a full column gutter) gets rendered as a comma
    instead of a plain space, so downstream skill-splitting (which
    already splits on commas) can tell separate skills apart correctly.
    """
    words = sorted(words, key=lambda w: w["x0"])
    parts = [words[0]["text"]]
    for prev, curr in zip(words, words[1:]):
        gap = curr["x0"] - prev["x1"]
        parts.append(", " if gap >= CHIP_GAP_THRESHOLD else " ")
        parts.append(curr["text"])
    return "".join(parts)


def extract_column_aware_text(pdf) -> str:
    """
    Takes an already-opened pdfplumber.PDF object and returns its text,
    reading column blocks left-to-right-then-top-to-bottom instead of
    naive line-by-line order.
    """
    all_lines_out = []

    for page in pdf.pages:
        words = page.extract_words()
        if not words:
            continue

        line_groups = _group_into_lines(words)

        left_buffer, right_buffer = [], []

        def flush():
            all_lines_out.extend(left_buffer)
            all_lines_out.extend(right_buffer)
            left_buffer.clear()
            right_buffer.clear()

        for line_words in line_groups:
            left, right = _split_line_on_gutter(line_words)
            if left is not None:
                left_buffer.append(_line_text(left))
                right_buffer.append(_line_text(right))
            else:
                flush()
                all_lines_out.append(_line_text(line_words))

        flush()

    return "\n".join(all_lines_out)
