# Inventaire de migration du contrat de données

Inventaire établi le 25 novembre 2026 après fusion de `origin/main` dans la branche de travail. La décision retenue est le contrat d'Ikram (P2) : `data/db/qanun.db`, tables `texts`, `articles`, `relations`, `chunks` et `versions`.

## Ancien schéma encore présent

| Fichier | Noms ou usages à retirer / adapter |
|---|---|
| `src/common/schema.sql` | `articles.article_number`, `version_no`, `modified_by_text_id`; relations `from_text_id`, `to_text_id`, `to_article_number`, `relation_type`; anciennes clés et index. Ce fichier est encore lu par `init_db.py`. |
| `src/common/init_db.py` | Valeur par défaut `data/db/qanun.sqlite3`. |
| `src/structure/validate_articles.py` | Colonnes `article_number`, `version_no`, `modified_by_text_id`; chemin par défaut `data/db/qanun.sqlite3`. |
| `src/graph/build_graph.py` | Lit `from_text_id`, `to_text_id`, `relation_type`, `to_article_number`. |
| `src/search/bm25_baseline.py` | Ouvre `data/db/qanun.sqlite3`; ce baseline est remplacé par la recherche P4. |
| `config.example.yaml` | `paths.db: data/db/qanun.sqlite3`. |
| `docs/data_contract.md` | Décrit `article_number` et `modified_by_text_id`; ne documente que trois tables et présente l'ancien schéma comme source. |
| `docs/data_contract_proposal.md` | Proposition P2 déjà alignée sur `number`, `sort_key`, `article_id`, `source_id`, `target_id`, `type`; sa section provisoire P3 cite encore `version_no`. |
| `src/search/search_service.py` | À l'inventaire, l'API P4 et sa requête SQL employaient `article_number`. Étape 4 : l'API expose `number`; sa lecture SQL de P3 reste suspendue jusqu'à réception du vrai schéma. |
| `src/search/smoke_test.py`, `tests/test_search_p4.py`, `tests/test_search_p4_integration.py`, `eval/run_eval.py`, `docs/P4_HANDOFF_P3_P5.md` | À l'inventaire, les tests et le relais P4/P5 exposaient `article_number`. Étape 4 : les tests, l'évaluation et le relais ont été alignés sur la clé de sortie `number`. |
| `src/rag/prompts.py` | `article_number` reste un champ du JSON de réponse destiné à l'utilisateur; ce n'est pas une colonne SQLite. |
| `src/versions/timeline.py` | Le paramètre de recherche est nommé `article_number`; le fichier ne contient qu'une interface provisoire. |
| `src/collect/split_issue.py`, `tests/test_collect.py` | Corrigé le 26/11/2026 : le producteur et son test utilisent des `text_id` en minuscules à préfixe complet (`loi-90-11`, `ordonnance-26-01`, `decret-executif-26-253`, `arrete-2026-05-07-1`) et le type `decret` ; la distinction décret exécutif / présidentiel n'est que dans l'identifiant. |

## Éléments déjà alignés sur P2

| Fichier | Éléments présents |
|---|---|
| `src/structuring/build_db.py` | Base `data/db/qanun.db`; `articles.article_id` textuel, `number`, `sort_key`; relations `source_id`, `target_id`, `type`. Le schéma est encore codé en chaîne dans ce module. |
| `src/structuring/chunks.py` | Utilise `article_id`, `number`, `sort_key` et les colonnes de `chunks`. L'ancien comportement réécrivait aussi `data/interim/chunks.json`; il a été retiré pour préserver les données d'équipe. |
| `src/structuring/validate.py` | Vérifie `number` et `sort_key` dans `articles`. |
| `docs/data_contract_proposal.md` | Définit les tables P2 et le format d'identifiants comme `loi-90-11-art-33`. |
| `data/interim/articles.json`, `data/interim/articles_ar.json`, `data/interim/chunks.json` | Données P2 contenant des numéros et clés de tri. Ces fichiers ne seront ni supprimés ni réécrits. |

## État P3 observé

`data/db/` ne contient pas de base SQLite, seulement `.gitkeep`. `src/versions/` contient `hierarchy.py` et une interface provisoire `timeline.py`, mais ni `versions.py`, ni chargeur, ni `validate_versions.py`. Les branches `origin/p3-week1` et `origin/p5/week2-rag-pipeline` ne fournissent dans leur arborescence que les CSV/notes P3 et le relais P4/P5, sans schéma de table `versions` ni base SQLite. Les colonnes attendues par les tests P4 ne remplacent pas la définition réelle demandée par P3.

Cette absence empêche d'inventorier les vraies colonnes de `versions`. Elle est consignée dans `docs/contract_open_questions.md`; aucune colonne P3 n'est devinée ici.
