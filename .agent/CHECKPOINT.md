CHECKPOINT ID:
M6-software-inference-rejection-verified

COMPLETED:
Modèles PC locaux : version Python/paquets, code features/prétraitement, SHA/taille, contrats, paramètres et classes contrôlés.
Features identiques au train, standardisation figée, jamais de fit. Scores RF/MLP non calibrés, SVM binaire signé/multiclasses OVR explicites.
Rejet UNKNOWN par politique non configurée ou seuils expérimentaux liés au modèle ; inconnus/égalités/conflits toujours rejetés, aucune action matérielle.
CLI sur capture RAW revérifiée, protège test final par ID/contenu/groupe, préserve fichiers existants.
Guide outputs/inference-guide.md et documentation à jour.

TESTED:
.venv/bin/python -m unittest discover -s tests -v :87 tests OK dont17 M6.
CLI predict --help et git diff --check OK. Preuves reports/m6-inference-tests.txt ; log brut work/m6-all-tests.log.
87 inclut les tests des corrections de collecte déjà présentes chez l’utilisateur, laissées inchangées.
81 fichiers data/rapports matériels présents au départ : aucun modifié/manquant après tests.

REAL DATA:
3 swipe_left valides sur2 séances,0 rejet au scan. Aucun autre geste, aucun entraînement ou score ML.
Rapport bench-offline-001.json en échec imu_init/0 sample. Ne pas annoncer un banc60s réussi. Captures courtes seules validées.

UNRESOLVED:
Choix/évaluation des seuils sur validation, calibration probabiliste, test final, temps réel/segmentation/lissage, CNN/KNN/augmentation, TinyML et tests des actionneurs restent à venir.
Pas de seuil optimal inventé, politique livrée unconfigured. Aucun modèle réel disponible pour un essai d’inférence physique.

GIT:
Base59a9d74. Commit M6 à créer : feat: validate frozen PC inference and UNKNOWN rejection.
Changements préexistants laissés non committés : capture.py/dataset.py/test_dataset.py ; reports/hardware/ non suivi.
Vérifier git status/log à la reprise, ne pas prétendre au dépôt propre.

QUOTA:
0 % utilisés au départ,24 % au dernier contrôle sur5h, semaine69 %. Aucun crédit/reset consommé par l’agent.

SAFE TO RESUME:
YES — M6 validé côté logiciel, captures et modifications utilisateur préservées, limites physiques explicites.
