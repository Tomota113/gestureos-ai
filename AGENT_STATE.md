# GestureOS AI — état de reprise des agents

Mis à jour : 2026-09-25

## Objectif actuel
M11 logiciel terminé. Le prochain jalon autonome est la segmentation temporelle des gestes ; l'entraînement ML réel et les essais physiques restent conditionnés par les captures et le câblage.

## Tâches terminées
- M1–M9 : acquisition et collecte IMU, split, prétraitement, baselines, inférence/rejet, seuils expérimentaux, présentation LCD et augmentation train-only. Voir `.agent/decisions.md`.
- M10 modes et macros intégré dans `7268b87` ; tests C++ natifs, 102 tests Python et deux builds PlatformIO réussis le 2026-09-25. Rapport : `reports/m10-software-validation.md`.
- M11 menu LCD logique intégré dans `b4f5665` : RUN, DATASET, TEST, MODES, SETTINGS, CALIBRATE, STATS et ABOUT ; haut/bas, pression, gauche ; `lcd_ui::Frame` 16×2. La sélection ouvre seulement une page logique. Test natif, 102 tests Python et builds PlatformIO `esp32dev`/`dataset` réussis. Rapport : `reports/m11-menu-software-tests.md`. Aucun flash ni essai matériel.
- Inventaire RAW en lecture seule le 2026-09-25 : 3 captures valides, 0 rejetée, toutes `swipe_left`, sujet `user01` sur 2 séances. Split session/sujet bloqué faute de 3 groupes indépendants.

## Première tâche inachevée
Concevoir un jalon logiciel borné pour segmenter un flux IMU continu en fenêtres candidates (`gesture_engine.*`) sans faire passer les simulations pour des mesures réelles. Lire d'abord le brief et les contrats firmware existants. Définir la détection de début/fin, les bornes mémoire et les tests hors matériel ; ne pas brancher de modèle non entraîné ni déclencher d'action physique.

## Travaux dépendants de l'utilisateur
- Recueillir des captures réelles de plusieurs labels et groupes indépendants ; comparer les baselines avec/sans augmentation sur validation seulement quand le dataset le permet. Test final réservé, aucun score réel actuellement.
- Après câblage par l'utilisateur : refaire le banc MPU6050 de 60 s (dernier rapport `imu_init` en échec), identifier le LCD 1602 à 16 broches et tester les niveaux et broches. Aucun flash automatique.

## Décisions et limites
- RAW, pending et notes de séance immuables. Préserver les modifications utilisateur non commitées : `src/gestureos/capture.py`, `src/gestureos/dataset.py`, `tests/test_dataset.py` et `reports/hardware/`.
- M10 émet des intentions logicielles ; il ne prouve ni calibration des scores ni autorisation d'action physique. Tout futur adaptateur devra appliquer `action_authorized`.
- Le menu M11 n'a ni pilote LCD, ni joystick, ni bouton, ni broches. Il ne lance aucune capture ou commande matérielle.
- Si Codex s'arrête faute de quota, l'utilisateur peut donner à Antigravity le prompt général dans `ANTIGRAVITY_HANDOFF.md`. Antigravity doit faire ses propres tests, contrôle du diff et checkpoint ; Codex ne répète pas ses vérifications pour économiser son quota. Pas d'édition concurrente du même fichier.

## Dernière validation et quota
2026-09-25 : test C++ menu réussi avec `-std=c++11 -Wall -Wextra -Werror`, 102 tests Python OK, deux builds PlatformIO SUCCESS. Dernier contrôle officiel Codex : 14 % utilisés sur 5 h, 82 % sur la semaine ; aucun reset consommé. Ce chiffre peut changer.

## Protocole de continuité
Lire ce fichier en premier à chaque « continue », puis `.agent/PROJECT_STATE.md`, `.agent/NEXT_ACTION.md`, `.agent/CHECKPOINT.md`, `.agent/decisions.md`, le statut Git et les cinq derniers commits. Mettre `AGENT_STATE.md` à jour après chaque tâche majeure et avant tout arrêt, même après échec d'outil ou quota indisponible. Indiquer résultats vérifiés, fichiers modifiés, blocages et première action réalisable. Ne jamais déduire un quota épuisé d'une erreur réseau, d'authentification ou de permission.
