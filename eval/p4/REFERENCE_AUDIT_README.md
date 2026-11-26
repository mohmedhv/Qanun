> État actuel: les cinq contre-lectures demandées sont renseignées par Codex en assistance de FOUGHALI HOUSSEINE. Quatre références sont confirmées au texte original, Q008 nécessite une correction. Les quinze autres questions restent hors de cette revue de cinq références. L’ancienne colonne supplémentaire human_confirmation_status a été retirée. Le protocole reçu et ses états historiques sont conservés ci-dessous.

# Reference verification — Law 90-11 (original text, 1990)

**Primary reference audit:** the mapping of all 20 questions to the specified article in the original law has been inspected against **Journal officiel n°17, 25 April 1990, printed pages 488–491**, through the official archived PDF: https://joradp.dz/FTP/jo-francais/1990/F1990017.pdf. Evidence is recorded per question in `reference_audit_1990.csv`. This verifies the *article mapping in the original 1990 text*, not historical amendments or the law currently in force.

**Independent second-person sign-off:** **PENDING** on all 20 rows. This cannot be supplied by an assistant acting in place of P2/P3. A teammate must inspect the same official PDF and enter their actual name, date, and `CONFIRMED` (or `CORRECTION_REQUIRED`) in the audit CSV; only then update the corresponding column in `eval/questions.csv`.

**Critical temporal limits:** Article 22 in the original publication explicitly states **44 hours per week**; do not treat this as an up-to-date rule without P3's legal amendments. Article 33 lists Friday in the original. The dataset is a retrieval benchmark against the source supplied by P2, **not proof that every 1990 wording remains legally valid today**.

**Procedure for reviewer:** Open the official PDF; find the original article number and confirm it answers the exact question; verify that the article wording extracted into `data/processed/chunks.jsonl` matches the source (OCR typography may differ); enter reviewer, review date, and status. Resolve disagreements before using these labels as certified benchmark ground truth.
