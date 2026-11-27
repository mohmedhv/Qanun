## Week 1
- P2: Split law 90-11 into 158 articles with a regex splitter, loaded them in SQLite, validated count and sequence, checked 10 articles by hand.
- P2 learned: amendment blocks contain fake Art. N lines, so an article start is accepted only if it is the next expected number.

## Week 2
- P2: Chunking (one article = one chunk, 160 chunks), parser of amending texts (59 records for P3), splitter made tolerant to OCR errors and tested on the Arabic JO scan (136/158 articles).
- P2 learned: a strict "next number" rule breaks on OCR text (11 articles), so we accept a small gap and report what is missing.

## Week 3
- P2: Built a NetworkX graph (220 nodes, 298 edges), exported it to nodes.csv and edges.csv, and performed integrity checks. Fixed the splitter to prevent 2018 text from leaking into articles 141–154.
- P2 learned: basic integrity checks are not enough to catch all errors. P3 identified missing articles in some versions and incorrectly stored dates by comparing the data with the official journal (JO).