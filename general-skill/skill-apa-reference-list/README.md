# APA Reference List Generator

> **v0.1.0** · Updated 2026-03-31 · `utility`

Reads all literature files in `your-project/project-{name}/literature/`, extracts citation metadata using a three-method pipeline, and outputs a complete APA 7th edition reference list.

## Features

- **Multi-format support** — PDF, Word (.docx), plain text, BibTeX (.bib), RIS (.ris)
- **Three-method metadata extraction** for PDFs:
  1. DOI → CrossRef API lookup (most reliable)
  2. PDF DocInfo/XMP metadata via pymupdf
  3. PDF content reading and parsing
- **Smart merging** — picks the most complete and reliable result per field across all three methods
- **APA 7th edition** formatting for journal articles, books, book chapters, conference papers, and more

## Output

Results saved to `your-project/project-{name}/output/`:

| File | Description |
|------|-------------|
| `apa_references.md` | Full APA 7th edition reference list in Markdown |

## Quick Start

1. Drop your literature files into `your-project/project-{name}/literature/`:
   ```
   your-project/project-{name}/literature/
   ├── paper1.pdf
   ├── paper2.pdf
   ├── references.bib
   └── export.ris
   ```

2. Tell the agent: *"Generate my APA reference list"*

## How It Works

For each PDF, three methods run in parallel:

| Method | Source | Reliability |
|--------|--------|-------------|
| DOI → CrossRef | Publisher registry | Highest — complete, verified |
| PDF metadata | DocInfo/XMP embedded | Medium — depends on publisher |
| PDF content | Text parsing | Fallback — heuristic |

Results are merged field-by-field, preferring CrossRef → metadata → content in that order.

BibTeX and RIS files are parsed directly — no extraction needed.

## Author

**Xin Jin** (@xjin6) · xjin6@outlook.com

## License

CC BY-NC-ND 4.0
