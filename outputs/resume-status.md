# Reprise GestureOS AI

**M7 logiciel terminé : sélection expérimentale des seuils UNKNOWN sur validation.**
La suite Python passe avec 100 tests après la revue Antigravity.
[Guide M7](threshold-selection-guide.md).

Trois captures réelles de gauche, sur deux séances, ont été revérifiées à la
reprise. Les données existantes sont intactes. Aucun modèle de gestes n’est
entraîné et aucun score ML n’est disponible. Le banc60s conservé est en échec ;
il reste à refaire, séparément des captures courtes qui sont valides.

La collecte reste possible avec le [kit hors ligne](COLLECTE_SANS_WIFI.md).
La politique d’inférence livrée rejette tout tant que les seuils ne sont pas
configurés ; aucune action matérielle n’est envoyée.

La recherche M7 exige des objectifs explicites et un modèle réel issu du
manifeste vérifié. Elle ne produit donc encore aucun seuil ni résultat ML
réel. Le test final reste réservé. La [revue Antigravity](../reports/m7-antigravity-review.md)
a été réalisée en lecture seule et ses remarques confirmées ont été traitées.
Les corrections de collecte déjà
présentes ont été conservées sans modification et restent non committées.
