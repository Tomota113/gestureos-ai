# GestureOS AI

Contrôleur gestuel TinyML sur ESP32 + MPU6050, avec interface LCD 1602.
L'objectif est une reconnaissance locale fiable, avec rejet UNKNOWN et modes
ROBOT, SMART CONTROL, PRESENTATION, GAME, MACRO et CUSTOM.

**État réel : collecte physique commencée, logiciels de collecte et d’inférence PC prêts.**
Trois captures MPU6050 réelles de gauche ont été revérifiées à la reprise M6.
Le rapport de banc de 60 s conservé est en échec ; sa validation reste à refaire.
La carte répond au bootloader : ESP32-D0WDQ6 révision 1, Flash 4 Mo, CP2102.
Les deux firmwares compilent ; les tests C++ natifs du précédent jalon passent.
La suite Python passe : **98 tests**. Elle couvre aussi la sélection M7 sur scores analytiques, sans
mesure ML réelle.
Aucun modèle de gestes entraîné, score de précision ou test d’actionneur n’existe encore.

Le chargeur, les splits par session/sujet et le prétraitement à 64 caractéristiques
avec normalisation ajustée sur le train sont également prêts.
Le lanceur RF/SVM/MLP et ses journaux d’expériences sont prêts, avec comparaison
sur validation et test final réservé. Aucun entraînement réel n’a été lancé.
M6 ajoute le diagnostic sur capture, les scores RF/SVM/MLP et le rejet UNKNOWN,
avec une politique non configurée par défaut et aucune action matérielle.
M7 ajoute la recherche de seuils sur validation, bloquée sans contraintes
explicites ou sans données et modèle réels adéquats.

## Lire en premier

- [Inférence PC et rejet UNKNOWN](outputs/inference-guide.md)
- [Sélection des seuils UNKNOWN](outputs/threshold-selection-guide.md)
- [Collecter tes gestes sans Wi-Fi](outputs/COLLECTE_SANS_WIFI.md)
- Lanceur local : `bash outputs/LANCER_COLLECTE.sh` (premier test matériel à réaliser selon le guide).
- [Baselines RF/SVM/MLP et expériences](outputs/baselines-guide.md)
- [Prétraitement et caractéristiques](outputs/preprocessing-guide.md)
- [Préparation et partitions du dataset](outputs/dataset-preparation-guide.md)
- [Audit et architecture proposée](outputs/phase-0-audit.md)
- [Premier test : câblage, commandes, critères](outputs/first-mpu6050-test.md)
- [Collecte de gestes : logiciel prêt et procédure future](outputs/dataset-collection-guide.md)
- [Architecture évolutive](docs/architecture.md)
- [Revue Antigravity et décisions](docs/antigravity-review.md)
- [État de reprise](.agent/PROJECT_STATE.md)
- [Prochaine action exacte](.agent/NEXT_ACTION.md)
- Brief et protocole complets : `docs/requirements/`.

## Installation minimale déjà effectuée

L'environnement `.venv` utilise le Python système 3.14.4, pyserial 3.5 et
le paquet local `gestureos` 0.1.0 installé en mode éditable.
Il est séparé du Python interne de PlatformIO. Pour le recréer s'il manque :

```bash
/usr/bin/python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

PlatformIO 6.2.0 est installé. Le projet fixe `espressif32@7.0.1`, dont le
framework présent est Arduino ESP32 2.0.17. L’option ML est installée dans `.venv`
(scikit-learn 1.9.1, dépendances figées). Pour la recréer et lancer tous les tests :

```bash
.venv/bin/python -m pip install --only-binary=:all: -r requirements-ml.txt
.venv/bin/python -m pip check
```

```bash
pio run -d firmware
pio run -d firmware -e dataset
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_stream.py --help
.venv/bin/python -m gestureos.capture --help
.venv/bin/python -m gestureos.preprocess --help
.venv/bin/python -m gestureos.train --help
.venv/bin/python -m gestureos.predict --help
.venv/bin/python -m gestureos.select_thresholds --help
```

La collecte physique a commencé ; le banc long et les autres mesures restent
à valider. Aucun flashage n’a été effectué pendant M6. Le LCD disponible
possède 16 broches, sans adaptateur I2C.

## Périmètre actuel

`firmware/src/imu.*` lit le capteur et contrôle les erreurs ; `main.cpp` produit
un flux CSV de banc. `firmware/include/config.h` centralise sa configuration.
`scripts/check_stream.py` conserve ce flux sans écrasement et vérifie sa cadence.
`firmware/src/dataset_main.cpp` fournit le protocole de collecte bornée,
`src/gestureos/` valide les captures et conserve leur provenance. Le guide
de collecte explique les deux profils de firmware, le CRC et les sorties.
Les fixtures de `tests/` sont artificielles, utilisées uniquement pour tester
le code. Les tests du lanceur emploient des estimateurs factices sans apprentissage.
Elles ne constituent jamais des données ML ou des résultats de reconnaissance.

Le logger de gestes labellisés fonctionne sur les premières captures courtes. La
calibration, le LCD, le ML, le déploiement TinyML et les modes seront ajoutés
par jalons logiciels successifs, avec leurs contrôles physiques reportés.
Les deux firmwares conservent gravité et biais : ils ne sont pas une calibration.

## Reprise

Dire `continue` dans ce dossier. Lire d'abord les quatre fichiers `.agent/`,
puis `git status` et `git log --oneline -n 5`. Les checkpoints sont versionnés.
`data/raw/`, les modèles et les expériences sont exclus de Git : prévoir leur
copie de sauvegarde séparée dès qu'ils existent. Les rapports de test de banc
seront dans `reports/hardware/` et conservés avec leurs logs réels.

Pas de réseau requis pour le futur fonctionnement embarqué. Aucun objectif
de 15–20 gestes ou 90–95 % n'est présenté comme déjà atteint.
