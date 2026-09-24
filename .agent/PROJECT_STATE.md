PROJECT: GestureOS AI

CURRENT PHASE:
Développement logiciel sans matériel. M5 terminé ; kit de collecte hors ligne terminé côté logiciel. M6 non terminé.

CURRENT MILESTONE:
OFFLINE-COLLECTION : menu français, confirmation des prises, RAW/pending séparés, notes, firmwares fusionnés et installateur local avec sauvegarde Flash. 69 tests OK.

STATUS:
READY_FOR_NEXT_SOFTWARE_MILESTONE

LAST COMPLETED TASK:
Dépendances ML vérifiées/installées sur Python3.14.4. Entrée préparée recalculée depuis les RAW revérifiés. Fit train, métriques et sélection sur validation uniquement. Paramètres, versions, empreintes, prédictions, bundles et interruptions conservés sans écrasement. Guide baselines disponible.

CURRENT TASK:
Kit hors ligne prêt pour cet ordinateur + ESP32/MPU6050, comme confirmé par l’utilisateur. Guide outputs/COLLECTE_SANS_WIFI.md. Aucun port USB détecté ni test capteur/flashage réalisé. M6 sauvegardé en cours, pas prêt : inference.py, rejection.py, predict.py, configs/rejection.json. Syntaxe seulement vérifiée ; tests fonctionnels à écrire.

LAST SUCCESSFUL COMMAND:
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
.venv/bin/python -m gestureos.train --help
git diff --check

LAST SUCCESSFUL TEST:
69 tests Python OK, dont13 nouveaux pour la collecte hors ligne. Preuves reports/offline-collection-tests.txt. Lanceurs --check et intégrité des deux images OK.
Estimateurs réels importés/paramètres contrôlés seulement ; estimateurs factices pour les tests du lanceur.
Aucun changement firmware : builds et tests C++ du précédent jalon restent les derniers effectués.

FILES MODIFIED:
src/gestureos/baselines.py, train.py ; configs/baselines.json ; tests/test_baselines.py ; pyproject.toml ; requirements-ml.txt ; README.md ; docs/architecture.md ; outputs/baselines-guide.md ; outputs/resume-status.md ; reports/m5-baselines-tests.txt ; .agent/*.

HARDWARE CURRENTLY TESTED:
USB/ROM ESP32 uniquement, précédemment ESP32-D0WDQ6 revision1.0, Flash4Mo, CP2102 sur /dev/ttyUSB0.
Aucun nouveau contrôle USB, test matériel ou flashage pendant M5.

HARDWARE NOT YET TESTED:
MPU6050, LCD1602 16 broches, actionneurs. Câblage, calibration, cadence, axes et collecte à valider plus tard.
Référence/tension du module MPU6050 à confirmer seulement à l’étape matérielle.

MODEL CURRENTLY USED:
Aucun classificateur de gestes entraîné, aucun modèle exporté ou embarqué.
RF/SVM/MLP sont des configurations prêtes à utiliser après collecte, pas des résultats ML.

DATASET STATUS:
Aucune capture physique, aucun dataset externe. data/raw/, experiments/ et models/ absents au dernier contrôle.
Fixtures artificielles uniquement sous work/ temporaire. Certaines imitent les métadonnées hardware pour tester la validation ; elles ne sont jamais des mesures ni des expériences du projet. Les fichiers temporaires des tests sont nettoyés à leur fin.
Captures futures : data/raw/<subject>/<session>/<capture_id>/.

KNOWN LIMITATIONS:
Aucun test actuellement en échec. Entraînement réel non exercé faute de données.
Pas de rejet par seuil/marge, de calibration des probabilités, de final-test CLI ou de déploiement TinyML.
La classe supervisée unknown seule ne garantit pas le rejet de tous les mouvements inconnus.
PC latency = predict seul ; bundle joblib = taille fichier compressé, ni RAM ni taille embarquée.
Prétraitement : pas de décimation sans anti-aliasing ; tout le dataset pilote reste en mémoire.
Reprise automatique d’une expérience interrompue non implémentée : inspecter les modèles déjà terminés avant toute nouvelle exécution.
Un arrêt brutal peut laisser des fichiers partiels : absence de résultat final valide = lot incomplet.

BLOCKERS:
Aucun blocage pour les jalons logiciels. Entraînement réel, métriques ML et tests physiques attendent les données et branchements que l’utilisateur fera ultérieurement.

IMPORTANT DECISIONS:
Avancer côté logiciel maintenant, branchements plus tard sans demandes répétées.
Split par sujet/session figé ; scaler ajusté sur train uniquement ; aucune augmentation avant split.
RF utilise features brutes ; SVM/MLP standardisées. Seed42, un thread, comparaison macro F1 validation.
Pas de probabilité SVM/calibration interne aléatoire ni de holdout interne MLP.
ConvergenceWarning exclut le modèle de la sélection, tout en conservant ses artefacts.
Le test est relu pour intégrité/prétraitement, jamais transmis aux estimateurs ou évalué pendant M5.
Journal par expérience et modèles sauvegardés progressivement ; RAW et expériences jamais écrasés.
Conserver LCD16 broches sans imposer d’achat. Aucun crédit acheté, aucun compte changé.

DO NOT FORGET:
Lire les quatre fichiers .agent et git status/log avant modification. Ne pas refaire un jalon fini sans motif.
Ne jamais présenter fixtures, compilation ou tests logiciels comme des performances ML/matérielles.
Sauvegarder séparément RAW/données préparées/modèles/expériences dès qu’ils existeront, car exclus de Git.
Les bundles joblib se chargent uniquement depuis une provenance locale de confiance et des versions compatibles.

NEXT ACTION:
Lire .agent/NEXT_ACTION.md : préparation de l’inférence PC et du rejet UNKNOWN. Aucune nouvelle demande de câblage.

ENVIRONMENT:
Ubuntu26.04 x86_64, Python3.14.4, Git2.53.0, PlatformIO6.2.0, espressif32 7.0.1 / Arduino2.0.17.
.venv indépendant : gestureos0.1.0 éditable, pyserial3.5, scikit-learn1.9.1, numpy2.5.3, scipy1.18.1, joblib1.6.0, threadpoolctl3.7.0, narwhals2.26.0, cloudpickle3.1.2.
Installation ML optionnelle : requirements-ml.txt. La suite complète des tests requiert les dépendances ML.

ANTIGRAVITY:
Revue de conception initiale réussie (docs/antigravity-review.md).
Ancienne revue de code : timeout60s sans avis malgré exit0, INCOMPLETE_TIMEOUT ; aucune preuve de quota épuisé.
Aucune relance automatique pendant M5, conformément à la décision persistante.

CODEX QUOTA:
Dernier contrôle officiel : 92 % utilisés sur5h, 8 % restants ; semaine64 % utilisés. Aucune nouvelle fonctionnalité après sauvegarde de ce kit. Aucun crédit/reset consommé.
