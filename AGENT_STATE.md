# GestureOS AI — état des agents

Date : 2026-09-24

## Objectif actuel
Collaboration Codex–Antigravity rétablie pour les revues ciblées en lecture seule. M9 logiciel terminé ; la suite dépendra des données réelles disponibles.

## Tâches terminées
- M1–M8 logiciels documentés dans `.agent/` ; M8 LCD 1602 logique compilé hors matériel.
- M9 implémenté localement et testé : petite rotation commune de l'accéléromètre et du gyroscope autour de Z, après split, identifiant parent conservé, scaler train réel figé.
- Suite Python complète : 102 tests OK le 2026-09-24. `git diff --check` OK.

## Tâches en attente
- Revue M9 ciblée reçue : `No concrete findings` sur `augment.py` et `train.py`. Voir `reports/m9-antigravity-review.md`.
- Commit M9 `786271e` effectué. Comparer sur captures réelles seulement lorsque le dataset sera suffisant.
- Comparaison ML réelle et tests physiques lorsque données et câblage seront disponibles.

## Décisions d'architecture
- L'augmentation est désactivée sans `--augmentation-config`.
- Copies exclusivement dans train ; validation/test inchangés ; RAW immuables.
- Rotation rigide de l'ensemble des mesures 3D pour préserver la cohérence des vecteurs ; durée inchangée. L'invariance du label reste à vérifier sur les captures réelles.
- Antigravity examine le dépôt en lecture seule avec `--mode plan --effort low`, et les outils `view_file`/`grep_search` demandés explicitement. Le mode headless refuse les commandes `run_command` non autorisées ; aucune approbation globale. Codex seul intègre les corrections.
- Préserver les modifications utilisateur déjà présentes dans `src/gestureos/capture.py`, `src/gestureos/dataset.py`, `tests/test_dataset.py` et `reports/hardware/`.

## Bugs connus et limites
- Aucun bug logiciel M9 connu après tests et revue ciblée. Cette revue ne couvrait que deux fichiers.
- Seulement trois captures valides `swipe_left` au dernier inventaire ; aucun score ML réel.
- Banc IMU long en échec (`imu_init`) ; LCD 16 broches non câblé ni testé physiquement.

## Dernier build / test réussi
`.venv/bin/python -m unittest discover -s tests` : 102 tests OK après revue Antigravity, 2026-09-24.

## Prochaine action recommandée
À la prochaine phase, reprendre la première tâche inachevée : vérifier la suffisance des captures réelles avant toute comparaison ML. Pour une nouvelle revue Antigravity, donner un périmètre court, `--mode plan --effort low`, demander `view_file`/`grep_search` seulement et contrôler la réponse ainsi que Git.

AGY RÉSOLU 2026-09-24 : `run_command` non autorisé était refusé en headless. `view_file` en mode plan a fonctionné et la revue M9 ciblée a répondu sans modifier le dépôt. Aucune permission globale changée.
