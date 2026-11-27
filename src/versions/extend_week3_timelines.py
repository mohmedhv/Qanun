"""Reconstruct full article versions from P2 baselines and official JO amendments.

This maintenance script is intentionally narrow: it updates the P3 version seed,
the review flags for wordings reconstructed here, and a provenance ledger. It
does not modify the immutable P2 parser snapshot or the P1 article corpus.
"""
import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/db/qanun.db"
SEED = ROOT / "data/version_seed/p3_seed.json"
AMENDMENTS = ROOT / "data/interim/amendments.json"
AMENDMENTS_CSV = ROOT / "data/interim/amendments.csv"
EVIDENCE = ROOT / "data/version_seed/p3_week3_evidence.json"
REVIEW = ROOT / "data/week3/full_wording_review.csv"
DATE_RULE = "https://www.joradp.dz/TRV/F2024G02.pdf#page=6"

JO_1990 = "https://www.joradp.dz/FTP/Jo-Francais/1990/F1990017.pdf"
JO_1991 = "https://www.joradp.dz/FTP/Jo-Francais/1991/F1991068.pdf"
JO_1996 = "https://www.joradp.dz/FTP/Jo-Francais/1996/F1996043.pdf"
JO_2017 = "https://www.joradp.dz/FTP/jo-francais/2017/F2017076.pdf"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def split_paragraphs(content):
    return [part.strip() for part in content.splitlines() if part.strip()]


def replace_once(content, old, new, label):
    if content.count(old) != 1:
        raise ValueError(f"Expected one {label} marker; found {content.count(old)}")
    return content.replace(old, new, 1)


def article_id(number):
    return "loi-90-11-art-" + str(number).replace(" ", "-")


def version(version_id, number, number_in_chain, content, valid_from, valid_to,
            status, modifying_text_id, source_url, verification_status=None):
    return {
        "version_id": version_id,
        "text_id": "loi-90-11",
        "article_number": str(number),
        "article_id": article_id(number),
        "version_number": number_in_chain,
        "content": content,
        "paragraphs": json.dumps(split_paragraphs(content), ensure_ascii=False),
        "valid_from": valid_from,
        "valid_to": valid_to,
        "status": status,
        "repeal_date": None,
        "repealing_text_id": None,
        "modifying_text_id": modifying_text_id,
        "source_url": source_url,
        "verification_status": verification_status,
    }


def source_for(text_id, number, printed_page):
    base = {"loi-91-29": (JO_1991, "#page=4"),
            "ordonnance-96-21": (JO_1996, f"#page={printed_page}"),
            "loi-17-11": (JO_2017, f"#page={printed_page}")}
    url, fragment = base[text_id]
    return url + fragment


def build_current_2017(number, baseline, inserted_1996=None, operation=None):
    if number in {"141", "144", "145"}:
        return operation["new_content"].replace(" En cas de récidive, ", "\nEn cas de récidive, ")

    source = inserted_1996 if inserted_1996 is not None else baseline
    replacements = {
        "142": (
            "est puni d’une amende de 2.000 à 5.000 DA.\nEn cas de récidive, la peine est de 2.000 à 10.000 DA et d’un emprisonnement de trois (3) jours, ou de l’une de ces deux (2) peines seulement.",
            "est puni d'une amende de 100.000 DA à 200.000 DA.\nEn cas de récidive, la peine est de 200.000 DA à 500.000 DA et d'un emprisonnement d’un (1) mois à trois (3) mois, ou de l'une de ces deux peines seulement"),
        "143": (
            "est puni d’une amende de 500 à 1.000 DA appliquée pour chacune des infractions constatées et autant de fois qu’il y a de travailleurs concernés.",
            "est puni d’une amende de 10.000 DA à 20.000 DA appliquée pour chacune des infractions constatées et autant de fois qu'il y a de travailleurs concernés.\nEn cas de récidive, la peine est de 40.000 DA à 50.000 DA multipliée par autant de fois qu’il y a de travailleurs concernés"),
        "143 bis": (
            "est puni d’une amende de 1.000 à 2.000 DA appliquée autant de fois qu’il y a de travailleurs concernés",
            "est puni d'une amende de 10.000 DA à 20.000 DA appliquée autant de fois qu'il y a de travailleurs concernés.\nEn cas de récidive, la peine est de 40.000 DA à 50.000 DA multipliée par autant de fois qu’il y a de travailleurs concernés"),
        "146": (
            "est puni d’une amende de 2.000 à 5.000 DA multipliée par autant de fois qu’il y a de travailleurs concernés.",
            "est puni d'une amende de 100.000 DA à 200.000 DA multipliée par autant de fois qu'il y a de travailleurs concernés"),
        "146 bis": (
            "est punie d’une amende de 1.000 à 2.000 DA appliquée autant de fois qu’il y a infractions",
            "est punie d'une amende de 10.000 DA à 20.000 DA appliquée autant de fois qu'il y a de travailleurs concernés.\nEn cas de récidive, la peine est de 40.000 DA à 50.000 DA multipliée par autant de fois qu’il y a de travailleurs concernés"),
        "147": (
            "est puni d’une amende de 1.000 à 2.000 DA.",
            "est punie d'une amende de 10.000 DA à 20.000 DA"),
        "148": (
            "est puni d’une amende de 500 à 1.000 DA, multipliée, par autant de fois qu’il y a d’infractions.",
            "est puni d'une amende de 10.000 DA à 20.000 DA multipliée par autant de fois qu'il y a de travailleurs concernés.\nEn cas de récidive, la peine est de 40.000 DA à 50.000 DA multipliée par autant de fois qu'il y a de travailleurs concernés"),
        "150": (
            "est punie d’une amende de 1.000 à 2.000 DA, multipliée par autant de fois qu’il y a d’infractions.\nEn cas de récidive, la peine est de 2.000 à 4.000 DA applicable autant de fois qu’il y a d’infractions et d’un emprisonnement d’un (1) mois à trois (3) mois, ou de l’une de ces deux (2) peines seulement.",
            "est punie d'une amende de 10.000 DA à 20.000 DA multipliée par autant de fois qu'il y a de travailleurs concernés.\nEn cas de récidive, la peine est de 40.000 DA à 50.000 DA applicable autant de fois qu'il y a de travailleurs concernés et d'un emprisonnement de trois (3) mois à six (6) mois, ou de l'une de ces deux peines seulement"),
        "151": (
            "est punie d’une amende 5.000 à 20.000 DA et d’un emprisonnement de un (1) mois à trois (3) mois ou de l’une de ces deux (2) peines seulement.",
            "est punie d'une amende de 100.000 DA à 200.000 DA et d'un emprisonnement d’un (1) mois à trois (3) mois ou de l'une de ces deux peines seulement.\nEn cas de récidive, la peine est de 200.000 DA à 500.000 DA multipliée par autant de fois qu'il y a de travailleurs concernés et d'un emprisonnement de trois (3) mois à six (6) mois, ou de l'une de ces deux peines seulement"),
        "152": (
            "est punie d’une amende de 1.000 à 4.000 DA.",
            "est punie d'une amende de 10.000 DA à 20.000 DA.\nEn cas de récidive, la peine est de 40.000 DA à 50.000 DA"),
        "154": (
            "sont punis d’une amende de 2.000 à 4.000 DA.\nEn cas de récidive, l’amende est porté de 4.000 à 8.000 DA.",
            "sont punis d'une amende de 10.000 DA à 20.000 DA.\nEn cas de récidive, la peine est de 40.000 DA à 50.000 DA"),
    }
    old, new = replacements[number]
    return replace_once(source, old, new, f"article {number} sanction")


def run():
    seed = read_json(SEED)
    generated_ids = set(range(18, 55))
    # Keep this maintenance step repeatable after partial I/O failures.
    seed["versions"] = [row for row in seed["versions"] if row["version_id"] not in generated_ids]
    amendments = read_json(AMENDMENTS)
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        articles = {row["number"]: row for row in con.execute(
            "SELECT number, content, paragraphs, source_url FROM articles WHERE text_id='loi-90-11'")}

    def original(number):
        row = articles[number]
        return row["content"].strip()

    def operation(text_id, number):
        rows = [r for r in amendments if r["modifying_text_id"] == text_id and r["target_article"] == number]
        if len(rows) != 1:
            raise ValueError(f"Expected one operation for {(text_id, number)}, found {len(rows)}")
        return rows[0]

    additions = []
    evidence = [row for row in read_json(EVIDENCE) if row.get("version_id") not in generated_ids]
    reviews = []

    # 1991 insertion of article 73-4, followed by its existing 1996 replacement.
    article_73_4_1991 = (
        "En cas de licenciement présumé abusif ou effectué en violation des procédures légales et/ou "
        "conventionnelles obligatoires, le travailleur peut introduire une demande en annulation de la "
        "décision de licenciement et/ou de dommages et intérêts en réparation du préjudice subi auprès de "
        "la juridiction compétente qui statue en premier et dernier ressort."
    )
    for row in seed["versions"]:
        if row["version_id"] == 12:
            row["version_number"] = 2
            row["valid_from"] = "1996-07-12"
            row["valid_to"] = None
            row["status"] = "in_force"
    additions.append(version(18, "73-4", 1, article_73_4_1991, "1991-12-27", "1996-07-11",
                             "replaced", "loi-91-29", source_for("loi-91-29", "73-4", 2167),
                             "verifie_jo_officiel"))
    evidence.append({
        "version_id": 18, "article_number": "73-4", "modifying_text_id": "loi-91-29",
        "content_source_url": source_for("loi-91-29", "73-4", 2167), "content_printed_page": "2167-2168",
        "valid_from_basis": "JO n°68 published 1991-12-25; one clear day in Alger is 1991-12-26, effective 1991-12-27 under Civil Code article 4.",
        "date_rule_source": DATE_RULE, "review_date": "2026-11-27",
        "reviewer": "Codex documentary reconstruction; independent human review pending",
        "method": "Full article text transcribed from the official JO insertion; effect date follows the project Alger convention.",
        "independent_review_status": "pending"
    })
    reviews.append({"modifying_text_id": "loi-91-29", "target_article": "73-4", "provision": "Art. 3",
                    "version_ids": "18", "full_wording_status": "reconstructed_from_official_insertion",
                    "official_source_url": source_for("loi-91-29", "73-4", 2167),
                    "source_pages": "2167-2168", "independent_review_status": "pending",
                    "note": "The former 1991 wording is now stored separately from the 1996 amended text."})

    # Four 1996 modifications now have complete consolidated text in the timeline.
    op96 = {n: operation("ordonnance-96-21", n) for n in ("13", "31", "54", "97")}
    content96 = {
        "13": original("13") + "\n" + op96["13"]["new_content"].strip(),
        "31": original("31") + "\n" + op96["31"]["new_content"].strip().replace(
            "Dans ces cas, les représentants", "\nDans ces cas, les représentants"),
        "54": "\n".join(split_paragraphs(original("54"))[:3] + [op96["54"]["new_content"].strip()] + split_paragraphs(original("54"))[4:]),
        "97": original("97") + "\n" + op96["97"]["new_content"].strip(),
    }
    page96 = {"13": 7, "31": 7, "54": 7, "97": 8}
    next_id = 19
    for number in ("13", "31", "54", "97"):
        content0 = original(number)
        content1 = content96[number]
        from_url = source_for("ordonnance-96-21", number, page96[number])
        additions.extend([
            version(next_id, number, 1, content0, "1990-04-27", "1996-07-11", "replaced",
                    "loi-90-11", articles[number]["source_url"] + "#page=" + {"13": "3", "31": "5", "54": "6", "97": "9"}[number]),
            version(next_id + 1, number, 2, content1, "1996-07-12", None, "in_force",
                    "ordonnance-96-21", from_url, "verifie_jo_officiel"),
        ])
        evidence.extend([
            {"version_id": next_id, "article_number": number, "content_source_url": articles[number]["source_url"] + "#page=" + {"13": "3", "31": "5", "54": "6", "97": "9"}[number],
             "content_printed_page": {"13": 489, "31": 491, "54": 492, "97": 495}[number],
             "review_date": "2026-11-27", "reviewer": "Codex documentary reconstruction",
             "method": "Baseline text retained from the project article database and attributed to the official JO page; no independent second-person sign-off."},
            {"version_id": next_id + 1, "article_number": number, "modifying_text_id": "ordonnance-96-21",
             "content_source_url": from_url, "content_printed_page": page96[number],
             "valid_from_basis": "JO n°43 published 1996-07-10; one clear day in Alger is 1996-07-11, effective 1996-07-12 under Civil Code article 4.",
             "date_rule_source": DATE_RULE, "review_date": "2026-11-27",
             "reviewer": "Codex documentary reconstruction; independent human review pending",
             "method": "Complete wording reconstructed by combining the 1990 baseline with the exact added or replaced clause in Ordonnance 96-21.",
             "independent_review_status": "pending"},
        ])
        reviews.append({"modifying_text_id": "ordonnance-96-21", "target_article": number,
                        "provision": op96[number]["amending_article"], "version_ids": f"{next_id},{next_id + 1}",
                        "full_wording_status": "reconstructed_from_baseline_and_official_amendment",
                        "official_source_url": from_url, "source_pages": page96[number],
                        "independent_review_status": "pending",
                        "note": "Source operation excerpt remains partial; the full consolidated article is in the version timeline."})
        next_id += 2

    # 2017 text: base articles plus the 1996 insertions for 143 bis and 146 bis.
    article_ids = ("141", "142", "143", "143 bis", "144", "145", "146", "146 bis", "147", "148", "150", "151", "152", "154")
    op17 = {n: operation("loi-17-11", n) for n in article_ids}
    old_insertions = {
        "143 bis": operation("ordonnance-96-21", "143 bis")["new_content"].strip(),
        "146 bis": operation("ordonnance-96-21", "146 bis")["new_content"].strip(),
    }
    page17 = {n: (44 if n == "141" else 46 if n in {"150", "151", "152", "154"} else 45)
              for n in article_ids}
    for number in article_ids:
        base = old_insertions[number] if number in old_insertions else original(number)
        current = build_current_2017(number, base, old_insertions.get(number), op17[number])
        if number in old_insertions:
            additions.append(version(next_id, number, 1, base, "1996-07-12", "2017-12-29", "replaced",
                                     "ordonnance-96-21", source_for("ordonnance-96-21", number, 8),
                                     "verifie_jo_officiel"))
            evidence.append({"version_id": next_id, "article_number": number,
                             "modifying_text_id": "ordonnance-96-21",
                             "content_source_url": source_for("ordonnance-96-21", number, 8),
                             "content_printed_page": 8, "review_date": "2026-11-27",
                             "reviewer": "Codex documentary reconstruction; independent human review pending",
                             "method": "Complete insertion text from the 1996 amendment is preserved as the baseline for the 2017 amendment.",
                             "independent_review_status": "pending"})
            current_number = 2
            next_id += 1
        else:
            additions.append(version(next_id, number, 1, base, "1990-04-27", "2017-12-29", "replaced",
                                     "loi-90-11", articles[number]["source_url"], None))
            evidence.append({"version_id": next_id, "article_number": number,
                             "content_source_url": articles[number]["source_url"],
                             "review_date": "2026-11-27", "reviewer": "Codex documentary reconstruction",
                             "method": "Baseline wording inherited from the project article database; official JO transcription remains subject to independent review."})
            current_number = 2
            next_id += 1
        src = source_for("loi-17-11", number, page17[number])
        additions.append(version(next_id, number, current_number, current, "2017-12-30", None, "in_force",
                                 "loi-17-11", src, "verifie_jo_officiel"))
        evidence.append({"version_id": next_id, "article_number": number, "modifying_text_id": "loi-17-11",
                         "content_source_url": src, "content_printed_page": page17[number],
                         "valid_from_basis": "JO n°76 published 2017-12-28; one clear day in Alger is 2017-12-29, effective 2017-12-30 under Civil Code article 4.",
                         "date_rule_source": DATE_RULE, "review_date": "2026-11-27",
                         "reviewer": "Codex documentary reconstruction; independent human review pending",
                         "method": "Full current wording reconstructed from the 1990 baseline (or 1996 insertion) plus Article 99 of the official JO. Text marked ‘sans changement’ was retained from the prior version.",
                         "independent_review_status": "pending"})
        version_ids = f"{next_id - current_number + 1},{next_id}"
        reviews.append({"modifying_text_id": "loi-17-11", "target_article": number,
                        "provision": "Art. 99", "version_ids": version_ids,
                        "full_wording_status": "reconstructed_from_baseline_and_official_amendment",
                        "official_source_url": src, "source_pages": page17[number],
                        "independent_review_status": "pending",
                        "note": "Official Article 99 uses ‘sans changement’ ellipses for unchanged clauses; inherited wording is retained in full."})
        next_id += 1

    seed_ids = {r["version_id"] for r in seed["versions"]}
    if any(r["version_id"] in seed_ids for r in additions):
        raise ValueError("A generated version ID already exists in the seed")
    seed["versions"].extend(additions)
    seed["versions"].sort(key=lambda r: r["version_id"])
    write_json(SEED, seed)

    # Preserve operation excerpts and parser metadata; update only completion review fields.
    checked = {(r["modifying_text_id"], r["target_article"]) for r in reviews}
    checked |= {("loi-17-11", n) for n in ("141", "144", "145")}
    for row in amendments:
        if (row["modifying_text_id"], row["target_article"]) in checked:
            row["needs_review"] = False
            row["review_reasons"] = ""
            row["official_full_wording_checked"] = True
            row["independent_check_status"] = "pending"
    write_json(AMENDMENTS, amendments)
    with AMENDMENTS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        csv_fields = next(csv.reader(handle))
    csv_fields.extend(key for row in amendments for key in row if key not in csv_fields)
    with AMENDMENTS_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerows(amendments)

    evidence.sort(key=lambda row: (row.get("version_id", 0), row.get("article_number", "")))
    write_json(EVIDENCE, evidence)
    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    with REVIEW.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(reviews[0]))
        writer.writeheader()
        writer.writerows(reviews)
    print(f"Added {len(additions)} version rows; full wording reviews recorded: {len(reviews)}")


if __name__ == "__main__":
    run()
