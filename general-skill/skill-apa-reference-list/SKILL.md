---
name: skill-apa-reference-list
description: Generate an APA 7th edition reference list from literature files in your-project/literature/. Use this skill whenever the user wants to format references, generate a bibliography, build a reference list, or asks about APA citations — even if they just say "format my references" or "what's in my literature folder". Supports PDFs, Word documents (.docx), plain text, BibTeX (.bib), and RIS (.ris) files.
---

# APA Reference List Generator

This skill reads all files in `your-project/literature/`, extracts citation metadata from each, and formats a complete APA 7th edition reference list.

## Step 1 — Scan the literature folder

List all files in `your-project/literature/`. Group them by type:
- **Structured formats** (`.bib`, `.ris`) — parse fields directly
- **Documents** (`.pdf`, `.docx`, `.txt`, `.md`) — read and extract metadata from the content

If the folder is empty, tell the user and stop.

## Step 2 — Extract metadata from each file

For every file, extract as many of these fields as possible:

| Field | Notes |
|-------|-------|
| Authors | All authors. Last name, First initial format for APA |
| Year | Publication year |
| Title | Article/chapter/book title |
| Source | Journal name, book title, or website name |
| Volume / Issue | For journal articles |
| Pages | e.g., 45–67 |
| DOI | Preferred over URL when available |
| URL | Use only if no DOI |
| Publisher | For books |
| Editor(s) | For edited book chapters |
| Edition | For books |

**For `.bib` files** — map BibTeX fields: `author`, `year`/`date`, `title`, `journal`/`booktitle`, `volume`, `number` (→ issue), `pages`, `doi`, `url`, `publisher`, `editor`, `edition`.

**For `.ris` files** — map RIS tags: `AU`/`A1` (authors), `PY`/`Y1` (year), `TI`/`T1` (title), `JO`/`JF`/`T2` (journal/book), `VL` (volume), `IS` (issue), `SP`+`EP` (start/end pages), `DO` (DOI), `UR` (URL), `PB` (publisher), `ED` (editor).

**For PDFs and documents** — read the file content. Look for a title (often the first large heading or line), authors (typically below the title or at the end), and the journal/publication name (often in the header, footer, or abstract section). Academic PDFs usually contain the full citation details somewhere in the document.

**When metadata is incomplete** — make a reasonable inference if possible (e.g., a PDF filename like `Smith_2019_cultivation.pdf` suggests author "Smith" and year 2019). Note any uncertain fields with `[?]` so the user knows to verify.

## Step 3 — Format each reference in APA 7th edition

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

## Step 4 — Output

Sort the final list **alphabetically by first author's last name** (or by title if no author). Number each entry for easy reference in conversation, but do NOT include numbers in the saved file (APA reference lists are not numbered).

**In the conversation:** Print the full reference list with a header, numbered for readability.

**Save to file:** Write the unnumbered list to `your-project/output/apa_references.md` using this structure:

```markdown
# APA 7th Edition References

Generated: YYYY-MM-DD  
Source folder: your-project/literature/  
Total references: N

---

Author, A. A. (Year). Title...

Author, B. B. (Year). Title...
```

Tell the user the file path when done.

## Step 5 — Flag issues

After the list, report any problems in a short section:
- Files that could not be read
- References with missing critical fields (author, year, or title)
- Fields marked `[?]` that the user should verify
