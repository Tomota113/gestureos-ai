# GestureOS AI — état de reprise des agents

Mis à jour : 2026-09-25

## Objectif actuel
Les jalons logiciels M1–M12 sont préparés. Prochaine progression utile : collecte et caractérisation physiques lorsque l'utilisateur câblera le matériel, puis comparaison ML réelle après obtention d'un dataset suffisant. Aucun modèle gestuel réel ou seuil physique n'est validé.

## Tâches terminées
- M1–M9 : acquisition, collecte, split, prétraitement, baselines, inférence/rejet, seuils expérimentaux, rendu LCD et augmentation train-only. Voir `.agent/decisions.md`.
- M10 modes et macros : commit `7268b87`, rapport `reports/m10-software-validation.md`.
- M11 menu LCD 16×2 logique : commit `b4f5665`, rapport `reports/m11-menu-software-tests.md`. Huit entrées ; la sélection ouvre une page logique, sans action matérielle.
- M12 segmentation candidate IMU : commit `2d6dcbb`, rapport `reports/m12-gesture-segmentation-tests.md`. Début/fin par énergie et hystérésis avec seuils explicitement fournis, fenêtre bornée à 256 points, préambule de 32 points maximum, contrôle des timestamps et des valeurs. Ni modèle, ni classe, ni action. Test C++ natif et builds PlatformIO `esp32dev`/`dataset` réussis. Aucun flash ni mesure physique.
- Dernière suite Python complète au M11 : 102 tests OK. Aucun fichier Python modifié dans M12.
- Inventaire RAW en lecture seule le 2026-09-25 : 3 captures valides, 0 rejetée, toutes `swipe_left`, sujet `user01` sur 2 séances. Splits session/sujet bloqués faute de 3 groupes indépendants.

## Première tâche inachevée
Pour un prochain jalon logiciel autonome, préparer un outil de replay en lecture seule des flux IMU déjà enregistrés afin d'exercer `gesture_engine` sans inventer de calibration ni publier de taux de reconnaissance. Sinon attendre les nouvelles captures et le câblage de l'utilisateur pour caractériser bruit, pertes, seuils, durée et latence réels. Ne pas connecter les intentions M10 à des broches avant une politique d'autorisation validée.

## Travaux dépendants de l'utilisateur
- Obtenir plusieurs gestes et au moins 3 groupes indépendants avant split/comparaison ML ; garder le test final réservé.
- Après câblage : répéter le banc MPU6050 de 60 s (dernier rapport en échec `imu_init`), identifier les niveaux et broches du LCD 1602 16 broches. Aucun flash automatique.

## Décisions et limites
- RAW, pending et notes de séance immuables. Préserver les modifications utilisateur non commitées : `src/gestureos/capture.py`, `src/gestureos/dataset.py`, `tests/test_dataset.py` et `reports/hardware/`.
- M10 ne garantit pas calibration/autorisation d'action ; l'adaptateur matériel futur devra appliquer `action_authorized`.
- M11 et M12 sont des couches logicielles compilées, non branchées au LCD/IMU réel. Les seuils et valeurs de tests M12 sont synthétiques, pas des réglages MPU6050.
- Si Codex n'a plus de quota, l'utilisateur peut donner à Antigravity le prompt général `ANTIGRAVITY_HANDOFF.md`. Antigravity vérifie lui-même ses changements ; Codex ne répète pas ces vérifications pour économiser le quota. Pas d'édition concurrente.

## Dernière validation et quota
2026-09-25 : M12 test natif C++11 avec `-Wall -Wextra -Werror` réussi ; deux builds PlatformIO SUCCESS. Dernière suite Python : 102 OK au M11. Dernier contrôle officiel Codex : 22 % utilisés sur 5 h et 83 % sur la semaine ; aucun reset consommé. Valeurs susceptibles de changer.

## Protocole de continuité
Lire ce fichier en premier à chaque « continue », puis `.agent/PROJECT_STATE.md`, `.agent/NEXT_ACTION.md`, `.agent/CHECKPOINT.md`, `.agent/decisions.md`, le statut Git et les cinq derniers commits. Mettre `AGENT_STATE.md` à jour après chaque tâche majeure et avant tout arrêt, même après échec d'outil ou quota indisponible. Indiquer résultats vérifiés, fichiers modifiés, blocages et première action réalisable. Ne jamais déduire un quota épuisé d'une erreur réseau, d'authentification ou de permission.
