# GestureOS AI — état de reprise des agents

Mis à jour : 2026-09-24

## Objectif actuel
Le jalon logiciel M9 est terminé. Reprendre le prochain travail logiciel utile sans prétendre disposer d'un modèle de gestes validé ; vérifier les captures réelles avant toute comparaison ML. Les essais physiques attendent les branchements de l'utilisateur.

## Dernières tâches terminées
- M9 : augmentation IMU optionnelle par petite rotation commune de l'accélération et du gyroscope, après le split et uniquement dans train. Provenance parent conservée, scaler des captures train originales figé. Commit `786271e`.
- Collaboration Antigravity rétablie : revue ciblée en lecture seule de `augment.py` et `train.py`, réponse « No concrete findings ». `--mode plan --effort low` avec `view_file` a fonctionné sans permission globale ajoutée. Diagnostic et limites : `reports/m9-antigravity-review.md`, commit `3592c90`.
- Suite Python complète après cette revue : 102 tests OK. Ancien M8 : tests C++ LCD et deux compilations ESP32 réussis, sans flash ni test physique.

## Première tâche inachevée et suite
1. Faire un inventaire en lecture seule des captures réelles et des groupes/labels, avant toute expérience ML. Au dernier inventaire : seulement trois captures valides `swipe_left` sur deux séances ; cette information peut avoir changé.
2. Si les données deviennent suffisantes, comparer baseline et augmentation sur le même split, validation seulement ; conserver le test final réservé. Ne jamais présenter les fixtures ou simulations comme une performance réelle.
3. Quand l'utilisateur aura câblé le matériel : refaire le banc IMU de 60 secondes (dernier rapport en échec `imu_init`), puis identifier et tester le LCD 1602 à 16 broches. Aucun flash automatique.

## Décisions et limites
- RAW immuables ; aucune augmentation dans validation ou test. L'invariance des labels après rotation reste une hypothèse à mesurer.
- Antigravity : tâche et fichiers autorisés définis avant chaque délégation ; revue en lecture seule, sans édition concurrente. En mode sans interface, demander `view_file`/`grep_search` et éviter `run_command` non autorisé. Vérifier la réponse finale, le statut Git et les tests. Ne pas utiliser l'approbation globale automatique.
- Préserver les changements utilisateur préexistants non commités : `src/gestureos/capture.py`, `src/gestureos/dataset.py`, `tests/test_dataset.py`, ainsi que `reports/hardware/` non suivi.
- Aucun modèle, score ML réel, seuil opérationnel ou validation matérielle complète à annoncer. Le rendu LCD logiciel n'est pas encore un affichage physique.

## Dernière validation et état Git
`.venv/bin/python -m unittest discover -s tests` : 102 tests OK le 2026-09-24 après la revue Antigravity. Dernier commit de revue Antigravity : `3592c90` ; l’état de reprise est suivi par un commit de documentation distinct. Les seules modifications de code non commitées listées ci-dessus préexistaient ; ne pas les intégrer par erreur.

## Protocole de continuité
Lire ce fichier en premier à chaque « continue », puis `.agent/PROJECT_STATE.md`, `.agent/NEXT_ACTION.md`, `.agent/CHECKPOINT.md`, `.agent/decisions.md`, le statut Git et les cinq derniers commits. **Mettre `AGENT_STATE.md` à jour après chaque tâche majeure terminée et avant tout arrêt**, y compris si un outil échoue ou si le quota devient indisponible. Noter exactement le dernier résultat vérifié, les travaux incomplets, les fichiers modifiés, les blocages et la première action réalisable. Ne jamais déduire un quota épuisé d'une erreur réseau, d'authentification ou de permission.
