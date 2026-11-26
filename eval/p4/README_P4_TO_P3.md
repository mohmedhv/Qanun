> État actuel: les cinq contre-lectures demandées sont renseignées par Codex en assistance de FOUGHALI HOUSSEINE. Quatre références sont confirmées au texte original, Q008 nécessite une correction. Les quinze autres questions restent hors de cette revue de cinq références. L’ancienne colonne supplémentaire human_confirmation_status a été retirée. Le protocole reçu et ses états historiques sont conservés ci-dessous.

# P4 → P3 | Questions, références et sign-off (25 novembre 2026)

## À transmettre

- `questions.csv` : les **20 questions originales du benchmark P4**, 10 `dev` et 10 `test`, avec `expected_article_number`, `expected_cite_id`, `source_url`, `independent_second_check`.
- `P4_P3_legal_references_20.csv` : tableau unique question → article de loi → `cite_id` → source JORADP → page imprimée → état de vérification.
- `official_sources.csv` : lien officiel *enregistré* vers le Journal officiel n°17 du 25 avril 1990, pages imprimées 488–491. Le lien n'a pas été retesté en ligne pour cet envoi.
- `reference_audit_1990.csv` : audit de premier niveau des correspondances avec la **version originale de 1990**, plus cases de validation indépendante.
- `reference_review.md` : contenu extrait par P2 + formulaire de revue, question par question.
- `P4_P3_signoff_status.csv` : état actuel du sign-off pour permettre à P3 de documenter la revue réelle.
- `REFERENCE_AUDIT_README.md` : protocole et limites de la vérification.

## Statut au moment de l'envoi

- Questions : **20/20** présentes ; 10 dev / 10 test.
- Références attribuées : **20/20**, **une référence attendue par question** (ce sont des annotations de recherche à confirmer, pas une validation juridique définitive).
- Contrôle de premier niveau contre la version **initiale (1990)** : `MATCHES_ORIGINAL_ARTICLE` dans le registre d'audit pour 20/20.
- **Sign-off indépendant documenté : 0/20 CONFIRMED ; 20/20 PENDING.** Les champs relecteur/date sont vides ; ne pas marquer CONFIRMED avant la vérification effective par P2/P3.
- La loi a été modifiée après 1990. Les pages et textes initiaux ne prouvent **pas** la validité de la version actuelle ou d'une date historique particulière. P3 doit confronter les modifications pertinentes et relever les sources officielles des versions concernées.

## Travail demandé à P3

Comparer chaque référence à la publication officielle et, si besoin, aux amendements en vigueur selon la date de la question. Renseigner pour chaque ligne le nom de l'examinateur, la date, le statut réel (`CONFIRMED` ou `CORRECTION_REQUIRED`) et une note. Retourner le tableau annoté à P4 et P1. Ne jamais remplacer des statuts PENDING sans une vérification humaine.

## ملاحظة بالعربية

الحزمة تحتوي على الأسئلة الـ20 والمادة القانونية المرجعية لكل سؤال، ورابط الجريدة الرسمية وصفحاتها وفق بيانات P4. **التوقيع المستقل ما زال 0/20**، لذلك المطلوب من P3 تدقيق المراجع وتسجيل اسمه وتاريخ المراجعة والنتيجة الحقيقية. الربط بالنص الأصلي لسنة 1990 لا يعني أن المادة ما زالت نافذة بصيغتها القديمة.

**مصدر هذه الحزمة:** ملفات تسليم P4 المحلية (`eval/questions.csv`, `eval/reference_audit_1990.csv`, `eval/reference_review.md`) المتاحة ضمن أرشيف العمل السابق. وهي مجموعة P4 ذات 20 سؤالًا، **وليست** أسئلة الأستاذ الأصلية العشرة.
