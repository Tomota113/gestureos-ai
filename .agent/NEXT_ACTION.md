CURRENT PHASE:
Progression logicielle sans branchement. M2-SOFTWARE collecte terminé ; M1-PHYSICAL en attente volontaire.

NEXT OBJECTIVE:
Créer le chargement fiable des futurs datasets réels et les partitions train/validation/test.
Ne pas lancer un entraînement sur des fixtures ni produire de faux résultats ML.

NEXT ACTION:
1. Lire les quatre fichiers .agent ; git status ; git log --oneline -n 5.
2. Lire src/gestureos/protocol.py, capture.py, configs/collection.json,
   docs/dataset-protocol.md et tests/test_capture.py. Vérifier ce qui existe déjà sous data/.
3. Implémenter le chargement des dossiers de capture : result.json complet, provenance hardware,
   eligible_for_training=true, identité cohérente, vérification de SHA256 et des données.
   Refuser par défaut fixtures, captures partielles, doublons et incohérences ; conserver les RAW.
4. Ajouter manifests et splits reproductibles par session et, si possible, par sujet.
   Aucun sample parent ou augmentation ne doit franchir les partitions.
   Si données/groupes insuffisants, produire un diagnostic explicite, pas un split fuyant.
5. Tester les invariants sur fixtures sous work/ uniquement. Aucun dataset de gestes inventé.
6. Documenter les commandes et mettre à jour checkpoint avant le jalon suivant.
7. Plus tard : preprocessing train-only, baselines RF/SVM/MLP puis CNN selon données réelles.
   Vérifier les dépendances Python disponibles avant installation et conserver les versions.

EXPECTED RESULT:
Pipeline de préparation exploitable et testé, capable d'attendre les données réelles.
Aucune accuracy, matrice de confusion réelle ou validation embarquée annoncée sans mesure.

IF SUCCESS:
Commit cohérent et prochaine action logicielle précise, sans redemander le câblage.

IF FAILURE:
Lire la cause, conserver les fichiers, corriger et tester. Aucune boucle de retry de service IA.

DEFERRED HARDWARE ACTIONS:
Quand l'utilisateur annonce vouloir câbler/tester/collecter : identifier le module,
valider alimentation et câblage, préserver le programme précédent si nécessaire,
flasher le profil approprié et tester de vraies mesures selon outputs/first-mpu6050-test.md
puis outputs/dataset-collection-guide.md. Ces commandes ne sont PAS à exécuter maintenant.

FILES INVOLVED:
src/gestureos/*, tests/*, configs/*, docs/dataset-protocol.md, .agent/*.
