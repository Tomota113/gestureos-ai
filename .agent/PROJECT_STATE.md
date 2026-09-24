PROJECT: GestureOS AI

CURRENT PHASE:
Phase 0 terminée ; préparation minimale du test de phase 2 réalisée.
Les phases suivantes ne sont PAS validées.

CURRENT MILESTONE:
M0 audit terminé. M1 à valider : ESP32 + MPU6050, six axes réels, 100 Hz stable.

STATUS:
READY_FOR_HARDWARE_WIRING — l'utilisateur souhaite effectuer les branchements plus tard.

LAST COMPLETED TASK:
Audit réel, revue Antigravity, structure minimale, compilation, six tests de flux,
guide de câblage conditionnel, architecture proposée et rapports de vérification.

CURRENT TASK:
Checkpoint final avant attente du matériel câblé.

LAST SUCCESSFUL COMMAND:
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
pio run -d firmware

LAST SUCCESSFUL TEST:
6 tests logiciels OK ; firmware compilé sans warning relevé.
RAM statique 21808 octets ; Flash application 287585 octets.
Ce ne sont PAS des mesures runtime, de modèle ML ou du MPU6050.

FILES MODIFIED:
.agent/* ; AGENTS.md ; .gitignore ; README.md ; requirements.txt ;
firmware/platformio.ini ; firmware/include/config.h ; firmware/src/{main.cpp,imu.h,imu.cpp} ;
scripts/check_stream.py ; tests/test_stream.py ; docs/* ; outputs/* ; reports/*.

HARDWARE CURRENTLY TESTED:
Énumération USB et interrogation ROM ESP32 uniquement : ESP32-D0WDQ6 revision 1.0,
Flash 4 Mo, quartz 40 MHz, CP2102 sur /dev/ttyUSB0. Aucun flashage effectué.

HARDWARE NOT YET TESTED:
MPU6050, LCD 1602 16 broches, actionneurs et autres composants.

MODEL CURRENTLY USED:
Aucun modèle de reconnaissance gestuelle.

DATASET STATUS:
Aucune donnée physique de gestes collectée ; aucun dataset externe téléchargé.
Fixtures artificielles de tests uniquement dans tests/test_stream.py, pas utilisables comme dataset.

KNOWN BUGS:
Aucun défaut logiciel constaté par les contrôles actuels. Tests physiques non réalisés.
Polling sans FIFO/compteur INT ; limites documentées, absence absolue de pertes internes non prouvée.

BLOCKERS:
Référence exacte et schéma du module MPU6050 non fournis ; alimentation/pull-ups à confirmer.
Utilisateur effectuera le câblage plus tard. Ne pas flasher ou lancer une collecte avant vérification.

IMPORTANT DECISIONS:
PlatformIO 6.2.0 + espressif32 7.0.1 (Arduino ESP32 2.0.17), cible esp32dev.
I2C 100 kHz sur GPIO21/22 ; DATA_RDY ; cadence 100 Hz ; UART 230400.
LCD 16 broches conservé ; aucun achat ni ajout d'adaptateur I2C nécessaire maintenant.
Venv indépendant depuis /usr/bin/python3 3.14.4 avec pyserial 3.5 seulement.
Calibration et logger de gestes labellisés NON implémentés ; mesures actuelles prévues non calibrées.

DO NOT FORGET:
Lire les quatre fichiers .agent et git status/log avant toute modification.
Ne pas recréer le projet, réinstaller les dépendances ou recommencer la phase 0 sans motif.
Inspecter tout log, modèle ou expérience déjà présent avant de relancer.
Préserver firmware existant avant flash si nécessaire et conserver les captures réelles sans écrasement.
Un test de protocole artificiel ou une compilation n'est jamais une mesure physique ni un résultat ML.

NEXT ACTION:
Suivre .agent/NEXT_ACTION.md ; identifier module MPU6050 puis valider câblage et M1.

ENVIRONMENT:
Ubuntu 26.04 LTS x86_64 ; Python 3.14.4 ; Git 2.53.0.
Python par défaut = venv interne PlatformIO ; employer .venv/bin/python pour ce projet.
arduino-cli et idf.py absents de PATH ; IDF_PATH absent.
Port stable observé : /dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0

ANTIGRAVITY:
agy --help, agy models et revue --mode plan --print-timeout 60s réussis.
Revue conservée dans docs/antigravity-review.md ; aucune édition concurrente.
Quota inconnu ; /usage, /quota et /resume non confirmés, non exécutés.

CODEX QUOTA:
Instantané officiel initial : 6 % de la fenêtre 5 h et 35 % de la semaine utilisés.
Aucun crédit consommé ni reset lancé ; ne pas extrapoler cet instantané.
