# Test of the splitter on noisy PDF text (P2, week 2)

## What was tested
The splitter written for the clean French text was run on **text coming from a scanned PDF**: the official Journal officiel n°17 of 25/04/1990 (`loi_90_11_1990.pdf`, 16 pages). **That file is the ARABIC edition** (two columns), so this test also checks Arabic.

Pipeline: `ocr_pdf.py` (PyMuPDF renders each page at 250 dpi, each page is cut in two columns, right column first, Tesseract with the Arabic model reads each half; 16 pages in about 30 seconds) -> `data/raw/loi_90_11_ar_ocr.txt` -> `splitter.py --lang ar`.

## Results
| mode | articles found (target 158) |
|---|---|
| strict (rule of week 1: accept only the next expected number) | **11** |
| tolerant (`--max-gap 3`: accept a number up to 3 ahead, report what was skipped) | **136** (86%) |

Missing (22): 12, 16, 25, 28, 30, 31, 35, 65, 69, 75, 84, 86, 88, 93, 98, 100, 107, 109, 113, 126, 138, 158. The scan was OCR'd twice with two renderers: 137 and 136 articles found, so the result varies by about 1 with the image conversion.

## What it taught us
1. **The week-1 rule is perfect on clean text but fragile on OCR text:** one missed article marker ("المادة 16" read badly) blocks every following article, hence 11 instead of 136. The tolerant mode fixes this, and the skipped numbers are **reported, not hidden**.
2. **The French splitter output is byte-for-byte identical** after the change (same 158 articles): the same code now serves both cases, strict by default.
3. **OCR variants had to be handled**: "المادة" is read as "الملدة" or "الماية"; article 1 is written "الأولى"; the running page header must be removed; the Arabic headings are الباب / الفصل / الفرع.
4. **Reading order**: OCR of the whole page mixes the two columns. Cutting the columns first is essential.

## Limits (what we did NOT prove)
- Article **detection** is measured (136/158). The **text quality** is not: some paragraphs contain OCR garbage (for example article 33 has stray symbols). A weak automatic signal: for 26 articles that have numbers in parentheses in French, 14 (53%) have the same numbers in the Arabic OCR. This is only a lower bound (the Arabic version sometimes writes numbers in words), **not an accuracy figure**.
- **To do (needs a human who reads Arabic):** compare 10 Arabic articles with the scan and write the error rate here.
- The **French** noisy test is still to do: download the French JO (P1's downloader), run `python src/structuring/ocr_pdf.py <pdf> data/raw/jo_fr_ocr.txt --lang fra --columns 1`, then `splitter.py --input ... --max-gap 3`.

## Decision needed from the team: Arabic
The teacher's page for project 1 says texts are in French **and Arabic** and requires **at least 5 test questions whose answer is in an Arabic text**. We therefore need Arabic articles in the corpus. Options: (a) improve this OCR (cleaner scan, image preprocessing); (b) find the Arabic text in a digital form and use that; (c) translate or summarize the Arabic passages into French when preparing the corpus (accepted by the teacher if justified). `articles_ar.json` is a **test artefact, not yet corpus quality**.
