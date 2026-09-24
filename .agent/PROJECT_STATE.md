PROJECT: GestureOS AI

CURRENT PHASE:
Développement logiciel sans matériel. Audit, logger et préparation des partitions implémentés.

CURRENT MILESTONE:
M3-SOFTWARE terminé : lecture contrôlée des captures et splits groupés. Tests physiques toujours différés.

STATUS:
READY_FOR_NEXT_SOFTWARE_MILESTONE. Arrêt de session pour préserver le quota restant.

LAST COMPLETED TASK:
Chargeur dataset.py, split.py et CLI prepare.py ; contrôles identité/SHA/CRC/CSV/doublons ; partitions reproductibles par groupe. 30 tests logiciels OK.

CURRENT TASK:
Jalon M3 terminé, documentation et checkpoint sauvegardés. Ne pas démarrer une autre fonctionnalité dans cette session.

LAST SUCCESSFUL COMMAND:
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m gestureos.prepare --help
git diff --check

LAST SUCCESSFUL TEST:
30 tests Python OK ; preuves reports/m3-dataset-tests-20260924.txt. Firmware inchangé, pas de nouveau build ou flashage. Aucun test physique ni résultat ML.

FILES MODIFIED:
src/gestureos/{dataset,split,prepare}.py ; tests/test_dataset.py ; README.md ; outputs/dataset-preparation-guide.md ; reports/m3-dataset-tests-20260924.txt ; .agent/*.

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
Prétraitement reproductible et features, puis baselines selon disponibilité des données. Lire NEXT_ACTION.md ; ne pas demander le câblage pendant le développement logiciel.

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
Instantanés officiels de cette session : 83 % utilisés au départ, puis 90 %, enfin 95 % (5 % restants sur 5 h) avant clôture. Semaine : 49 % utilisés au dernier contrôle. Aucun crédit/reset consommé. Arrêt après ce jalon, pas de nouvelle fonctionnalité.
