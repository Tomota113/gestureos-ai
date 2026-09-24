CURRENT PHASE:
M4-SOFTWARE terminé. Aucun modèle entraîné, aucun dataset physique.

NEXT OBJECTIVE:
Préparer les baselines PC et leurs expériences reproductibles, sans inventer de résultats ML.

NEXT ACTION:
1. Lire .agent/*, git status, git log --oneline -n 5 ; vérifier quota réel.
2. Lire manifest.py, preprocessing.py, features.py, preprocess.py et tests/test_preprocessing.py.
3. Vérifier la compatibilité et disponibilité des dépendances ML avec Python3.14.4 avant installation. Venv actuellement : gestureos et pyserial seulement.
4. Concevoir l’entrée d’entraînement depuis le dataset préparé : vérifier pipeline/version, partitions, scaler, ordre des features, labels et provenance. Revalider les empreintes si les RAW sont utilisés à nouveau.
5. Implémenter RF/SVM/MLP (et autres baselines seulement si utiles), seeds/config et sauvegarde d’expériences. SVM/MLP utilisent le scaler train-only déjà figé ; ne pas ajuster sur validation/test.
6. Réserver le test final : hyperparamètres et seuils de rejet choisis sur train/validation uniquement. Aucun score réel sans gestes réels.
7. Tester les invariants de code avec fixtures explicitement artificielles sous work/ ; aucune expérience synthétique ne devient un résultat du projet.
8. Documenter/mettre à jour checkpoint avant toute opération longue et après tests.

NOTES:
Le prétraitement normalise la durée vers200 points, conserve duration_s, refuse la décimation.
Pour captures>200 points, augmenter target_points (max512) ; aucun filtre anti-repliement implémenté.
Les séquences restent en unités physiques ; scaler par canal pour CNN non implémenté.
Pas de nouvelle demande de branchement pendant ces jalons logiciels.
Ne pas relancer Antigravity automatiquement après les anciens timeouts.
