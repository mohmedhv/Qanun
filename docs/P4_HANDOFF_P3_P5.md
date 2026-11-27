État P3 Week 2 au 26 novembre 2026: module, base et chargeur intégrés. Résultats courants dans docs/P3_WEEK2_DELIVERY.md. Les observations antérieures ci-dessous sont historiques.

# Relais P4, P3 et P5 — état du dépôt

Mis à jour le 25 novembre 2026 après adoption du contrat P2 d'Ikram.

## Interface P4

Le service de recherche est `src/search/search_service.py`; il combine BM25, E5 et fusion RRF. Les résultats suivent désormais les noms du contrat :

`cite_id`, `article_id`, `number`, `text_id`, `chunk_id`, `text`, `source_url`, `score`, `version_id`, `valid_from`, `valid_to`, `version_status`, `version_record_available`, `version_verified`, `modifying_text_id`, `repealing_text_id`, `method`.

`number` est le numéro TEXT de la table `articles`. Les scores dépendent de la méthode et ne sont pas des probabilités de confiance.

## État de l'intégration P3

La base `data/db/qanun.db`, `src/versions/versions.py`, le chargeur P3 et `src/versions/validate_versions.py` ne sont pas présents dans ce dépôt au moment de ce relais. Le service P4 ne devine donc pas les colonnes de la table `versions`; sa recherche temporelle reste suspendue jusqu'à réception du vrai DDL et du module P3. Les résultats déjà consignés dans d'anciens rapports concernent un paquet antérieur et ne prouvent pas que ces fichiers sont présents ici.

P3 doit fournir le DDL réellement utilisé, le chargeur, le validateur et la correspondance des statuts de vérification sans réécrire les valeurs de lignes déjà stockées. Voir `docs/contract_open_questions.md`.

## Intégration P5

- L'interface P4 fournit `number`; l'invite P5 attend encore le champ de réponse `article_number`. P5 doit mapper ce champ ou modifier son schéma de réponse.
- P5 doit vérifier chaque citation avec les résultats réellement récupérés et s'assurer que tout extrait cité apparaît dans le texte retourné.
- `version_verified=False` ne constitue pas une validation juridique.

## Construction et vérifications

La commande commune est `python -m src.common.build_all`; elle exécute le chargeur P3 configuré par `QANUN_P3_VERSIONS_LOADER`. En son absence, elle affiche `FAILED` pour cette étape et continue avec les validateurs.

L'installation de `pytest` et de PyMuPDF est requise pour la suite de tests. Les résultats précédents consignés dans `docs/TEST_EVIDENCE.md` décrivent une autre distribution du dépôt et ne sont pas considérés comme une vérification de l'état courant.
