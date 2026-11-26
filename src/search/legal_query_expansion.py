"""Conservative, generic French legal query expansion (experimental)."""
import re
import unicodedata

PHRASES = (
    ("relation salariée", ("relation de travail", "relation d'emploi")),
    ("relation de travail", ("relation salariée", "relation d'emploi")),
    ("travailleurs salariés", ("personnes salariées", "employés")),
    ("travailleur salarié", ("salarié", "employé")),
    ("travailleur", ("salarié", "employé")),
    ("salariés", ("employés", "personnes salariées")),
    ("salariée", ("employée", "personne salariée")),
    ("salarié", ("employé", "personne salariée")),
    ("contrat à durée déterminée", ("CDD", "contrat de travail à durée déterminée")),
    ("contrat à durée indéterminée", ("CDI", "contrat de travail sans terme")),
    ("heures supplémentaires", ("travail supplémentaire", "heures au-delà de la durée légale")),
    ("durée légale hebdomadaire", ("durée légale du travail par semaine", "temps de travail hebdomadaire")),
    ("travail de nuit", ("travail nocturne", "travail effectué la nuit")),
    ("congé annuel", ("congés payés", "repos annuel rémunéré")),
    ("licencier", ("licenciement", "rupture du contrat à l'initiative de l'employeur")),
    ("licenciement", ("rupture du contrat à l'initiative de l'employeur",)),
    ("rémunération", ("salaire", "contrepartie financière du travail")),
    ("prouver", ("établir la preuve", "démontrer")),
    ("preuve", ("établissement de l'existence",)),
)
TERMS = (
    ("salari", ("employé", "personne salariée", "travailleur rémunéré")),
    ("employ", ("travailleur salarié", "personne employée")),
    ("cdd", ("contrat à durée déterminée", "durée déterminée")),
    ("heures supplementaires", ("majoration", "travail au-delà de la durée légale")),
    ("travail de nuit", ("travail nocturne", "heures de nuit")),
    ("conge", ("repos annuel", "congé rémunéré")),
    ("licenci", ("rupture du contrat de travail", "motif de licenciement")),
    ("duree hebdomadaire", ("temps de travail par semaine", "durée légale du travail")),
    ("remuner", ("salaire", "rémunération du travail")),
)

def _norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower()).strip()

def expand_queries(query, max_variants=4):
    """Original query first, then bounded deterministic generic alternatives."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if not isinstance(max_variants, int) or isinstance(max_variants, bool) or max_variants < 0:
        raise ValueError("max_variants must be a non-negative integer")
    original = re.sub(r"\s+", " ", query).strip()
    normalized = _norm(original)
    variants, seen = [], {_norm(original)}

    def add(candidate):
        candidate = re.sub(r"\s+", " ", candidate).strip()
        key = _norm(candidate)
        if candidate and key not in seen and len(variants) < max_variants:
            seen.add(key)
            variants.append(candidate)

    for source, alternatives in PHRASES:
        if _norm(source) in normalized:
            for alternative in alternatives:
                add(re.sub(re.escape(source), alternative, original, count=1, flags=re.IGNORECASE))
                if len(variants) >= max_variants:
                    break
        if len(variants) >= max_variants:
            break

    if len(variants) < max_variants:
        extra = []
        for marker, terms in TERMS:
            if marker in normalized:
                extra.extend(terms)
        if extra:
            add(original + " " + " ".join(dict.fromkeys(extra)))
    return [original, *variants]

def expanded_query_text(query, max_variants=4):
    """Concatenated query for one BM25 ranking; original text remains included."""
    return " ".join(expand_queries(query, max_variants=max_variants))
