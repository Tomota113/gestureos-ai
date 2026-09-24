CHECKPOINT ID:
M5-software-baselines-verified

PHASE:
Baselines et journalisation PC terminés côté logiciel ; tests matériels différés.

OBJECTIVE:
Préparer des expériences reproductibles sur captures réelles, sans fuite de données ni résultats inventés.

COMPLETED:
Dépendances ML compatibles Python3.14 installées depuis wheels et versions figées.
RF, SVM RBF, MLP configurés ; entrée préparée recalculée depuis RAW/manifeste validés.
Fit train uniquement ; métriques/predictions/latence PC sur validation, test final jamais évalué.
Scalers figés, seeds/configuration/versions/code SHA et provenance sauvegardés.
Bundles atomiquement publiés sans écrasement, sauvegarde par modèle, journal d’interruption.
Sélection macro F1 validation, avertissements de convergence conservés et modèle exclu.
Guide outputs/baselines-guide.md et documentation mis à jour.

TESTED:
.venv/bin/python -m unittest discover -s tests -v : 56 tests OK, dont13 nouveaux.
.venv/bin/python -m pip check : No broken requirements found.
.venv/bin/python -m gestureos.train --help : OK.
git diff --check : OK avant clôture.
Données préparées/RAW altérés refusés ; routage train/validation exclusif et scaler vérifié ; test remplacé par sentinel inutilisable ; sauvegarde/relecture de bundles factices ; refus d’écrasement ; interruptions et avertissements.
Preuves : reports/m5-baselines-tests.txt. Logs bruts : work/m5-tests.log et work/m5-install.log.

TEST RESULTS:
Tests logiciels uniquement, avec estimateurs factices sans apprentissage. Paramètres/constructeurs des vrais estimateurs vérifiés sans fit.
Aucun dataset réel, entraînement de gestes, score ML, mesure physique ou flashage.

FAILED / UNRESOLVED:
Aucun test en échec. Entraînement réel à exercer après collecte.
Inférence utilisateur, rejet/calibration, test final, CNN/KNN, export TinyML et parité C++ non implémentés.
Pas de reprise à mi-entraînement. Arrêt brutal/disque plein peut empêcher failure.json : exiger un result.json final valide.
Modèles PC compressés et latence predict seule ne mesurent pas les ressources ESP32.

FILES CHANGED:
src/gestureos/{baselines,train}.py ; tests/test_baselines.py ; configs/baselines.json ;
pyproject.toml ; requirements-ml.txt ; README.md ; docs/architecture.md ;
outputs/{baselines-guide,resume-status}.md ; reports/m5-baselines-tests.txt ; .agent/*.

CURRENT GIT STATUS:
Base38dfc00 propre avant M5. Lot à sauvegarder dans « feat: add verified PC baselines and experiment logging ».
Vérifier le statut et le commit réel à la prochaine reprise.

QUOTA:
Contrôle officiel : 31 % utilisés au début de M5 ; 57 % avant clôture sur5h (43 % restants), semaine58 % utilisés.
Aucun reset/crédit de réinitialisation utilisé par l’agent.

NEXT EXACT STEP:
Préparer le logiciel d’inférence PC et de rejet UNKNOWN selon .agent/NEXT_ACTION.md, sans demander de branchements.

SAFE TO RESUME:
YES

REASON:
Code, versions, paramètres, preuves et limites persistants ; aucune donnée utilisateur écrasée ; aucun état matériel modifié.
