PROJECT: GestureOS AI

CURRENT PHASE:
Développement logiciel par jalons, matériel reporté à la demande utilisateur.
Audit achevé ; banc MPU6050 et logger labellisé implémentés côté logiciel.

CURRENT MILESTONE:
M2-SOFTWARE : collecte bornée ESP32/PC avec provenance et intégrité, tests hors matériel réussis.
M1-PHYSICAL : acquisition réelle MPU6050, toujours non validée.

STATUS:
READY_FOR_NEXT_SOFTWARE_MILESTONE. Ne pas attendre ou redemander le câblage maintenant.

LAST COMPLETED TASK:
- Reprise depuis a02bf6b et correction du contrôle des premières trames perdues (3d8dc7c).
- Ajout profil firmware dataset et protocole CAPTURE/begin/D/end, compteur + CRC32 IEEE.
- Package Python gestureos 0.1.0 installé en mode éditable, CLI capture et conservation des données.
- Guides, tests et traces de vérification enregistrés.

CURRENT TASK:
Jalon de collecte logiciel terminé ; prochain jalon : chargement contrôlé des captures et splits ML.

LAST SUCCESSFUL COMMAND:
pio run -d firmware -e esp32dev -e dataset
.venv/bin/python -m unittest discover -s tests -v
./work/capture_protocol_test
.venv/bin/python -m gestureos.capture --help
.venv/bin/python -m pip check

LAST SUCCESSFUL TEST:
20 tests Python OK ; tests C++ natifs de parsing/CRC OK ; 2 builds ESP32 SUCCESS.
Banc : RAM statique 21808 octets, Flash application 287585 octets.
Dataset : RAM statique 22016 octets, Flash application 315941 octets.
Ces tailles viennent du linker, pas d'une mesure runtime ou d'un modèle ML.
Preuves : reports/logger-validation-20260924/.

FILES MODIFIED:
pyproject.toml, requirements.txt, .gitignore, configs/collection.json,
src/gestureos/{__init__,protocol,capture}.py, scripts/capture_serial.py,
firmware/platformio.ini, firmware/src/{capture_protocol.h,capture_protocol.cpp,dataset_main.cpp},
tests/test_capture.py, tests/native/capture_protocol_test.cpp, README.md,
docs/{architecture,dataset-protocol}.md, outputs/dataset-collection-guide.md,
reports/logger-validation-20260924/*, .agent/*.

HARDWARE CURRENTLY TESTED:
USB/ROM ESP32 seulement, précédemment ESP32-D0WDQ6 revision 1.0, Flash 4 Mo, CP2102.
CP2102 encore énuméré sur /dev/ttyUSB0 à la reprise. Aucun flashage effectué.

HARDWARE NOT YET TESTED:
MPU6050, LCD1602 16 broches, tous les actionneurs et autres composants.
Le câblage réel, la calibration, la stabilité de cadence, les axes et la collecte restent à mesurer.

MODEL CURRENTLY USED:
Aucun modèle de reconnaissance entraîné, exporté ou embarqué.

DATASET STATUS:
Aucune séquence physique collectée, aucun dataset externe téléchargé.
Fixtures exclusivement artificielles pour tests de code : source_kind=synthetic_test,
éligibilité entraînement false, dossiers temporaires sous work/ (jamais data/raw/).
Captures réelles futures : data/raw/<subject>/<session>/<capture_id>/.

KNOWN BUGS:
Perte de trames initiales dans le vérificateur de banc : corrigée et testée.
Aucun autre défaut identifié par les contrôles actuels, limites physiques non testées.
Polling sans FIFO/INT. Un arrêt brutal peut laisser un result.json absent/invalide : ne pas considérer la capture valide.

BLOCKERS:
Aucun blocage pour le prochain jalon logiciel.
Tests matériels et entraînement/évaluation réels attendent branchements et données réelles.
Référence/tension du module MPU6050 à confirmer UNIQUEMENT à l'étape matérielle.

IMPORTANT DECISIONS:
Instruction utilisateur prioritaire : avancer côté logiciel maintenant ; branchements plus tard.
Deux environnements PlatformIO : esp32dev (banc par défaut), dataset (collecte bornée).
I2C 100kHz, 100Hz par défaut, UART230400, +/-4g et +/-500 deg/s, pas de calibration.
Capture PC avec sujet/session/label, UUID, CRC et SHA256 du log ; jamais d'écrasement.
Les captures incomplètes et les fixtures sont inéligibles à l'entraînement.
Conserver LCD16 broches ; pas d'achat imposé.

DO NOT FORGET:
Lire les quatre fichiers .agent et git status/log avant modification.
Ne pas réinstaller, recompiler ou relancer les tests déjà réussis sans motif.
Ne pas redemander le câblage lors des jalons logiciels.
Ne jamais présenter compilation, fixtures ou tests simulés comme de vraies performances ML/matérielles.
Ne pas supprimer les captures réelles ; les sauvegarder séparément de Git dès qu'elles existent.

NEXT ACTION:
Suivre .agent/NEXT_ACTION.md : pipeline de lecture/validation et partitionnement sans fuite de données.

ENVIRONMENT:
Ubuntu26.04 x86_64, Python3.14.4, Git2.53.0, PlatformIO6.2.0, espressif32 7.0.1 / Arduino2.0.17.
Venv .venv indépendant, pyserial3.5 et gestureos0.1.0 éditable installés.
Build Python utilise setuptools80.9.0 dans un environnement isolé (pyproject.toml).
Aucune dépendance ML installée dans .venv ; compatibilité à vérifier avant ajout.

ANTIGRAVITY:
Revue initiale de conception réussie (docs/antigravity-review.md).
Revue du code à la reprise : délai 60s atteint sans avis, malgré exit0. INCOMPLETE_TIMEOUT,
pas une revue réussie ou une preuve de quota. Aucun retry automatique. Détails reports/resume-stream-check-20260924.txt.

CODEX QUOTA:
Ancien instantané officiel au début du projet : 6% utilisé sur 5h et 35% sur semaine.
Ne pas extrapoler à l'état actuel. Aucun crédit ou reset consommé.
