"""Module tests.test_versions — Tests unitaires et d'intégration pour P3 (Versions et Hiérarchie).

Ce module teste rigoureusement les 4 cas obligatoires et les cas limites :
1. Cas 1 : Date antérieure à la première version (retourne None).
2. Cas 2 : Date intermédiaire entre deux versions (retourne la version historique exacte).
3. Cas 3 : Date actuelle / aujourd'hui (retourne la version actuellement en vigueur).
4. Cas 4 : Date postérieure à une abrogation (l'article abrogé ne revient jamais comme en vigueur).
5. Cas limites : Bornes exactes de validité (valid_to = next_valid_from - 1 jour).
6. Cas ordonnancement : list_versions retourne l'historique complet par ordre chronologique.
7. Cas hiérarchie des normes : rank_conflict résout correctement les conflits entre textes.
8. Cas d'intégrité : table 'texts' (11 textes officiels) et table 'relations'.
9. Cas d'erreur et robustesse : numéro d'article inexistant ou dates limites.
10. Vérification des sources officielles et des relations.
11. Dates légales et inventaire d'amendements synchronisé.
"""
import sqlite3
import unittest
from pathlib import Path
from src.versions.versions import get_version, list_versions, rank_conflict

# Chemin de la base de données de test
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "db" / "qanun.db"


class TestVersionsEtHierarchie(unittest.TestCase):
    """Suite de tests pour le versionnage et la hiérarchie des normes de la Loi 90-11."""

    def setUp(self):
        self.db = DB_PATH
        self.assertTrue(self.db.exists(), f"La base de données doit exister à {self.db}")

    # -------------------------------------------------------------------------
    # 1. CAS OBLIGATOIRE 1 : Avant la première date
    # -------------------------------------------------------------------------
    def test_01_date_avant_premiere_version_retourne_none(self):
        """Vérifie qu'une requête à une date antérieure à la promulgation retourne None."""
        # Article 73 promulgué le 21/04/1990 (obligatoire à Alger le 27/04/1990)
        v_1980 = get_version("loi-90-11", "73", "1980-01-01")
        self.assertIsNone(v_1980, "Une date antérieure à 1990 ne doit retourner aucune version pour l'art. 73.")

        v_1990_early = get_version("loi-90-11", "73", "1990-04-25")
        self.assertIsNone(v_1990_early, "La veille de l'entrée en vigueur (25/04/1990) doit retourner None.")

        # DL94-03 has no 1 January clause; the adjacent DL94-04 does.
        v_87bis_1993 = get_version("loi-90-11", "87 bis", "1993-12-31")
        self.assertIsNone(v_87bis_1993)
        self.assertIsNone(get_version("loi-90-11", "87 bis", "1994-04-14"))
        self.assertIsNotNone(get_version("loi-90-11", "87 bis", "1994-04-15"))

    # -------------------------------------------------------------------------
    # 2. CAS OBLIGATOIRE 2 : Entre deux versions (période historique)
    # -------------------------------------------------------------------------
    def test_02_date_entre_deux_versions_retourne_version_historique(self):
        """Vérifie qu'une requête à une date intermédiaire retourne la version historique exacte."""
        # Article 73 : version 1 active du 27/04/1990 au 26/12/1991
        v_1990 = get_version("loi-90-11", "73", "1990-06-15")
        self.assertIsNotNone(v_1990, "L'art. 73 en juin 1990 doit retourner une version valide.")
        self.assertEqual(v_1990["version_number"], 1)
        self.assertEqual(v_1990["valid_from"], "1990-04-27")
        self.assertEqual(v_1990["valid_to"], "1991-12-26")
        self.assertEqual(v_1990["modifying_text_id"], "loi-90-11")
        self.assertIn("Le licenciement intervient dans le cas de fautes graves", v_1990["content"])

        # Article 87 : version 1 active du 27/04/1990 au 01/01/2015
        v_87_2005 = get_version("loi-90-11", "87", "2005-07-01")
        self.assertIsNotNone(v_87_2005)
        self.assertEqual(v_87_2005["version_number"], 1)
        self.assertEqual(v_87_2005["valid_from"], "1990-04-27")
        self.assertEqual(v_87_2005["valid_to"], "2015-01-01")

    # -------------------------------------------------------------------------
    # 3. CAS OBLIGATOIRE 3 : Aujourd'hui (version actuelle)
    # -------------------------------------------------------------------------
    def test_03_date_actuelle_retourne_version_en_vigueur(self):
        """Vérifie que la requête sans date (ou date du jour) retourne la version actuellement en vigueur."""
        # Article 73 : version 2 en vigueur issue de la loi 91-29
        v_today = get_version("loi-90-11", "73")
        self.assertIsNotNone(v_today, "L'art. 73 doit retourner une version actuellement en vigueur.")
        self.assertEqual(v_today["version_number"], 2)
        self.assertEqual(v_today["valid_from"], "1991-12-27")
        self.assertIsNone(v_today["valid_to"], "La version actuelle doit avoir valid_to à NULL (durée indéterminée).")
        self.assertEqual(v_today["status"], "in_force")
        self.assertEqual(v_today["modifying_text_id"], "loi-91-29")
        self.assertIn("Le licenciement à caractère disciplinaire intervient", v_today["content"])

        # Article 87 : version 2 en vigueur issue de la loi 14-10
        v_87_today = get_version("loi-90-11", "87")
        self.assertIsNotNone(v_87_today)
        self.assertEqual(v_87_today["version_number"], 2)
        self.assertEqual(v_87_today["valid_from"], "2015-01-02")
        self.assertIsNone(v_87_today["valid_to"])
        self.assertEqual(v_87_today["status"], "in_force")
        self.assertEqual(v_87_today["modifying_text_id"], "loi-14-10")

    # -------------------------------------------------------------------------
    # 4. CAS OBLIGATOIRE 4 : Après abrogation (l'article abrogé ne revient jamais)
    # -------------------------------------------------------------------------
    def test_04_date_apres_abrogation_ne_retourne_rien(self):
        """Vérifie qu'un article abrogé ne revient jamais comme en vigueur après sa date d'abrogation."""
        # Article 72 abrogé le 03/06/1994 par le Décret législatif 94-09
        # Test historique avant abrogation : doit exister
        v72_active = get_version("loi-90-11", "72", "1992-01-01")
        self.assertIsNotNone(v72_active)
        self.assertEqual(v72_active["version_number"], 1)
        self.assertEqual(v72_active["valid_to"], "1994-06-02")

        # Test après abrogation (date historique postérieure)
        v72_1995 = get_version("loi-90-11", "72", "1995-01-01")
        self.assertIsNone(v72_1995, "L'art. 72 ne doit retourner aucune version après le 02/06/1994.")

        # Test aujourd'hui (date=None)
        v72_today = get_version("loi-90-11", "72")
        self.assertIsNone(v72_today, "L'art. 72 abrogé ne doit jamais être retourné comme version actuelle.")

        # Article 87 bis abrogé le 02/01/2015 par la Loi 14-10
        # Test historique pendant validité (1994-2014)
        v87b_active = get_version("loi-90-11", "87 bis", "2005-01-01")
        self.assertIsNotNone(v87b_active)
        self.assertEqual(v87b_active["valid_from"], "1994-04-15")
        self.assertEqual(v87b_active["valid_to"], "2015-01-01")

        # Test après abrogation
        v87b_2016 = get_version("loi-90-11", "87 bis", "2016-01-01")
        self.assertIsNone(v87b_2016, "L'art. 87 bis ne doit retourner aucune version après le 01/01/2015.")

        v87b_today = get_version("loi-90-11", "87 bis")
        self.assertIsNone(v87b_today, "L'art. 87 bis abrogé ne doit jamais être retourné comme actuel.")

    # -------------------------------------------------------------------------
    # 5. TEST DES BORNES EXACTES DE VALIDITÉ (valid_to = next_valid_from - 1 jour)
    # -------------------------------------------------------------------------
    def test_05_bornes_exactes_de_validite(self):
        """Vérifie la transition exacte d'une version à l'autre au jour près."""
        # Art. 73 : publication 25/12/1991, jour franc 26/12, obligation à Alger le 27/12
        v_dernier_jour_v1 = get_version("loi-90-11", "73", "1991-12-26")
        self.assertIsNotNone(v_dernier_jour_v1)
        self.assertEqual(v_dernier_jour_v1["version_number"], 1, "Le 26/12/1991 est le dernier jour de la V1.")

        v_premier_jour_v2 = get_version("loi-90-11", "73", "1991-12-27")
        self.assertIsNotNone(v_premier_jour_v2)
        self.assertEqual(v_premier_jour_v2["version_number"], 2, "Le 27/12/1991 est le premier jour de la V2.")

        # Art. 72 : publication 01/06/1994, jour franc 02/06, abrogation obligatoire à Alger le 03/06
        v72_veille = get_version("loi-90-11", "72", "1994-06-02")
        self.assertIsNotNone(v72_veille, "Le 02/06/1994 est le dernier jour avant l'abrogation, encore valide.")

        v72_jour_abrog = get_version("loi-90-11", "72", "1994-06-03")
        self.assertIsNone(v72_jour_abrog, "Le 03/06/1994 est la date d'abrogation obligatoire à Alger, doit retourner None.")

    # -------------------------------------------------------------------------
    # 6. TEST DE L'ORDONNANCEMENT CHRONOLOGIQUE (list_versions)
    # -------------------------------------------------------------------------
    def test_06_list_versions_ordonnancement_chronologique(self):
        """Vérifie que list_versions retourne l'historique complet par ordre chronologique."""
        hist_73 = list_versions("loi-90-11", "73")
        self.assertEqual(len(hist_73), 2, "L'art. 73 doit comporter exactement 2 versions.")
        self.assertEqual(hist_73[0]["version_number"], 1)
        self.assertEqual(hist_73[1]["version_number"], 2)
        self.assertTrue(hist_73[0]["valid_from"] < hist_73[1]["valid_from"])

        hist_87 = list_versions("loi-90-11", "87")
        self.assertEqual(len(hist_87), 2)
        self.assertEqual(hist_87[0]["version_number"], 1)
        self.assertEqual(hist_87[1]["version_number"], 2)
        self.assertTrue(hist_87[0]["valid_from"] < hist_87[1]["valid_from"])

        hist_72 = list_versions("loi-90-11", "72")
        self.assertEqual(len(hist_72), 1)
        self.assertEqual(hist_72[0]["status"], "repealed")
        self.assertEqual(hist_72[0]["repeal_date"], "1994-06-03")

        hist_87bis = list_versions("loi-90-11", "87 bis")
        self.assertEqual(len(hist_87bis), 1)
        self.assertEqual(hist_87bis[0]["status"], "repealed")
        self.assertEqual(hist_87bis[0]["repeal_date"], "2015-01-02")

    # -------------------------------------------------------------------------
    # 7. TEST DE LA HIÉRARCHIE DES NORMES (rank_conflict)
    # -------------------------------------------------------------------------
    def test_07_rank_conflict_resolution_hierarchie(self):
        """Vérifie que rank_conflict applique fidèlement la pyramide des normes du droit algérien."""
        # 1. Constitution l'emporte sur Loi
        res_const_loi = rank_conflict("constitution", "loi")
        self.assertEqual(res_const_loi["winner"], "text_a")
        self.assertEqual(res_const_loi["prevailing_text"], "constitution")

        # 2. Loi l'emporte sur Décret
        res_loi_decret = rank_conflict("loi", "decret_executif")
        self.assertEqual(res_loi_decret["winner"], "text_a")
        self.assertEqual(res_loi_decret["prevailing_text"], "loi")

        # 3. Décret l'emporte sur Arrêté
        res_dec_arr = rank_conflict("decret", "arrete")
        self.assertEqual(res_dec_arr["winner"], "text_a")

        # 4. Arrêté l'emporte sur Circulaire
        res_arr_circ = rank_conflict("arrete", "circulaire")
        self.assertEqual(res_arr_circ["winner"], "text_a")

        # 5. Loi et Ordonnance ont le même rang (rang 2)
        res_loi_ord = rank_conflict("loi", "ordonnance")
        self.assertEqual(res_loi_ord["winner"], "equal")
        self.assertEqual(res_loi_ord["rule"], "same_rank")

        # 6. Test avec text_id réels de la base
        res_ids = rank_conflict("loi-90-11", "decret-legislatif-94-09")
        self.assertEqual(res_ids["winner"], "text_a")
        self.assertEqual(res_ids["prevailing_text"], "loi-90-11")

        # 7. Test avec les textes fiscaux ajoutés
        res_ord15 = rank_conflict("ordonnance-15-01", "arrete")
        self.assertEqual(res_ord15["winner"], "text_a")
        self.assertEqual(res_ord15["rank_a"], 2)

    # -------------------------------------------------------------------------
    # 8. TEST D'INTÉGRITÉ DE LA BASE DE DONNÉES (texts, relations, articles)
    # -------------------------------------------------------------------------
    def test_08_integrite_texts_et_relations(self):
        """Vérifie l'enregistrement des 11 textes officiels et des relations juridiques."""
        con = sqlite3.connect(self.db)
        cur = con.cursor()
        try:
            # 11 textes officiels requis
            expected_texts = [
                "loi-90-11", "loi-91-29", "decret-legislatif-94-03", "decret-legislatif-94-09",
                "ordonnance-96-21", "ordonnance-97-02", "ordonnance-97-03", "loi-14-10",
                "ordonnance-15-01", "loi-17-11", "loi-22-16"
            ]
            db_texts = [r[0] for r in cur.execute("SELECT text_id FROM texts").fetchall()]
            for t in expected_texts:
                self.assertIn(t, db_texts, f"Le texte officiel '{t}' doit être enregistré dans 'texts'.")

            # Au moins 20 relations juridiques enregistrées
            rel_count = cur.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
            self.assertGreaterEqual(rel_count, 20, "La table relations doit contenir les liens juridiques vérifiés.")

            # Corpus articles de 1990 intact (158 articles)
            art_count = cur.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            self.assertEqual(art_count, 158, "La table articles doit conserver ses 158 articles originaux.")
        finally:
            con.close()

    # -------------------------------------------------------------------------
    # 9. TEST DE ROBUSTESSE ET CAS LIMITES
    # -------------------------------------------------------------------------
    def test_09_robustesse_cas_limites(self):
        """Vérifie le comportement face à des requêtes inexistantes ou invalides."""
        # Article inexistant
        v_inconnu = get_version("loi-90-11", "999")
        self.assertIsNone(v_inconnu, "Un article inexistant doit retourner None sans erreur.")

        # Texte inexistant
        v_texte_inconnu = get_version("loi-inconnue", "73")
        self.assertIsNone(v_texte_inconnu, "Un texte inexistant doit retourner None.")

        # Historique d'un article inexistant
        hist_vide = list_versions("loi-90-11", "999")
        self.assertEqual(hist_vide, [], "L'historique d'un article inexistant doit être une liste vide.")

    # -------------------------------------------------------------------------
    # 10. TEST DES RÉFÉRENCES JURIDIQUES ET RELATIONS OFFICIELLES CERTIFIÉES
    # -------------------------------------------------------------------------
    def test_10_verifications_sources_officielles_et_relations_exactes(self):
        """Vérifie rigoureusement la conformité des métadonnées de textes et des relations juridiques."""
        con = sqlite3.connect(self.db)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        try:
            # 1. Vérification Loi 91-29 : JO n° 68 du 25/12/1991
            t_9129 = cur.execute("SELECT jo_number, jo_date FROM texts WHERE text_id = 'loi-91-29'").fetchone()
            self.assertIsNotNone(t_9129)
            self.assertEqual(t_9129["jo_number"], "JO n°68")
            self.assertEqual(t_9129["jo_date"], "1991-12-25")

            # 2. Vérification Loi 22-16 : JO n° 49 du 20/07/2022
            t_2216 = cur.execute("SELECT jo_number, jo_date FROM texts WHERE text_id = 'loi-22-16'").fetchone()
            self.assertIsNotNone(t_2216)
            self.assertEqual(t_2216["jo_number"], "JO n°49")
            self.assertEqual(t_2216["jo_date"], "2022-07-20")

            # 3. Vérification de l'abrogation de l'article 72 par Décret législatif 94-09 (art. 35)
            v72 = cur.execute("SELECT repealing_text_id, status FROM versions WHERE article_number = '72'").fetchone()
            self.assertIsNotNone(v72)
            self.assertEqual(v72["repealing_text_id"], "decret-legislatif-94-09")
            self.assertEqual(v72["status"], "repealed")

            # 4. Vérification de la modification de l'art. 87 par Loi 14-10 (art. 89)
            v87_v2 = cur.execute("SELECT modifying_text_id, status FROM versions WHERE article_number = '87' AND version_number = 2").fetchone()
            self.assertIsNotNone(v87_v2)
            self.assertEqual(v87_v2["modifying_text_id"], "loi-14-10")
            self.assertEqual(v87_v2["status"], "in_force")

            # 5. Vérification de l'abrogation de l'art. 87 bis par Loi 14-10 (art. 90)
            v87b = cur.execute("SELECT repealing_text_id, status FROM versions WHERE article_number = '87 bis'").fetchone()
            self.assertIsNotNone(v87b)
            self.assertEqual(v87b["repealing_text_id"], "loi-14-10")
            self.assertEqual(v87b["status"], "repealed")

            # 6. Vérification des relations spécifiques :
            # - ordonnance-97-02 -> art-52-bis (et AUCUNE relation vers art-88)
            rel_9702_52bis = cur.execute("SELECT 1 FROM relations WHERE source_id = 'ordonnance-97-02' AND target_id = 'loi-90-11-art-52-bis'").fetchone()
            self.assertIsNotNone(rel_9702_52bis, "Ordonnance 97-02 doit être reliée à l'article 52 bis.")
            rel_9702_88 = cur.execute("SELECT 1 FROM relations WHERE source_id = 'ordonnance-97-02' AND target_id LIKE '%88%'").fetchone()
            self.assertIsNone(rel_9702_88, "Ordonnance 97-02 ne doit PAS être reliée à l'article 88.")

            # - ordonnance-15-01 -> art-140 et art-149 (et AUCUNE vers art-87)
            rel_1501_140 = cur.execute("SELECT 1 FROM relations WHERE source_id = 'ordonnance-15-01' AND target_id = 'loi-90-11-art-140'").fetchone()
            rel_1501_149 = cur.execute("SELECT 1 FROM relations WHERE source_id = 'ordonnance-15-01' AND target_id = 'loi-90-11-art-149'").fetchone()
            rel_1501_87 = cur.execute("SELECT 1 FROM relations WHERE source_id = 'ordonnance-15-01' AND target_id LIKE '%87%'").fetchone()
            self.assertIsNotNone(rel_1501_140)
            self.assertIsNotNone(rel_1501_149)
            self.assertIsNone(rel_1501_87, "Ordonnance 15-01 ne doit PAS être reliée à l'article 87.")

            # - loi-17-11 -> art-144 et art-148 (et AUCUNE vers art-87)
            rel_1711_144 = cur.execute("SELECT 1 FROM relations WHERE source_id = 'loi-17-11' AND target_id = 'loi-90-11-art-144'").fetchone()
            rel_1711_148 = cur.execute("SELECT 1 FROM relations WHERE source_id = 'loi-17-11' AND target_id = 'loi-90-11-art-148'").fetchone()
            rel_1711_87 = cur.execute("SELECT 1 FROM relations WHERE source_id = 'loi-17-11' AND target_id LIKE '%87%'").fetchone()
            self.assertIsNotNone(rel_1711_144)
            self.assertIsNotNone(rel_1711_148)
            self.assertIsNone(rel_1711_87, "Loi 17-11 ne doit PAS être reliée à l'article 87.")

            # - loi-22-16 -> art-56-bis et art-64
            rel_2216_56bis = cur.execute("SELECT 1 FROM relations WHERE source_id = 'loi-22-16' AND target_id = 'loi-90-11-art-56-bis'").fetchone()
            rel_2216_64 = cur.execute("SELECT 1 FROM relations WHERE source_id = 'loi-22-16' AND target_id = 'loi-90-11-art-64'").fetchone()
            self.assertIsNotNone(rel_2216_56bis)
            self.assertIsNotNone(rel_2216_64)

        finally:
            con.close()


    def test_11_dates_legales_et_inventaire_complet(self):
        """Vérifie les dates calculées selon l'article 4 et la couverture des modifications directes."""
        # La loi 90-11 est publiée le 25/04/1990 : le 26/04 est le jour franc, obligation à Alger le 27/04.
        self.assertIsNone(get_version("loi-90-11", "73", "1990-04-26"))
        self.assertIsNotNone(get_version("loi-90-11", "73", "1990-04-27"))
        # Loi 91-29 publiée le 25/12/1991 : le 26/12 est le jour franc, version nouvelle le 27/12.
        self.assertEqual(get_version("loi-90-11", "73", "1991-12-26")["version_number"], 1)
        self.assertEqual(get_version("loi-90-11", "73", "1991-12-27")["version_number"], 2)
        # Loi 14-10 publiée le 31/12/2014 : le 01/01/2015 est le jour franc, effet obligatoire le 02/01.
        self.assertEqual(get_version("loi-90-11", "87", "2015-01-01")["version_number"], 1)
        self.assertEqual(get_version("loi-90-11", "87", "2015-01-02")["version_number"], 2)
        self.assertIsNotNone(get_version("loi-90-11", "87 bis", "2015-01-01"))
        self.assertIsNone(get_version("loi-90-11", "87 bis", "2015-01-02"))

        # Inventaire : la ligne d'abrogation de 87 bis est attribuée à la Loi 14-10, pas au décret d'application 15-107.
        import json
        amendments = json.loads((Path(__file__).resolve().parents[1] / "data/interim/amendments.json").read_text(encoding="utf-8"))
        self.assertEqual(len(amendments), 79)
        self.assertEqual(sum(bool(a.get("needs_review")) for a in amendments), 16)
        self.assertFalse(any(a.get("modifying_text_id") == "decret-executif-15-107" and a.get("target_article") == "87 bis" for a in amendments))
        self.assertTrue(any(a.get("modifying_text_id") == "loi-14-10" and a.get("target_article") == "87 bis" and a.get("action") == "repeal" for a in amendments))
        # Tous les articles 56 bis à 56 bis 6 et l'article 64 sont reliés à la Loi 22-16.
        con = sqlite3.connect(self.db)
        try:
            for art in ["56-bis", "56-bis-1", "56-bis-2", "56-bis-3", "56-bis-4", "56-bis-5", "56-bis-6", "64"]:
                self.assertIsNotNone(con.execute("SELECT 1 FROM relations WHERE source_id='loi-22-16' AND target_id=?", (f"loi-90-11-art-{art}",)).fetchone())
            for art in ["141", "142", "143", "143-bis", "144", "145", "146", "146-bis", "147", "148", "150", "151", "152", "154"]:
                self.assertIsNotNone(con.execute("SELECT 1 FROM relations WHERE source_id='loi-17-11' AND target_id=?", (f"loi-90-11-art-{art}",)).fetchone())
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main()
