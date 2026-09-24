PROJECT: GestureOS AI

CURRENT PHASE:
M6 inférence PC/rejet UNKNOWN terminé côté logiciel. Collecte physique commencée par l’utilisateur.

CURRENT MILESTONE:
M6-SOFTWARE : chargement vérifié, features/scaler figés, scores RF/MLP/SVM, politique UNKNOWN et CLI diagnostique. 87 tests OK.

STATUS:
READY_FOR_NEXT_SOFTWARE_MILESTONE / COLLECTION_IN_PROGRESS

LAST COMPLETED TASK:
M6 : vérifier modèles locaux de confiance (SHA256, versions, code de prétraitement, paramètres, contrat, classes), inférer sans fit, refuser le test final dans la CLI, rejeter les scores ambigus et les mouvements inconnus. Défaut unconfigured => UNKNOWN, aucune action matérielle.

CURRENT TASK:
Jalon M6 documenté et testé. Prochain logiciel : sélection/évaluation des seuils sur validation uniquement ; données réelles encore insuffisantes pour entraîner les modèles.

LAST SUCCESSFUL COMMAND:
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m gestureos.predict --help
git diff --check

LAST SUCCESSFUL TEST:
87 tests Python OK dont17 nouveaux M6. Preuves reports/m6-inference-tests.txt. Modèles factices, scores analytiques, aucun fit de classificateur.
81 fichiers de données/rapports matériels présents au départ : empreintes inchangées après tests.
Aucun changement/rebuild/flash du firmware pendant M6. Builds/tests C++ antérieurs restent les derniers réalisés.

HARDWARE CURRENTLY TESTED:
ESP32 classique ESP32-D0WDQ6, Flash4Mo, CP2102. Les captures réelles MPU6050 revérifiées couvrent200 échantillons à100Hz avec CRC/SHA/timing valides.
ATTENTION : reports/hardware/bench-offline-001.json indique passed:false,0 sample et imu_init. Les captures courtes ultérieures ne prouvent pas un banc de60s réussi. Axes, biais, fixation et robustesse restent à caractériser.
Aucun accès actif au périphérique pendant M6.

HARDWARE NOT YET TESTED:
LCD1602 16 broches et actionneurs ; validation longue de cadence encore à refaire/documenter.

MODEL CURRENTLY USED:
Aucun classificateur de gestes entraîné/exporté/embarqué. RF/SVM/MLP sont prêts côté logiciel, pas des modèles validés sur gestes réels.

DATASET STATUS:
Inventaire revérifié en lecture seule :3 captures physiques swipe_left,2 séances de user01 (session_20260924_142811_6470 et session_20260924_151343_bb2e),0 capture rejetée par le chargeur.
Aucun autre label au moment de l’inventaire. Collecte potentiellement en cours : rescanner avant décision.
RAW confirmés dans data/raw ; toutes les tentatives/originaux dans data/pending ; notes dans data/session_notes. Ne pas employer pending automatiquement comme dataset.
Les fixtures restent sous work/ uniquement et ne sont jamais des résultats du projet.

KNOWN LIMITATIONS:
Aucun test en échec. Pas d’entraînement réel, de score ML ou de seuil optimisé.
Politique par défaut non configurée : UNKNOWN systématique. Politique experimental liée au modèle/convention, pour diagnostic seulement ; action_authorized:false même si ACCEPTED.
Sélection de seuils/calibration sur validation, métriques de rejet, test final, lissage/segmentation continue, KNN/CNN, augmentation, TinyML et parité C++ restent à venir.
Pas de reprise automatique d’un entraînement interrompu. Prétraitement en mémoire, aucune décimation sans filtre anti-aliasing.
Inférence bas niveau attend des lignes déjà validées ; la CLI assure relecture RAW et garde du test final.
Joblib : sources locales de confiance seulement ; checksum n’est pas une authentification. Versions strictement comparées.

EXISTING USER CHANGES:
Déjà présents à la reprise et laissés intacts : src/gestureos/capture.py, src/gestureos/dataset.py, tests/test_dataset.py (READY collé au texte ROM sans LF) ; reports/hardware/ non suivi.
Ces modifications et données matérielles ne sont pas incluses dans le commit M6. Les checkpoints intègrent l’état physique observé.

IMPORTANT DECISIONS:
Collecte hors ligne prête ; ne pas interrompre la collecte ni reflasher automatiquement.
Split par sujet/session, scaler train seulement, test final réservé. La CLI refuse IDs, copies de signal et groupes du test.
M6 conserve predict comme candidat, marge = score candidat moins meilleur autre score ; égalité/conflit => UNKNOWN.
SVM binaire [-d,d], multiclasses OVR ; aucun score présenté comme probabilité calibrée.
Conserver LCD16 broches, aucun achat imposé, aucun crédit/reset consommé par l’agent.

NEXT ACTION:
Lire .agent/NEXT_ACTION.md. Avancer sur la validation des seuils sans inventer de données ni demander de nouveau le câblage.

ENVIRONMENT:
Ubuntu26.04 x86_64, Python3.14.4, PlatformIO6.2.0, espressif32 7.0.1 / Arduino2.0.17.
.venv : gestureos0.1.0 éditable, pyserial3.5, scikit-learn1.9.1, numpy2.5.3, scipy1.18.1, joblib1.6.0, threadpoolctl3.7.0, narwhals2.26.0, cloudpickle3.1.2. Dépendances inchangées.

ANTIGRAVITY:
Revue de conception initiale reçue ; revue ultérieure timeout60s sans avis. Aucun retry automatique ni déduction de quota. Pas d’appel pendant M6.

CODEX QUOTA:
Fenêtre revenue :0 % utilisés au départ,24 % au dernier contrôle avant clôture (76 % restants sur5h), semaine69 % utilisés. Aucun crédit/reset utilisé par l’agent.
