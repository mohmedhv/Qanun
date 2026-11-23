# Évaluation du filtre de pertinence UpGrowth — état des annotations

Les 30 textes échantillonnés dans `eval/filter_labels.csv` ont actuellement le champ `relevant` vide. Il n'existe donc pas encore de matrice de confusion mesurée. Les cellules ci-dessous restent explicitement non calculées; elles ne valent pas zéro.

| Seuil du filtre | Textes étiquetés | TP | FP | FN | TN | Précision | Rappel |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 0/30 | n/a | n/a | n/a | n/a | n/a | n/a |

## Travail requis

- Attribuer `oui` ou `non` à `relevant` après lecture humaine des 30 textes.
- Garder l'identifiant, le titre et les extraits inchangés; ne pas déduire l'étiquette du score du filtre.
- Relancer `python -m eval.filter_eval --threshold 3` après annotation. Le script exige au moins 20 étiquettes et écrit alors la matrice de confusion, précision, rappel et les erreurs dans ce fichier.
- Faire relire au moins cinq étiquettes par une seconde personne, comme demandé par le script.
