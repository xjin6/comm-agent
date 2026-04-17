---
name: skill-apa-reference-list
description: Generate an APA 7th edition reference list from literature files in your-project/project-{name}/literature/. Use this skill whenever the user wants to format references, generate a bibliography, build a reference list, or asks about APA citations — even if they just say "format my references" or "what's in my literature folder". Supports PDFs, Word documents (.docx), plain text, BibTeX (.bib), and RIS (.ris) files.
---

# APA Reference List Generator

This skill reads all files in `your-project/project-{name}/literature/`, extracts citation metadata from each using up to three methods, picks the most reliable result, and formats a complete APA 7th edition reference list.

## Step 1 — Scan the literature folder

List all files in `your-project/project-{name}/literature/`. Group them by type:
- **Structured formats** (`.bib`, `.ris`) — skip to Step 3, parse fields directly (most reliable, no need for the three-method pipeline)
- **PDFs** — run the three-method pipeline below
- **Other documents** (`.docx`, `.txt`, `.md`) — read content and extract metadata directly (skip to Step 3)

If the folder is empty, tell the user and stop.

## Step 2 — Three-method metadata extraction (PDFs only)

For each PDF, run all three methods and then pick the best result.

---

### Method A — DOI lookup via CrossRef API

**Why it's reliable:** CrossRef is the authoritative registry for academic DOIs. If a DOI is found, the returned data is complete, structured, and verified by the publisher.

**How:**
1. Scan the first 2 pages of the PDF text for a DOI pattern: `10.\d{4,}/\S+`
2. If found, call the CrossRef REST API:
   ```
   GET https://api.crossref.org/works/{DOI}
   ```
3. Parse the JSON response. Key fields: `author` (array of `{family, given}`), `title`, `container-title` (journal), `volume`, `issue`, `page`, `published.date-parts`, `DOI`.

**Confidence: HIGH** — if CrossRef returns a full record, use it as the primary source. Mark as `[CrossRef]`.

---

### Method B — PDF DocInfo / XMP metadata

**Why it's useful:** Publisher-generated PDFs often embed structured metadata (title, author, DOI) in the file's header without needing to read the content.

**How:**
Run a Python script to extract embedded metadata:

```python
import fitz  # pymupdf — install with: pip install pymupdf
doc = fitz.open("file.pdf")
print(doc.metadata)   # DocInfo: title, author, subject, keywords, creator
xmp = doc.get_xml_metadata()  # XMP block if present
```

If `pymupdf` is not installed, try `pypdf`:
```python
from pypdf import PdfReader
r = PdfReader("file.pdf")
print(r.metadata)  # /Title, /Author, /Subject, /Keywords
```

If neither is installed, skip this method and note it in the flags.

**Confidence: MEDIUM** — publisher PDFs often have accurate title and author here, but fields like volume/issue/pages are rarely included. Use to supplement or confirm Method A/C.  Mark as `[DocInfo]`.

---

### Method C — PDF content reading

**Why it's needed:** Fallback when no DOI is found and DocInfo is empty or sparse. Reading the first 2 pages of the PDF text usually surfaces the full citation block that appears on the cover page of journal articles.

**How:** Use the Read tool on the PDF (limit to first 2–3 pages). Look for:
- Title (large heading at the top)
- Authors (line below title)
- Journal name, volume, issue, pages (usually in the header/footer or "To cite this article" block)
- DOI (if not already found in Step A)

**Confidence: MEDIUM-LOW** — accurate for well-formatted PDFs; may miss fields in scanned or non-standard layouts. Mark as `[Content]`.

---

### Picking the best result

After running all available methods, merge and rank:

| Priority | Rule |
|----------|------|
| 1st | If Method A (CrossRef) returned a full record → use it for all fields |
| 2nd | If CrossRef was partial or unavailable → fill gaps with DocInfo (Method B), then Content (Method C) |
| 3rd | If no DOI found → merge DocInfo + Content, prefer DocInfo for title/author, Content for volume/pages |

Flag any field that came from a lower-priority source as `[?]` so the user knows to verify.

---

## Step 3 — Extract metadata from structured files

**For `.bib` files** — map BibTeX fields: `author`, `year`/`date`, `title`, `journal`/`booktitle`, `volume`, `number` (→ issue), `pages`, `doi`, `url`, `publisher`, `editor`, `edition`.

**For `.ris` files** — map RIS tags: `AU`/`A1` (authors), `PY`/`Y1` (year), `TI`/`T1` (title), `JO`/`JF`/`T2` (journal/book), `VL` (volume), `IS` (issue), `SP`+`EP` (start/end pages), `DO` (DOI), `UR` (URL), `PB` (publisher), `ED` (editor).

**For `.docx` / `.txt` / `.md`** — read content and extract fields by pattern-matching the text.

**When metadata is incomplete** — infer what you can from the filename (e.g., `Smith_2019_cultivation.pdf` → author "Smith", year 2019). Mark uncertain fields with `[?]`.

---

## Step 4 — Format each reference in APA 7th edition

Apply the correct template based on source type:

**Journal article:**
> Author, A. A., & Author, B. B. (Year). Title of article. *Journal Name*, *Volume*(Issue), pages. https://doi.org/xxxxx

**Book:**
> Author, A. A. (Year). *Title of work: Capital letter also for subtitle* (Xth ed.). Publisher. https://doi.org/xxxxx

**Chapter in edited book:**
> Author, A. A. (Year). Title of chapter. In E. Editor & F. Editor (Eds.), *Title of book* (pp. xx–xx). Publisher.

**Website / online source:**
> Author, A. A. (Year, Month Day). Title of page. Site Name. URL

**Key APA 7th formatting rules:**
- Author format: `Last, F. M.` — use `&` before the final author (up to 20 authors listed; for 21+ use first 19, `...`, last author)
- Italicize: journal name + volume number (articles), full book title
- Title case for journals/books; sentence case for article/chapter titles
- DOI formatted as `https://doi.org/xxxxx` (not `doi:` prefix)
- No place of publication for books (dropped in APA 7th)
- If year is unknown, use `(n.d.)`; if author is unknown, move title to author position

---

## Step 5 — Output

Sort the final list **alphabetically by first author's last name** (or by title if no author). Number each entry for easy reference in conversation, but do NOT include numbers in the saved file.

**In the conversation:** Print the full reference list, numbered for readability.

**Save to file:** Write the unnumbered list to `your-project/project-{name}/output/apa_references.md`:

```markdown
# APA 7th Edition References

Generated: YYYY-MM-DD
Source folder: your-project/project-{name}/literature/
Total references: N

---

Author, A. A. (Year). Title...

Author, B. B. (Year). Title...
```

Tell the user the file path when done.

---

## Step 6 — Flag issues

After the list, report in a short section:
- Files where all three methods failed or returned sparse data
- References with missing critical fields (author, year, or title)
- Fields marked `[?]` that the user should verify
- Whether `pymupdf`/`pypdf` is installed (if not, Method B was skipped — suggest `pip install pymupdf`)
