# Accepté par l'équipe le 25 novembre 2026 : le contrat d'Ikram (P2) est la référence.

# Proposition de contrat de données P2

**État : accepté.** Base SQLite : `data/db/qanun.db`, reconstruite par la commande commune `python -m src.common.build_all`.

## Conventions

- Les dates sont des textes ISO `YYYY-MM-DD`. `valid_from` est la date d'entrée en vigueur, pas la date de signature.
- `article_id = <text_id>-art-<number>`; remplacer les espaces du numéro par des tirets. Exemples : `loi-90-11-art-33`, `loi-90-11-art-12-bis`.
- Les numéros d'article sont conservés comme TEXT (`33`, `12 bis`, `73-1`). `sort_key` est la partie entière initiale utilisée pour le tri.
- Un article modifié ou abrogé conserve son identité et son historique. Les statuts d'article sont `in_force` et `repealed`.

## Table `texts`

| Colonne | Type | Sens |
|---|---|---|
| `text_id` | TEXT, clé primaire | `loi-90-11` |
| `type` | TEXT | loi, ordonnance, décret, arrêté, circulaire, etc. |
| `number` | TEXT | `90-11` |
| `title` | TEXT | Titre complet |
| `date_signed` | TEXT | Date de signature |
| `jo_number` | TEXT | Numéro du Journal officiel, par exemple `JO n°17` |
| `jo_date` | TEXT | Date de publication au Journal officiel |
| `source_url` | TEXT | URL de la source |
| `rank_level` | INTEGER | Rang 1–5; loi et ordonnance = 2 |
| `language` | TEXT | Langue, défaut `fr` |
| `pdf_path` | TEXT | Chemin local du PDF, nullable |

## Table `articles`

| Colonne | Type | Sens |
|---|---|---|
| `article_id` | TEXT, clé primaire | Identifiant stable selon la convention ci-dessus |
| `text_id` | TEXT, clé étrangère | Texte parent |
| `number` | TEXT | `33` ou `12 bis` |
| `sort_key` | INTEGER | Partie entière du numéro |
| `suffix` | TEXT | NULL, `bis`, `ter`, etc. |
| `parent_title` | TEXT | Titre parent |
| `parent_chapter` | TEXT | Chapitre parent, nullable |
| `parent_section` | TEXT | Section parente, nullable |
| `content` | TEXT | Texte intégral de l'article |
| `paragraphs` | TEXT | Liste JSON des alinéas |
| `status` | TEXT | `in_force` par défaut; sinon `repealed` |
| `valid_from` | TEXT | Début de validité; renseigné par P3 |
| `valid_to` | TEXT | Fin de validité; NULL si la période n'est pas bornée |
| `source_url` | TEXT | URL de provenance |

Contrainte unique : (`text_id`, `number`).

## Table `relations`

| Colonne | Type | Sens |
|---|---|---|
| `relation_id` | INTEGER, clé primaire | Générée automatiquement |
| `source_id` | TEXT | `text_id` ou `article_id` |
| `target_id` | TEXT | `text_id` ou `article_id` |
| `type` | TEXT | `modifies`, `repeals`, `applies`, `adds` ou `cites` |

## Table `chunks` (P2 vers P4)

| Colonne | Type | Sens |
|---|---|---|
| `chunk_id` | TEXT, clé primaire | `loi-90-11-art-33` ou `loi-90-11-art-94#2` |
| `article_id` | TEXT, clé étrangère | Article parent, y compris pour une partie |
| `part`, `n_parts` | INTEGER | Numéro de partie et nombre total |
| `text` | TEXT | Texte fourni à la recherche et au lecteur |
| `text_for_embedding` | TEXT | Contexte et texte indexés par P4 |
| `n_chars` | INTEGER | Longueur du texte |
| `source_url` | TEXT | URL de provenance |

La table est construite par `src/structuring/chunks.py`. Les fichiers JSON d'équipe dans `data/interim/` ne sont pas remplacés par la construction.

## Amendements (P2 vers P3)

Les données de transfert sont dans `data/interim/amendments.json` et `.csv` (voir `docs/amendments_handoff.md`). Les nouveaux articles issus d'un amendement gardent leur numéro TEXT, par exemple `12 bis`, `52 ter`, `73-1`; `sort_key` reste la partie entière initiale.

## Langue

`texts.language` vaut `fr` par défaut. Si des articles arabes sont ajoutés, conserver leur langue explicitement et utiliser des identifiants stables.

## Versions (P3)

La table `versions` fait partie du contrat à cinq tables. Son DDL réel et les noms/types de ses colonnes doivent être repris du code ou de la base P3; ils ne sont pas présents dans ce dépôt. Ne pas les déduire de cette proposition. Voir `docs/contract_open_questions.md`.

`verification_status` est nullable et accepte `verifie_jo_officiel`, `verifie_copie_publiee` ou `a_verifier`. Ne pas modifier les valeurs des lignes P3 existantes.

## Découpage P4

Un article forme généralement un chunk. Les articles longs peuvent être découpés par paragraphe, mais chaque partie conserve `article_id` pour permettre la citation de l'article parent. Voir `docs/chunking.md`.

## Suivi

La définition DDL P3 et la correspondance de ses statuts de vérification CSV sont consignées dans `docs/contract_open_questions.md`.
