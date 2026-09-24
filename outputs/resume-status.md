# Reprise GestureOS AI

**M6 logiciel terminé : inférence PC et rejet UNKNOWN. 87 tests réussis.**
[Guide d’inférence](inference-guide.md).

Trois captures réelles de gauche, sur deux séances, ont été revérifiées à la
reprise. Les données existantes sont intactes. Aucun modèle de gestes n’est
entraîné et aucun score ML n’est disponible. Le banc60s conservé est en échec ;
il reste à refaire, séparément des captures courtes qui sont valides.

La collecte reste possible avec le [kit hors ligne](COLLECTE_SANS_WIFI.md).
La politique d’inférence livrée rejette tout tant que les seuils ne sont pas
configurés ; aucune action matérielle n’est envoyée.

Prochaine étape logicielle : sélectionner et évaluer les seuils sur validation,
en protégeant le test final. Les corrections de collecte déjà présentes ont
été conservées sans modification et restent non committées.
