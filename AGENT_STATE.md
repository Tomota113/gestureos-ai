# GestureOS AI — état des agents

Date : 2026-09-24

## Objectif actuel
Terminer M9 : augmentation IMU optionnelle, limitée au train, avec provenance des copies, sans entraîner un vrai modèle ni toucher aux captures RAW. Codex coordonne ; revue Antigravity ciblée en lecture seule.

## Tâches terminées
- M1–M8 logiciels documentés dans `.agent/` ; M8 LCD 1602 logique compilé hors matériel.
- M9 implémenté localement et testé : petite rotation commune de l'accéléromètre et du gyroscope autour de Z, après split, identifiant parent conservé, scaler train réel figé.
- Suite Python complète : 102 tests OK le 2026-09-24. `git diff --check` OK.

## Tâches en attente
- Revue Antigravity M9 restée sans sortie à cause d’une permission de commande refusée en mode headless. Reprendre seulement avec une autorisation étroite ; aucune conclusion de quota.
- Commit M9 `786271e` effectué. Comparer sur captures réelles seulement lorsque le dataset sera suffisant.
- Comparaison ML réelle et tests physiques lorsque données et câblage seront disponibles.

## Décisions d'architecture
- L'augmentation est désactivée sans `--augmentation-config`.
- Copies exclusivement dans train ; validation/test inchangés ; RAW immuables.
- Rotation rigide de l'ensemble des mesures 3D pour préserver la cohérence des vecteurs ; durée inchangée. L'invariance du label reste à vérifier sur les captures réelles.
- Antigravity peut examiner le dépôt en lecture seule, sans modifier aucun fichier ; Codex seul intègre les corrections. Cette limite provient de `AGENTS.md`.
- Préserver les modifications utilisateur déjà présentes dans `src/gestureos/capture.py`, `src/gestureos/dataset.py`, `tests/test_dataset.py` et `reports/hardware/`.

## Bugs connus et limites
- Aucun bug logiciel M9 connu après tests ; revue indépendante non obtenue (permission CLI).
- Seulement trois captures valides `swipe_left` au dernier inventaire ; aucun score ML réel.
- Banc IMU long en échec (`imu_init`) ; LCD 16 broches non câblé ni testé physiquement.

## Dernier build / test réussi
`.venv/bin/python -m unittest discover -s tests` : 102 tests OK, 2026-09-24.

## Prochaine action recommandée
À la prochaine phase, reprendre la première tâche inachevée : vérifier si une revue Antigravity en lecture seule peut être autorisée étroitement ; ensuite préparer la comparaison avec/sans augmentation seulement lorsque le vrai dataset sera suffisant. Toute nouvelle revue Antigravity doit disposer d’une autorisation de commande étroite, sans édition des fichiers.
