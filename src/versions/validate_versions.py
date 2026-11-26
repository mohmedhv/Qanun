"""Validateur de conformité P3 — Versions et Hiérarchie des normes.
Usage : python src/versions/validate_versions.py

Vérifie l'intégrité de la table `versions`, le respect des règles de temporalité
(valid_to = next_valid_from - 1 jour), l'absence de contenu fictif, la garantie
qu'un article abrogé ne revient jamais comme en vigueur, ainsi que l'enregistrement
des 11 textes normatifs officiels et des relations juridiques.
"""
import datetime
import json
import csv
import sqlite3
import sys
from pathlib import Path

# Ajouter la racine du projet au sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Chemins
DB_PATH = PROJECT_ROOT / "data" / "db" / "qanun.db"

# Exigences minimales du cahier des charges P3
MIN_TRACKED_ARTICLES = 3
EXPECTED_OFFICIAL_TEXTS = [
    "loi-90-11", "loi-91-29", "decret-legislatif-94-03", "decret-legislatif-94-09",
    "ordonnance-96-21", "ordonnance-97-02", "ordonnance-97-03", "loi-14-10",
    "ordonnance-15-01", "loi-17-11", "loi-22-16"
]


def parse_date(date_str: str) -> datetime.date:
    """Parse une date ISO YYYY-MM-DD."""
    return datetime.date.fromisoformat(date_str)


def validate_versions() -> int:
    """Exécute tous les contrôles de validation du jalon P3."""
    print("=" * 70)
    print("VALIDATEUR DE CONFORMITÉ P3 — VERSIONS ET HIÉRARCHIE (QANUN)")
    print("=" * 70)

    if not DB_PATH.exists():
        print(f"ANOMALY : Base de données introuvable à {DB_PATH}")
        return 1

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    problems = []

    # 1. Vérification de la présence des tables requises
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for expected_table in ["texts", "articles", "versions", "relations"]:
        if expected_table in tables:
            print(f"OK      Table présente : '{expected_table}'")
        else:
            print(f"ANOMALY Table manquante : '{expected_table}'")
            problems.append(f"missing_table_{expected_table}")

    if "versions" not in tables:
        print("\nRESULTAT : ÉCHEC CRITIQUE (table 'versions' absente)")
        con.close()
        return 1

    # 2. Vérification des 11 textes officiels enregistrés
    db_texts = [r[0] for r in cur.execute("SELECT text_id FROM texts").fetchall()]
    missing_texts = [t for t in EXPECTED_OFFICIAL_TEXTS if t not in db_texts]
    if not missing_texts:
        print(f"OK      Tous les 11 textes normatifs officiels sont enregistrés dans 'texts' ({len(db_texts)} textes au total).")
    else:
        print(f"ANOMALY Textes officiels manquants dans 'texts' : {missing_texts}")
        problems += missing_texts

    # 3. Vérification de la table 'relations'
    from src.versions.load_versions import SEED, read, relation_records
    expected = {(r["source_id"], r["type"], r["target_id"]) for r in relation_records(read(SEED))}
    triples = [tuple(row) for row in cur.execute("SELECT source_id, type, target_id FROM relations")]
    if set(triples) == expected and len(triples) == len(expected):
        print(f"OK      {len(expected)} relations conformes à l’inventaire Week 2.")
    else:
        print("ANOMALY Relations manquantes, supplémentaires ou dupliquées.")
        problems.append("relation_evidence_mismatch")

    # 4. Vérification des articles versionnés (au moins 3)
    art_numbers = [r[0] for r in cur.execute("SELECT DISTINCT article_number FROM versions").fetchall()]
    tracked_count = len(art_numbers)
    if tracked_count >= MIN_TRACKED_ARTICLES:
        print(f"OK      Nombre d'articles suivis = {tracked_count} (minimum requis : {MIN_TRACKED_ARTICLES}) -> {art_numbers}")
    else:
        print(f"ANOMALY Nombre d'articles suivis insuffisant : {tracked_count} < {MIN_TRACKED_ARTICLES}")
        problems.append("insufficient_tracked_articles")

    # 5. Vérification de l'absence de contenu vide ou fictif
    rows = cur.execute("SELECT version_id, article_number, version_number, content FROM versions").fetchall()
    empty_content = [f"Art {r['article_number']} v{r['version_number']}" for r in rows if not r["content"] or len(r["content"].strip()) < 15]
    if not empty_content:
        print("OK      Aucun contenu fictif ou vide détecté dans les versions.")
    else:
        print(f"ANOMALY Versions avec contenu vide ou insuffisant : {empty_content}")
        problems += empty_content

    # 6. Vérification de la règle de validité temporelle : valid_to = next_valid_from - 1 jour
    date_problems = []
    for art in art_numbers:
        v_rows = cur.execute(
            "SELECT version_number, valid_from, valid_to, status, repeal_date "
            "FROM versions WHERE article_number = ? ORDER BY version_number ASC",
            (art,),
        ).fetchall()

        for i in range(len(v_rows)):
            cur_v = v_rows[i]
            # Valider le format de valid_from
            try:
                cur_from = parse_date(cur_v["valid_from"])
            except Exception as e:
                date_problems.append(f"Format valid_from invalide pour art {art} v{cur_v['version_number']}: {e}")
                continue

            # Si ce n'est pas la dernière version, valid_to doit être exactement veille du prochain valid_from
            if i + 1 < len(v_rows):
                next_v = v_rows[i + 1]
                try:
                    next_from = parse_date(next_v["valid_from"])
                    expected_to = next_from - datetime.timedelta(days=1)
                    if not cur_v["valid_to"]:
                        date_problems.append(f"Art {art} v{cur_v['version_number']} valid_to manquant (attendu {expected_to})")
                    elif parse_date(cur_v["valid_to"]) != expected_to:
                        date_problems.append(
                            f"Art {art} v{cur_v['version_number']} valid_to non conforme : "
                            f"{cur_v['valid_to']} != {expected_to.isoformat()} (veille du prochain)"
                        )
                except Exception as e:
                    date_problems.append(f"Erreur calcul valid_to art {art}: {e}")

            else:
                # Dernière version
                if cur_v["status"] == "repealed" or cur_v["repeal_date"]:
                    # Article abrogé : valid_to doit être la veille de la date d'abrogation
                    try:
                        rep_date = parse_date(cur_v["repeal_date"])
                        expected_to = rep_date - datetime.timedelta(days=1)
                        if parse_date(cur_v["valid_to"]) != expected_to:
                            date_problems.append(
                                f"Art abrogé {art} : valid_to ({cur_v['valid_to']}) != veille abrogation ({expected_to})"
                            )
                    except Exception as e:
                        date_problems.append(f"Erreur validation abrogation art {art}: {e}")
                else:
                    # Article toujours en vigueur : valid_to doit être NULL
                    if cur_v["valid_to"] is not None:
                        date_problems.append(f"Art en vigueur {art} v{cur_v['version_number']} doit avoir valid_to à NULL")

    if not date_problems:
        print("OK      Règle de validité respectée : valid_to = next_valid_from - 1 jour (sans chevauchement ni trou).")
    else:
        for dp in date_problems:
            print(f"ANOMALY {dp}")
        problems += date_problems

    # 6 bis. Vérification des dates juridiques validées pour les articles suivis
    expected_timeline = {
        "73": [("1990-04-27", "1991-12-26"), ("1991-12-27", None)],
        "72": [("1990-04-27", "1994-06-02")],
        "87": [("1990-04-27", "2015-01-01"), ("2015-01-02", None)],
        "87 bis": [("1994-01-01", "2015-01-01")],
        "12": [("1990-04-27", "1996-07-11"), ("1996-07-12", None)],
        "12 bis": [("1996-07-12", None)],
        "73-4": [("1996-07-12", None)],
    }
    for article, expected_rows in expected_timeline.items():
        actual_rows = cur.execute(
            "SELECT valid_from, valid_to FROM versions WHERE article_number = ? ORDER BY version_number",
            (article,),
        ).fetchall()
        actual = [(r["valid_from"], r["valid_to"]) for r in actual_rows]
        if actual == expected_rows:
            print(f"OK      Dates de validité documentées : article {article} -> {actual}")
        else:
            problems.append(f"invalid_legal_timeline_{article}")
            print(f"ANOMALY Dates article {article} : {actual} != {expected_rows}")

    # Vérifier que l'inventaire JSON/CSV est synchronisé et n'attribue pas l'abrogation de 87 bis au décret 15-107.
    try:
        amendments_json = PROJECT_ROOT / "data" / "interim" / "amendments.json"
        amendments_csv = PROJECT_ROOT / "data" / "interim" / "amendments.csv"
        json_rows = json.loads(amendments_json.read_text(encoding="utf-8"))
        with amendments_csv.open("r", encoding="utf-8-sig", newline="") as f:
            csv_rows = list(csv.DictReader(f))
        false_repeal = any(
            a.get("modifying_text_id") == "decret-executif-15-107" and a.get("target_article") == "87 bis"
            for a in json_rows
        )
        compare_fields = [
            "target_article", "action", "modifying_text_id", "modifying_text_type", "modifying_text_number",
            "date_signed", "jo_number", "jo_date", "amending_article", "partial", "new_content",
            "instruction", "needs_review", "review_reasons"
        ]
        json_normalized = []
        for row in json_rows:
            item = dict(row)
            item["partial"] = str(bool(item.get("partial")))
            item["needs_review"] = str(bool(item.get("needs_review")))
            item["new_content"] = item.get("new_content") or ""
            json_normalized.append(tuple(str(item.get(k) or "") for k in compare_fields))
        csv_normalized = [tuple(str(row.get(k) or "") for k in compare_fields) for row in csv_rows]
        synchronized = json_normalized == csv_normalized
        if len(json_rows) == 79 and len(csv_rows) == 79 and not false_repeal and synchronized:
            review_count = sum(bool(a.get("needs_review")) for a in json_rows)
            print(f"OK      Inventaire amendments.json/amendments.csv synchronisé (79 entrées) ; abrogation 87 bis correctement attribuée ; {review_count} entrée(s) marquée(s) needs_review.")
        else:
            problems.append("amendment_inventory_mismatch")
            print(f"ANOMALY Inventaire amendements : JSON={len(json_rows)}, CSV={len(csv_rows)}, fausse attribution={false_repeal}, synchronisé={synchronized}")
    except Exception as e:
        problems.append(f"amendment_inventory_error: {e}")
        print(f"ANOMALY Impossible de valider l'inventaire des amendements : {e}")

    from src.versions.load_versions import verification_rows
    try:
        expected_reviews = verification_rows()
        actual_reviews = [dict(row) for row in con.execute("SELECT * FROM amendment_verification ORDER BY csv_row")]
        status_mismatch = con.execute("""
            SELECT v.version_id FROM versions v
            LEFT JOIN amendment_verification a ON a.modifying_text_id = v.modifying_text_id
                AND a.target_article = v.article_number
            WHERE v.verification_status IS NOT a.verification_status
        """).fetchall()
        if status_mismatch:
            problems.append("version_source_status_mismatch")
        if actual_reviews != expected_reviews:
            problems.append("verification_csv_database_mismatch")
        else:
            print(f"OK      {len(actual_reviews)} statuts identiques au CSV source.")
    except (sqlite3.Error, KeyError, ValueError) as exc:
        problems.append(f"verification: {exc}")

    # 7. Vérification du comportement des articles abrogés (ne reviennent jamais comme actuels)
    from src.versions.versions import get_version
    repeal_problems = []
    repealed_arts = [r[0] for r in cur.execute("SELECT DISTINCT article_number FROM versions WHERE status = 'repealed'").fetchall()]
    for r_art in repealed_arts:
        v_actuel = get_version("loi-90-11", r_art)
        if v_actuel is not None:
            repeal_problems.append(f"Article abrogé '{r_art}' retourné comme en vigueur aujourd'hui !")
        # Vérifier aussi à une date postérieure à l'abrogation
        v_post = get_version("loi-90-11", r_art, "2026-01-01")
        if v_post is not None:
            repeal_problems.append(f"Article abrogé '{r_art}' retourné comme en vigueur en 2026 !")

    if not repeal_problems:
        print(f"OK      Garantie absolue : aucun article abrogé ({repealed_arts}) n'est retourné comme actuel.")
    else:
        for rp in repeal_problems:
            print(f"ANOMALY {rp}")
        problems += repeal_problems

    # 8. Vérification de la non-régression sur le corpus d'articles (158 articles originaux)
    art_count = cur.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    if art_count == 158:
        print("OK      Corpus initial des articles préservé (158 articles conformes).")
    else:
        print(f"ANOMALY Altération de la table articles : {art_count} articles au lieu de 158.")
        problems.append("corrupted_articles_count")

    # 9. Bilan final
    con.close()
    print("-" * 70)
    if not problems:
        print("RÉSULTAT GLOBAL : TOUTES LES VÉRIFICATIONS P3 ONT RÉUSSI (CONFORME)")
        print("=" * 70)
        return 0
    else:
        print(f"RÉSULTAT GLOBAL : ÉCHEC ({len(problems)} anomalie(s) détectée(s))")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(validate_versions())
