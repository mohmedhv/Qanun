# P3 · Week 2 · Versions et hiérarchie

Livraison du 26 novembre 2026 pour FOUGHALI HOUSSEINE. Base de travail: Qanun-main(3).zip fourni. Périmètre appliqué: consignes Week 2 et corrections P3 figurant dans la capture de l’enseignant.

## Contrôle avant nettoyage

L’archive fournie contient 111 fichiers de travail et aucun qanun.db intégré. Son API P3 canonique manque, timeline est un placeholder et le service P4 bloque la lecture de versions. Il fallait intégrer les fonctions Week 2 réellement disponibles dans les livraisons précédentes.

Le chemin vérifié de l’extracteur de la précédente livraison est src/versions/extract_relations.py. Cet extracteur, son CSV p3_relations.csv, ses passages supplémentaires et ses trois tests d’ontologie sont exclus de cette distribution. Le chargeur et le validateur sont découplés de cet extracteur.

| Versions inspectées dans la précédente DB | Attribution et décision |
|---|---|
| 1–2, art. 73 | Historique principal Week 2, conservé |
| 3, art. 72 | Cas d’abrogation Week 2, conservé |
| 4–5, art. 87 | Historique principal Week 2, conservé |
| 6, art. 87 bis | Insertion puis abrogation Week 2, conservée |
| 7–8, art. 141 | Ajout explicitement introduit en Week 3, exclu |
| 9–10, art. 12 | Consolidation et recherche datée CDD ajoutées pendant la réparation d’intégration Week 2, conservées |
| 11, art. 12 bis | Article inséré, nécessaire au même scénario CDD, conservé |
| 12, art. 73-4 | Rédaction disponible depuis 1996 pour le recours après licenciement, conservée. La première rédaction de 1991 reste hors du versionnage disponible. |

Les numéros 7–12 ne constituent donc pas un ensemble exclusivement Week 3. Les ID conservés restent stables et les ID 7–8 restent vacants. Les références aux actes de 2017 restent dans l’inventaire Week 2 de toutes les modifications, même après exclusion du versionnage de 141.

La sauvegarde Qanun_Before_Week2_Cleanup_Backup.zip contient l’archive fournie et la base, les CSV/JSON ainsi que le code versions de la précédente distribution. La préparation a été effectuée dans un nouveau dossier.

Aucun fichier d’origine du ZIP équipe n’a été supprimé. src/graph/ontology.py et src/graph/build_graph.py existaient déjà dans le ZIP et sont conservés à l’identique comme code partagé. Les modules P1/P4/P5 et les PDF sources de l’équipe restent sous leur responsabilité. P3_Officially_Checked_Examples.csv reste identique octet pour octet au document Week 1 reçu. Aucun jeu Gold ajouté.

## Données et exigences Week 2

| Exigence | État |
|---|---|
| Liste des modifications | 79 opérations, JSON/CSV synchronisés et reliés au CSV source |
| Historiques principaux | Art. 73, 87 et 87 bis, avec toutes leurs rédactions recensées dans les actes du corpus. Art. 72 ajouté pour tester l’abrogation |
| Compléments d’intégration Week 2 | Art. 12, 12 bis et rédaction de 73-4 depuis 1996 |
| get_version(text_id, article_number, date=None) | Deux requêtes SQL, courante et historique. Date de fin inclusive. None en l’absence de version disponible |
| list_versions(text_id, article_number) | Historique enregistré, ordonné chronologiquement |
| rank_conflict(text_a, text_b) | Rang supérieur, égalité ou rang indéterminé. Échelle du contrat du projet |
| Intégration | DDL commun, chargeur transactionnel relançable, reconstruction et validateurs |
| Préservation P2 | 158 articles et 160 chunks. Corpus JSON des articles et chunks identique au ZIP fourni |

Base finale: **11 textes, 158 articles, 160 chunks, 10 versions sur 7 articles, 89 relations, 79 vérifications**.

Les 89 relations Week 2 proviennent des 79 opérations de l’inventaire et de dix liens vers la loi. Les insertions et abrogations ont une catégorie explicite. Les 32 relations de citation et le lien supplémentaire de texte d’application issus de l’extraction Week 3 sont exclus.

Les dates restent celles de la convention d’obligation à Alger utilisée dans les livraisons et les tests du projet, avec prise d’effet expresse de 87 bis. Le système représente les actes du corpus. Les sources et périodes restent visibles. La disponibilité d’une version n’atteste aucune recherche exhaustive de textes publiés après les actes recensés. Pour une date antérieure à 1996, l’historique de 73-4 n’est pas disponible dans l’API.

## Vérification des 79 opérations officielles

Les journaux ont été ouverts par source sur JORADP puis leurs pages opératoires examinées. Aucun téléchargement de masse. La vérification concerne l’identité du texte, la disposition modificatrice, la cible et l’opération. Les besoins de consolidation intégrale restent un champ distinct.

| Acte | Dispositions examinées | Pages imprimées |
|---|---|---|
| Loi 91-29 | Art. 2 et 3, modification de 73 et insertion de 73-1 à 73-6 | [2167–2168](https://www.joradp.dz/FTP/Jo-Francais/1991/F1991068.pdf#page=3) |
| Décret législatif 94-03 | Art. 1er et 2, insertion de 87 bis et effet exprès | [3](https://www.joradp.dz/FTP/Jo-Francais/1994/F1994020.pdf#page=3) |
| Décret législatif 94-09 | Art. 35, abrogation de 72 | [7](https://www.joradp.dz/FTP/Jo-Francais/1994/F1994034.pdf#page=7) |
| Ordonnance 96-21 | Art. 2 à 21, modifications et insertions. Art. 18 réorganise les sections et leurs articles | [6–8](https://www.joradp.dz/FTP/Jo-Francais/1996/F1996043.pdf#page=6) |
| Ordonnances 97-02 et 97-03 | Insertion de 52 bis/ter/quater et abrogation de 22 à 26 | [6–7](https://www.joradp.dz/FTP/Jo-Francais/1997/F1997003.pdf#page=6) |
| Loi 14-10 | Art. 89 et 90, modification de 87 et abrogation de 87 bis | [32](https://www.joradp.dz/FTP/jo-francais/2014/F2014078.pdf#page=32) |
| Ordonnance 15-01 | Art. 54, modification de 140 et 149 | [16](https://www.joradp.dz/FTP/Jo-Francais/2015/F2015040.pdf#page=16) |
| Loi 17-11 | Art. 99, quatorze articles visés | [44–46](https://www.joradp.dz/FTP/jo-francais/2017/F2017076.pdf#page=44) |
| Loi 22-16 | Art. 2 et 3, sept insertions 56 bis et complément de 64 | [10–11](https://www.joradp.dz/FTP/jo-francais/2022/F2022049.pdf#page=10) |

Les **28 lignes demandées** sont toutes marquées VERIFIED_OFFICIAL_JO après contrôle. Les 51 autres lignes ont également été confrontées aux trois sources restantes. **Bilan source de la liste reçue: 79 vérifiées sur JO, zéro à vérifier.** Le statut initial des 28 est conservé. Aucune restauration de valeurs antérieures ne supprime un contrôle acquis qui relève de Week 2.

Les champs before_week2_* retiennent les valeurs exactes du CSV reçu, dont 28 A_VERIFIER_SOURCE_OFFICIELLE. Les champs previous_* issus de la précédente livraison sont conservés à titre de provenance. Ils ne sont pas utilisés pour inventer un état manquant ni pour annuler la vérification exigée. Les pages anciennes de compilation sont conservées en historique, tandis que pdf_page contient maintenant la page imprimée du JO. Le lien #page désigne l’index PDF humain à partir de 1, qui diffère des pages imprimées en 1991.

### Résolution 28 / 19 / 16 pour P1 et P4

Le CSV reçu comptait **28 sources officielles à contrôler**. Les documents historiques mentionnaient **19 rédactions à revoir**, soit quatorze cibles de 2017 et cinq de 1996. L’intersection est de quatorze opérations. Les cinq autres cas textuels concernaient 1996 et n’appartenaient pas aux 28.

Trois rédactions de 2017 ont été retranscrites dans la reprise Week 2, ramenant le drapeau textuel à 16. Les corrections ultérieures ont consolidé le 12 de 1996 et signalé l’extrait incomplet de 73-4 de 1991, laissant 16 points textuels. Ces points sont extérieurs aux trois historiques principaux. Le contrôle de la référence de l’opération et la consolidation complète de toutes les rédactions sont deux champs distincts.

L’audit --strict contrôle les sources et les métadonnées demandées en Week 2. Les drapeaux de consolidation de l’inventaire continuent d’être affichés. La commande ne requiert plus de signature humaine sur les 79 opérations, condition ajoutée dans l’assistance précédente et absente de la demande enseignant.

## Statuts visibles et lien avec le CSV

La table amendment_verification contient csv_row, l’acte, la cible et la disposition, original_status, csv_status, verification_status, source_url, source_page, verification_note et needs_textual_review. Les valeurs contractuelles sont verifie_jo_officiel, verifie_copie_publiee, a_verifier. Les 28 initialement à vérifier sont retrouvables avec original_status.

versions.verification_status reprend le contrôle de la modification produisant la version. Une version initiale sans ligne modificatrice correspondante conserve NULL. La ligne de vérification d’une abrogation est liée par son texte abrogeant et sa cible. La reconstruction recharge le CSV et conserve le statut initial.

## Cinq références P4

Les quatre CSV de eval/p4 restent synchronisés. Q001, Q005, Q009 et Q010 sont confirmées au texte original de 1990, avec la page de Q010 corrigée à 490. Q008 est contrôlée et classée CORRECTION_REQUIRED car sa référence est historique et abrogée. Les preuves et le résultat sont renseignés au nom de **Codex — revue assistée pour FOUGHALI HOUSSEINE**. Aucun acte de lecture personnel du responsable humain n’est prétendu.

Les quinze autres références du benchmark ne font pas partie des cinq contre-lectures. Le jeu enseignant de dix questions dans eval/questions.csv est préservé à l’identique du ZIP reçu. La capture attribue la vérification de l’ensemble des dix questions à Assia/P4. P3 lui transmet les résultats des cinq contrôles et le signalement de Q008. Aucun changement du modèle Groq ni collecte de masse ne relève de cette intervention P3.

## Commandes et résultats réellement exécutés

Depuis le dossier Qanun, utiliser Python avec les dépendances du projet pour les modules concernés.

```powershell
python -m pytest -q
python -m src.structure.validate_articles --text loi-90-11 --expect 158
python -m src.versions.validate_versions
python -m src.versions.audit_amendments --strict
python -m src.search.smoke_test --bm25-only
```

Pour reconstruire sans écraser la base livrée:

```powershell
python -m src.versions.rebuild_db --output data/db/controle_week2.db
```

La construction commune python -m src.common.build_all suit le contrat et sauvegarde la base existante. Le chargeur par défaut est src.versions.load_versions.

| Contrôle exécuté sous Linux | Résultat |
|---|---|
| Suite complète après exclusion des tests spécifiques Week 3 | 42 tests réussis |
| Huit tests ciblés P3/P4 précédemment défaillants | Réussis, inclus dans la suite |
| Construction commune et validateurs P2/P3 | Réussis |
| Validateur des articles, --expect 158 | 0 erreur, 0 avertissement |
| Audit sources --strict | Réussi |
| Recherche BM25, changement temporel, exclusion des articles suivis abrogés | Réussis |
| Intégrité SQLite, clés étrangères, statuts CSV/DB et fermeture des connexions | Réussis |
| Corpus articles/chunks et exemples Week 1 comparés au ZIP reçu | Identiques |

Les deux fonctions de la réconciliation 2017 portant sur l’inventaire restent testées. Seule la fonction test_article_141_wording_at_transition est retirée de ce fichier mixte. Les trois tests de test_p3_relations.py sont spécifiques à l’export d’ontologie exclu. Le test de fermeture explicite des connexions garde la correction WinError 32 précédemment validée par l’utilisateur. Cette nouvelle distribution est testée sous Linux. Aucun nouveau résultat Windows n’est revendiqué.

L’interface Streamlit et les évaluations LLM gardent l’état fourni par leurs propriétaires. Aucun test d’inférence E5 réelle ni nouvelle mesure de précision/rappel n’a été exécuté. Le scénario hybride de la suite utilise le double de test existant.

## Relais technique P4 et P1

```python
from src.versions.versions import get_version, list_versions, rank_conflict

version = get_version("loi-90-11", "73", "1991-12-26")
history = list_versions("loi-90-11", "87")
```

Le résultat est un dictionnaire avec contenu, paragraphes, identifiants, source et intervalle. None signifie qu’aucune version documentée ne correspond à la date. Les bornes valid_to sont inclusives et les articles suivis abrogés sont exclus des résultats actuels. La recherche sans date conserve aussi le corpus provisoire P2 pour les autres articles. Les métadonnées signalent les dispositions de ce corpus dont l’abrogation est documentée.

P1 peut intégrer les fichiers listés dans P3_WEEK2_FILES.csv. P4 peut reprendre la correction de Q008 et exécuter ses tests temporels. Le CSV original des exemples Week 1 et tous les fichiers des autres phases restent présents.
