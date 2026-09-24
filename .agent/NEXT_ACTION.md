CURRENT PHASE:
M5-SOFTWARE terminé : lanceur RF/SVM/MLP et expériences, 56 tests OK. Aucun modèle réel entraîné.

NEXT OBJECTIVE:
M6 logiciel : contrat d’inférence PC et préparation du rejet UNKNOWN, avant toute liaison aux actions matérielles.

NEXT ACTION:
1. Lire .agent/*, git status et cinq derniers commits ; vérifier quota réel.
2. Lire outputs/baselines-guide.md, baselines.py, train.py, preprocessing.py et tests/test_baselines.py. Dépendances ML déjà installées : ne pas réinstaller sans motif.
3. Préparer une API d’inférence depuis un bundle local de confiance : valider contrat/versions/labels/features, appliquer exactement le pipeline et le scaler figés, sans fit à l’inférence.
4. Définir les scores RF/MLP et marges SVM sans les appeler probabilités calibrées. Ne pas inventer de seuil optimal. Concevoir le rejet UNKNOWN et le format d’événement de geste ; séparer classification et action.
5. Préparer, si possible dans le jalon, le choix de seuils sur validation seulement et des métriques de rejet. Le test final reste réservé. Aucun étalonnage ni résultat réel sans captures physiques.
6. Tester ces invariants avec estimateurs factices et scénarios analytiques sous work/ ; aucun entraînement de classificateur sur fixtures et aucun score factice publié comme résultat du projet.
7. Documenter limites, mettre à jour les trois checkpoints avant opération longue/après tests/avant fin et faire un commit cohérent.

NOTES:
L’utilisateur effectuera les branchements plus tard. Ne pas les redemander pendant les jalons logiciels.
Aucun dataset, modèle ou expérience réel ; ne pas générer des gestes synthétiques pour combler ce manque.
M5 : comparaison de trois baselines seulement. KNN, CNN, augmentation et export embarqué restent à venir.
Une classe supervisée unknown ne remplace pas un rejet des mouvements hors distribution.
Les artefacts joblib sont destinés au PC et doivent avoir une provenance de confiance.
Prétraitement : 200 points, durée physique conservée, pas de décimation ; augmenter target_points si capture plus longue (max512).
Conserver les résultats existants : pas de reprise/réentraînement automatique des expériences incomplètes.
Ne pas relancer Antigravity automatiquement après les anciens timeouts.
