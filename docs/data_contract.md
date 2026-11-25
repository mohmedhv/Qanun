# Contrat de données Qanun

**État : accepté par l'équipe le 25 novembre 2026. Référence retenue : proposition d'Ikram (P2).**

La base SQLite partagée est `data/db/qanun.db`. Le DDL commun est `src/common/schema.sql`. Les tables sont `texts`, `articles`, `relations`, `chunks` et `versions`.

> Le DDL réel de P3, son chargeur et sa base ne sont pas présents dans le dépôt ni dans les branches P3/P5 inspectées. Les quatre premières tables sont définies dans `schema.sql`. La définition SQL de `versions` reste suspendue jusqu'à réception du DDL P3; aucune colonne existante n'est devinée. Voir `docs/contract_open_questions.md`.

## Conventions communes

- Les dates sont du texte ISO `YYYY-MM-DD`. `date_signed` est la date de signature; `jo_date` est la date de publication au Journal officiel; `valid_from` est la date d'entrée en vigueur, qui peut être différente de la signature.
- `rank_level` est un entier de 1 à 5 : 1 Constitution, 2 loi ou ordonnance, 3 décret, 4 arrêté, 5 circulaire. Une loi ou ordonnance existante reçoit le niveau 2.
- Les numéros d'article sont conservés en texte, par exemple `33`, `87 bis`, `73-1`. `sort_key` est la partie entière initiale utilisée pour le tri; plusieurs articles peuvent donc partager cette clé.
- `text_id` est en minuscules et stable, par exemple `loi-90-11` ou `ordonnance-96-21`.
- `article_id` vaut `<text_id>-art-<number>`, les espaces du numéro étant remplacés par des tirets. Exemples : `loi-90-11-art-33`, `loi-90-11-art-87-bis`, `loi-90-11-art-73-1`.
- Le statut d'article est `in_force` ou `repealed`. Une abrogation ne supprime pas l'article ni son historique.

## Table `texts`

Une ligne décrit un texte juridique.

| Colonne | Type | Règle / sens |
|---|---|---|
| `text_id` | TEXT, clé primaire | Identifiant canonique en minuscules |
| `type` | TEXT | Type du texte : `loi`, `ordonnance`, `decret`, `arrete`, `circulaire`, etc. |
| `number` | TEXT | Numéro du texte, par exemple `90-11` |
| `title` | TEXT, nullable | Titre complet |
| `date_signed` | TEXT, nullable | Date de signature ISO |
| `jo_number` | TEXT, nullable | Numéro du Journal officiel |
| `jo_date` | TEXT, nullable | Date de publication ISO |
| `source_url` | TEXT, nullable | Source du document |
| `rank_level` | INTEGER, 1–5 | Rang juridique selon la liste ci-dessus |
| `language` | TEXT, défaut `fr` | Langue du texte |
| `pdf_path` | TEXT, nullable | Chemin local du PDF source |

## Table `articles`

Une ligne contient le texte d'un article et ses métadonnées de structure. La version de référence P2 a un identifiant textuel stable.

| Colonne | Type | Règle / sens |
|---|---|---|
| `article_id` | TEXT, clé primaire | Convention d'identifiant ci-dessus |
| `text_id` | TEXT, clé étrangère vers `texts.text_id` | Texte parent |
| `number` | TEXT | Numéro affiché, conservé comme texte |
| `sort_key` | INTEGER | Partie entière initiale du numéro |
| `suffix` | TEXT, nullable | Suffixe éventuel (`bis`, `ter`, etc.) |
| `parent_title` | TEXT, nullable | Titre parent |
| `parent_chapter` | TEXT, nullable | Chapitre parent |
| `parent_section` | TEXT, nullable | Section parente |
| `content` | TEXT | Contenu intégral de l'article |
| `paragraphs` | TEXT | Liste JSON des alinéas |
| `status` | TEXT, défaut `in_force` | `in_force` ou `repealed` |
| `valid_from` | TEXT, nullable | Début ISO de validité lorsqu'il est connu |
| `valid_to` | TEXT, nullable | Fin ISO de validité; NULL si non bornée |
| `source_url` | TEXT, nullable | Provenance de l'article |

La paire (`text_id`, `number`) est unique.

## Table `relations`

Une relation orientée va de `source_id` vers `target_id`. Chaque identifiant désigne un `text_id` ou un `article_id`.

| Colonne | Type | Règle / sens |
|---|---|---|
| `relation_id` | INTEGER, clé primaire | Généré automatiquement |
| `source_id` | TEXT | Identifiant source |
| `target_id` | TEXT | Identifiant cible |
| `type` | TEXT | `modifies`, `repeals`, `applies`, `adds` ou `cites` |

## Table `chunks`

Une ligne est une unité indexable. En règle générale, un article donne un chunk; un article long peut être découpé par paragraphes tout en gardant le même `article_id`.

| Colonne | Type | Règle / sens |
|---|---|---|
| `chunk_id` | TEXT, clé primaire | `article_id` ou `article_id#partie` |
| `article_id` | TEXT, clé étrangère vers `articles.article_id` | Article cité par le chunk |
| `part` | INTEGER | Numéro de partie, à partir de 1 |
| `n_parts` | INTEGER | Nombre total de parties |
| `text` | TEXT | Texte montré au lecteur et au système de réponse |
| `text_for_embedding` | TEXT | Contexte et texte utilisés par la recherche sémantique |
| `n_chars` | INTEGER | Longueur du texte |
| `source_url` | TEXT, nullable | Provenance |

Le constructeur met à jour la table SQLite et préserve les JSON d'équipe sous `data/interim/`.

## Table `versions`

`versions` porte les rédactions successives et leurs périodes de validité. L'identifiant d'article est lié au contrat P2; `content`, `valid_from` et `valid_to` décrivent la rédaction et sa période. Les autres noms/types de colonnes doivent être repris du schéma P3 réellement utilisé dès qu'il est fourni; ils ne sont pas fixés par une supposition dans ce document.

La colonne additionnelle `verification_status` est nullable et, lorsqu'elle est renseignée, accepte uniquement :

- `verifie_jo_officiel`
- `verifie_copie_publiee`
- `a_verifier`

Les lignes P3 déjà enregistrées ne doivent pas être réécrites pour appliquer cette liste. La correspondance des anciennes valeurs CSV est en attente de confirmation P3.

## Ordre de construction

1. `python -m src.structuring.build_db` lit `src/common/schema.sql` et charge les articles P2 dans `data/db/qanun.db`.
2. `python -m src.structuring.chunks` construit la table `chunks` sans remplacer les JSON d'équipe.
3. Exécuter le chargeur de versions P3 sur la même base.
4. Exécuter `python -m src.structuring.validate`.
5. Exécuter `python -m src.versions.validate_versions`.

La commande d'ensemble est `python -m src.common.build_all`. Elle sauvegarde d'abord toute base existante sous `data/db/qanun.db.bak`; elle n'écrase pas un fichier `.bak` déjà présent.
