"""French legal-text normalization shared by BM25 and evaluation."""
import re
import unicodedata

FRENCH_STOP_WORDS = set("""a à afin ai ainsi après attendu au aucun aucune aujourd hui auparavant auquel auxquels aussi autre autres aux auquel avec avoir bon car ce ceci cela celle celles celui ceux chacun chacune chaque chez comme comment concernant contre d dans de des du dedans dehors depuis derrière dès désormais devant donc dont du elle elles en encore entre envers est et eux fait faites fois font hors ici il ils je jusque la le les leur leurs lui ma mais malgré me même mes mien moins mon ne ni non nos notre nous on ont ou où par parce parmi pas pendant personne peu peut plus plusieurs pour pourquoi quand que quel quelle quelles quels qui quoi sa sans se selon ses seulement si sien son sont sous sur ta te tes toi ton tous tout toute toutes très tu un une vers via votre vos vous y""".split())

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("’", "'")
    # Keep legal article identifiers and alphanumeric compounds intact.
    return re.sub(r"[^a-z0-9]+", " ", text).strip()

def tokenize(text: str, remove_stopwords: bool = True) -> list[str]:
    tokens = normalize(text).split()
    if remove_stopwords:
        tokens = [t for t in tokens if t not in FRENCH_STOP_WORDS and len(t) > 1]
    return tokens
