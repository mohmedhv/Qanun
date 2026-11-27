"""Module src.versions.versions — Implémentation des fonctions de versionnage et hiérarchie (P3).

Ce module fournit :
1. get_version(text_id, article_number, date=None) : Récupération de la version d'un article
   selon sa validité temporelle (en vigueur aujourd'hui ou à une date historique).
2. list_versions(text_id, article_number) : Liste ordonnée chronologiquement de toutes les
   versions d'un article.
3. rank_conflict(text_a, text_b) : Résolution des conflits de normes selon la hiérarchie juridique
   officielle du droit algérien (Constitution > Loi/Ordonnance > Décret > Arrêté > Circulaire).
"""
import json
import sqlite3
from datetime import date as calendar_date
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Chemin par défaut vers la base de données SQLite
DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "db" / "qanun.db"

# Pyramide des normes algériennes (selon Cahier des charges Projet 1 Jurideazor, page 2)
# Plus le chiffre est petit, plus le rang hiérarchique est élevé (1 = rang suprême).
LEGAL_HIERARCHY: Dict[str, int] = {
    "constitution": 1,
    "loi": 2,
    "ordonnance": 2,            # Même force juridique que la loi en droit algérien
    "decret_legislatif": 3,     # Textes législatifs d'exception (1992-1996), assimilés décrets/lois
    "decret_presidentiel": 3,
    "decret_executif": 3,
    "decret": 3,
    "arrete_interministeriel": 4,
    "arrete_ministeriel": 4,
    "arrete": 4,
    "circulaire": 5,            # Consigne interne sans valeur législative
    "instruction": 5,
}


def _get_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """Ouvre une connexion à la base de données avec row_factory sqlite3.Row."""
    target_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Base de données introuvable : {target_path}")
    con = sqlite3.connect(target_path)
    con.row_factory = sqlite3.Row
    return con


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convertit un objet sqlite3.Row en dictionnaire avec désérialisation JSON des paragraphes."""
    d = dict(row)
    if "paragraphs" in d and isinstance(d["paragraphs"], str):
        try:
            d["paragraphs"] = json.loads(d["paragraphs"])
        except Exception:
            pass
    return d


def get_version(
    text_id: str,
    article_number: str,
    date: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retourne la version d'un article en vigueur à une date donnée ou aujourd'hui.

    Signature conforme au cahier des charges P3 (section 3.3).
    Utilise deux requêtes SQL distinctes selon que la date est précisée ou non.

    Règles de validité temporelle :
    - Si date is None : recherche la version actuellement en vigueur (valid_from <= date('now'),
      valid_to IS NULL, status != 'repealed').
    - Si date est fournie (format ISO YYYY-MM-DD) : recherche la version historique active à cette date
      (valid_from <= date AND (valid_to IS NULL OU valid_to >= date) AND non abrogée à cette date).
    - Si la date est antérieure au premier valid_from : retourne None.
    - Si l'article est abrogé à la date demandée : retourne None. Un article abrogé ne revient jamais
      comme version en vigueur.

    Args:
        text_id: Identifiant du texte (ex. 'loi-90-11').
        article_number: Numéro de l'article sous forme de chaîne (ex. '73', '87', '87 bis').
        date: Date cible au format 'YYYY-MM-DD' (optionnel).

    Returns:
        Dictionnaire représentant la version ou None si aucune version n'est en vigueur.
    """
    con = _get_connection()
    try:
        cur = con.cursor()
        art_num = str(article_number).strip()

        if date is None:
            # Requête SQL 1 : Version courante en vigueur
            sql_current = """
            SELECT version_id, text_id, article_number, article_id, version_number,
                   content, paragraphs, valid_from, valid_to, status, repeal_date,
                   repealing_text_id, modifying_text_id, source_url, verification_status
            FROM versions
            WHERE text_id = ?
              AND article_number = ?
              AND valid_from <= date('now')
              AND valid_to IS NULL
              AND status != 'repealed'
            ORDER BY valid_from DESC
            LIMIT 1;
            """
            cur.execute(sql_current, (text_id, art_num))
            row = cur.fetchone()
            return _row_to_dict(row) if row else None

        else:
            # Requête SQL 2 : Version à une date historique précise
            target_date = calendar_date.fromisoformat(str(date).strip()).isoformat()
            sql_historical = """
            SELECT version_id, text_id, article_number, article_id, version_number,
                   content, paragraphs, valid_from, valid_to, status, repeal_date,
                   repealing_text_id, modifying_text_id, source_url, verification_status
            FROM versions
            WHERE text_id = ?
              AND article_number = ?
              AND valid_from <= ?
              AND (valid_to IS NULL OR valid_to >= ?)
              AND (repeal_date IS NULL OR repeal_date > ?)
            ORDER BY valid_from DESC
            LIMIT 1;
            """
            cur.execute(sql_historical, (text_id, art_num, target_date, target_date, target_date))
            row = cur.fetchone()
            return _row_to_dict(row) if row else None

    finally:
        con.close()


def list_versions(
    text_id: str,
    article_number: str,
) -> List[Dict[str, Any]]:
    """Retourne l'historique complet des versions d'un article ordonné chronologiquement.

    Signature conforme au cahier des charges P3 (section 3.3).

    Args:
        text_id: Identifiant du texte (ex. 'loi-90-11').
        article_number: Numéro de l'article (ex. '73', '72', '87', '87 bis').

    Returns:
        Liste de dictionnaires représentant toutes les versions successives (valid_from ASC).
    """
    con = _get_connection()
    try:
        cur = con.cursor()
        art_num = str(article_number).strip()

        sql = """
        SELECT version_id, text_id, article_number, article_id, version_number,
               content, paragraphs, valid_from, valid_to, status, repeal_date,
               repealing_text_id, modifying_text_id, source_url, verification_status
        FROM versions
        WHERE text_id = ?
          AND article_number = ?
        ORDER BY valid_from ASC, version_number ASC;
        """
        cur.execute(sql, (text_id, art_num))
        rows = cur.fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        con.close()


def _normalize_type(raw_type: str) -> str:
    """Normalise un type de texte juridique vers une clé de la hiérarchie."""
    t = raw_type.lower().strip().replace("-", "_").replace(" ", "_")
    t = t.replace("é", "e").replace("è", "e").replace("ê", "e")
    return t


def _resolve_text_type(
    text_ref: Union[str, Dict[str, Any]],
    con: Optional[sqlite3.Connection] = None,
) -> tuple[str, str]:
    """Résout le type et l'identifiant d'un texte juridique donné par ID, dict ou type direct."""
    if isinstance(text_ref, dict):
        t_id = text_ref.get("text_id", "")
        t_type = text_ref.get("type", "")
        if t_type:
            return t_id or t_type, _normalize_type(t_type)
        if t_id and con:
            cur = con.cursor()
            row = cur.execute("SELECT type FROM texts WHERE text_id = ?", (t_id,)).fetchone()
            if row:
                return t_id, _normalize_type(row[0])
        return t_id, _normalize_type(t_id)

    ref_str = str(text_ref).strip()
    norm = _normalize_type(ref_str)
    if norm in LEGAL_HIERARCHY:
        return ref_str, norm

    # Si c'est un text_id (ex. 'loi-90-11', 'decret-legislatif-94-03'), chercher dans la base
    if con:
        cur = con.cursor()
        row = cur.execute("SELECT type FROM texts WHERE text_id = ?", (ref_str,)).fetchone()
        if row:
            return ref_str, _normalize_type(row[0])

    # Déduction par préfixe usuel
    for prefix in ["constitution", "loi", "ordonnance", "decret_legislatif", "decret_presidentiel", "decret_executif", "decret", "arrete", "circulaire", "instruction"]:
        if norm.startswith(prefix):
            return ref_str, prefix

    return ref_str, norm


def rank_conflict(
    text_a: Union[str, Dict[str, Any]],
    text_b: Union[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Compare la valeur hiérarchique de deux textes juridiques et résout leur conflit.

    Applique la règle de droit « Lex superior derogat legi inferiori » selon la hiérarchie
    définie dans le cahier des charges officiel du module RCR (Page 2) :
    1. Constitution
    2. Loi et Ordonnance (force juridique équivalente)
    3. Décret (présidentiel, exécutif, législatif)
    4. Arrêté
    5. Circulaire / Instruction

    Args:
        text_a: Premier texte (identifiant, type, ou dictionnaire).
        text_b: Second texte (identifiant, type, ou dictionnaire).

    Returns:
        Dictionnaire détaillant le texte prévalent, les rangs hiérarchiques et la règle appliquée.
    """
    con = None
    try:
        try:
            con = _get_connection()
        except Exception:
            con = None

        id_a, type_a = _resolve_text_type(text_a, con)
        id_b, type_b = _resolve_text_type(text_b, con)

        rank_a = LEGAL_HIERARCHY.get(type_a, 99)
        rank_b = LEGAL_HIERARCHY.get(type_b, 99)

        if rank_a == 99 or rank_b == 99:
            # An unknown legal text must not be silently classified as equal rank.
            return {
                "prevailing_text": None,
                "winner": "undetermined",
                "rank_a": rank_a if rank_a != 99 else None,
                "rank_b": rank_b if rank_b != 99 else None,
                "type_a": type_a,
                "type_b": type_b,
                "rule": "unknown_legal_rank",
                "explanation": "Impossible de déterminer la primauté sans identifier la nature juridique des deux textes.",
            }

        if rank_a < rank_b:
            prevailing = id_a
            winner = "text_a"
            rule = "lex_superior"
            explanation = (
                f"Le texte '{id_a}' (type: {type_a}, rang: {rank_a}) prévaut sur "
                f"'{id_b}' (type: {type_b}, rang: {rank_b}) en vertu du principe de primauté de la norme supérieure."
            )
        elif rank_b < rank_a:
            prevailing = id_b
            winner = "text_b"
            rule = "lex_superior"
            explanation = (
                f"Le texte '{id_b}' (type: {type_b}, rang: {rank_b}) prévaut sur "
                f"'{id_a}' (type: {type_a}, rang: {rank_a}) en vertu du principe de primauté de la norme supérieure."
            )
        else:
            prevailing = None
            winner = "equal"
            rule = "same_rank"
            explanation = (
                f"Les textes '{id_a}' et '{id_b}' ont le même rang hiérarchique ({rank_a}). "
                "En cas de contradiction, la règle chronologique (lex posterior derogat legi priori) "
                "ou la spécialité (lex specialis derogat legi generali) s'applique."
            )

        return {
            "prevailing_text": prevailing,
            "winner": winner,
            "rank_a": rank_a,
            "rank_b": rank_b,
            "type_a": type_a,
            "type_b": type_b,
            "rule": rule,
            "explanation": explanation,
        }
    finally:
        if con:
            con.close()
