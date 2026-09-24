# GestureOS AI

Contrôleur gestuel TinyML sur ESP32 + MPU6050, avec interface LCD 1602.
L'objectif est une reconnaissance locale fiable, avec rejet UNKNOWN et modes
ROBOT, SMART CONTROL, PRESENTATION, GAME, MACRO et CUSTOM.

**État réel : phase 0 terminée ; premier test logiciel préparé, MPU6050 non testé.**
La carte répond au bootloader : ESP32-D0WDQ6 révision 1, Flash 4 Mo, CP2102.
Le firmware de test compile ; six tests logiciels passent. Aucun modèle,
dataset de gestes, score de précision ou test d'actionneur n'existe encore.

## Lire en premier

- [Audit et architecture proposée](outputs/phase-0-audit.md)
- [Premier test : câblage, commandes, critères](outputs/first-mpu6050-test.md)
- [Architecture évolutive](docs/architecture.md)
- [Revue Antigravity et décisions](docs/antigravity-review.md)
- [État de reprise](.agent/PROJECT_STATE.md)
- [Prochaine action exacte](.agent/NEXT_ACTION.md)
- Brief et protocole complets : `docs/requirements/`.

## Installation minimale déjà effectuée

L'environnement `.venv` utilise le Python système 3.14.4 et pyserial 3.5.
Il est séparé du Python interne de PlatformIO. Pour le recréer s'il manque :

```bash
/usr/bin/python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

PlatformIO 6.2.0 est installé. Le projet fixe `espressif32@7.0.1`, dont le
framework présent est Arduino ESP32 2.0.17. Aucun package ML installé dans le
venv ; leur compatibilité Python sera vérifiée avant la phase d'entraînement.

```bash
pio run -d firmware
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_stream.py --help
```

Le flashage et les mesures restent à effectuer après confirmation du câblage.
Le guide indique les commandes ; le firmware actuellement dans la carte n'a
pas été remplacé. Le LCD disponible possède 16 broches, sans adaptateur I2C.

## Périmètre actuel

`firmware/src/imu.*` lit le capteur et contrôle les erreurs ; `main.cpp` produit
un flux CSV de banc. `firmware/include/config.h` centralise sa configuration.
`scripts/check_stream.py` conserve ce flux sans écrasement et vérifie sa cadence.
Les fixtures de `tests/` sont artificielles, utilisées uniquement pour tester
le protocole. Elles ne constituent jamais des données ML.

Le futur logger de gestes labellisés, la calibration, le LCD, le ML, le
déploiement TinyML et les modes seront ajoutés dans leurs phases respectives.
Le test actuel conserve la gravité et les biais : il n'est pas une calibration.

## Reprise

Dire `continue` dans ce dossier. Lire d'abord les quatre fichiers `.agent/`,
puis `git status` et `git log --oneline -n 5`. Les checkpoints sont versionnés.
`data/raw/`, les modèles et les expériences sont exclus de Git : prévoir leur
copie de sauvegarde séparée dès qu'ils existent. Les rapports de test de banc
seront dans `reports/hardware/` et conservés avec leurs logs réels.

Pas de réseau requis pour le futur fonctionnement embarqué. Aucun objectif
de 15–20 gestes ou 90–95 % n'est présenté comme déjà atteint.
