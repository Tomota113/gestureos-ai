# Baselines PC — jalon M5

Le logiciel d’entraînement Random Forest, SVM et MLP est prêt. **Aucun modèle de
gestes n’a été entraîné, aucune précision n’a été mesurée.** Les 56 tests du
dépôt utilisent des fixtures artificielles et, pour le lanceur, des estimateurs
factices qui n’apprennent rien. Les vrais estimateurs ont été importés et leurs
paramètres contrôlés ; leur entraînement reste à valider sur les données réelles.

## Installation vérifiée

Dans le dossier du projet, avec le venv séparé de PlatformIO :

```bash
.venv/bin/python -m pip install --only-binary=:all: -r requirements-ml.txt
.venv/bin/python -m pip check
.venv/bin/python -m gestureos.train --help
```

L’installation a réussi sous Linux x86_64, Python 3.14.4 : scikit-learn 1.9.1,
NumPy 2.5.3, SciPy 1.18.1, joblib 1.6.0, threadpoolctl 3.7.0,
narwhals 2.26.0 et cloudpickle 3.1.2. Les versions sont figées dans
`pyproject.toml` et `requirements-ml.txt`. L’acquisition seule continue de
fonctionner sans installer l’option ML. La suite complète de tests demande
désormais cette option. [Documentation d’installation scikit-learn](https://scikit-learn.org/stable/install).

## Quand les captures réelles seront disponibles

Suivre d’abord les guides de [collecte](dataset-collection-guide.md), de
[partitionnement](dataset-preparation-guide.md) et de
[prétraitement](preprocessing-guide.md). Une fois le manifeste et le dataset
préparé disponibles, lancer depuis la racine du projet :

```bash
.venv/bin/python -m gestureos.train \
  --prepared data/processed/prepared-v1.json \
  --manifest data/processed/split-v1.json \
  --collection-config configs/collection.json \
  --config configs/baselines.json \
  --output experiments/baselines-v1
```

Ces chemins désignent les futurs fichiers à créer avec les guides précédents ;
ils ne constituent pas un dataset déjà présent. Adapter les noms aux sorties
réelles. Un dossier d’expérience existant est refusé, même s’il est incomplet.
`--raw-root nouveau/chemin` permet de retrouver des RAW déplacés, toujours avec
revérification des empreintes. Toute sortie dans les RAW est refusée.

Avant l’entraînement, le lanceur revérifie le manifeste, ses groupes et ses
captures, puis recalcule le prétraitement depuis les snapshots validés. Il
compare le résultat au JSON préparé : features, scaler, labels, partitions,
version et provenance doivent correspondre. Une modification nécessite de
régénérer explicitement les fichiers dérivés ; les RAW restent inchangés.

## Comparaison prévue

| Modèle | Entrée | Paramètres de départ |
|---|---|---|
| Random Forest | 64 features en unités d’origine | 200 arbres, profondeur 12, feuille minimale 2, classes équilibrées |
| SVM RBF | Features standardisées avec le scaler du train | C=1, gamma=scale, classes équilibrées, 100000 itérations maximum |
| MLP | Même standardisation figée | Couches 64/32, Adam, alpha=0.001, 500 itérations maximum |

Seed 42 et un thread de calcul par défaut. Aucun de ces paramètres n’est encore
optimisé pour les gestes. Le SVM ne calcule pas de probabilités ; le MLP
n’effectue pas de split interne pour un arrêt anticipé. Les groupes fixés par
le manifeste restent la référence. Voir les contrats officiels du
[SVM](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html) et du
[MLP](https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html).

Seul le **train** est transmis à `fit`. Seule la **validation** fournit les
prédictions, métriques et mesures PC. Le test est lu pour contrôler l’intégrité
et le prétraitement, mais jamais transmis aux estimateurs ni évalué. Aucun
réglage d’hyperparamètres sur le test et aucun refit train+validation automatique.

La comparaison utilise le macro F1 de validation. En cas d’égalité, l’ordre
fixe est RF, SVM, MLP. Un modèle avec `ConvergenceWarning` est sauvegardé mais
exclu du choix automatique. Si tous sont concernés, aucun candidat n’est
proposé. Un candidat de validation n’est pas une autorisation de déploiement.

Pour explorer des paramètres, copier/modifier la configuration et choisir un
nouveau dossier d’expérience, en gardant le même split. La recherche automatique
et l’agrégation de plusieurs seeds ne sont pas implémentées dans ce jalon.

Une augmentation train-only optionnelle est décrite dans
[augmentation-guide.md](augmentation-guide.md). Elle requiert un nouveau dossier
d'expérience et l'option `--augmentation-config configs/augmentation-rotation-v1.json`.

## Fichiers conservés par expérience

```text
experiments/baselines-v1/
  run.json                      début, empreintes, versions, Git, code, limites
  config.json                   paramètres demandés
  data_contract.json            labels, pipeline, scaler, captures et split
  random_forest/                 mêmes sorties dans svm/ et mlp/
    parameters.json             tous les paramètres de l’estimateur
    model.joblib                modèle + contrat d’inférence + provenance
    validation_predictions.json capture, classe attendue, classe prédite
    result.json                 métriques, avertissements, temps et taille
  comparison.json               classement de validation et candidat éventuel
  result.json                   fin : complete ou needs_review
  failure.json                  seulement en cas d’échec ou interruption interceptée
```

Chaque modèle terminé est sauvegardé immédiatement. Les métriques comprennent
accuracy, précision/rappel/F1 par classe, macro/moyenne pondérée et matrice de
confusion (lignes réelles, colonnes prédites), avec `zero_division=0`.
Le [rapport de classification scikit-learn](https://scikit-learn.org/stable/modules/model_evaluation.html#classification-report)
décrit ces mesures. Aucun graphique de performance réelle n’est produit avant
la collecte ; les matrices sont enregistrées en JSON.

La latence enregistrée concerne **predict sur PC**, un sample par appel, après
un appel d’échauffement, sur au plus 100 captures de validation. Elle exclut
l’acquisition, le prétraitement et le chargement. Médiane et p95 sont des
observations locales, pas des mesures ESP32. La taille est celle du bundle
joblib compressé, pas sa consommation RAM ni une taille TFLite.

Les bundles joblib doivent provenir d’une expérience locale de confiance : leur
chargement utilise le mécanisme pickle et peut exécuter du code. Conserver les
versions enregistrées ; la compatibilité entre versions de scikit-learn n’est
pas garantie. [Documentation de persistance](https://scikit-learn.org/stable/model_persistence.html).

## Après une interruption

Lire `result.json` puis `failure.json` s’ils existent. Sans résultat final
valide, considérer le lot comme incomplet, même si `run.json` indique son
démarrage. Un arrêt forcé ou un disque plein peut empêcher l’écriture du fichier
d’échec. Un fichier `.partial` n’est pas un modèle publié.

Conserver les sous-dossiers terminés et leurs résultats. Il n’y a pas de reprise
automatique à mi-entraînement, ni de relance automatique dans un dossier
existant. Inspecter ce qui est déjà terminé avant de décider d’un nouvel essai ;
ne pas réentraîner silencieusement les trois modèles. Les captures, les fichiers
préparés et les expériences sont exclus de Git : les sauvegarder séparément.

## Ce qui reste à faire

Le [diagnostic M6](inference-guide.md) implémente maintenant le rejet par seuil
et marge, désactivant toute acceptation tant que la politique est non configurée.
Les seuils et leur évaluation restent à réaliser. La classe
`unknown` du dataset est une classe supervisée, elle ne prouve pas la capacité
à rejeter tout mouvement inconnu. Calibration des scores, lissage temporel,
tests finaux, validation réelle de l'augmentation, KNN/CNN, conversion TinyML et parité C++ restent des
jalons distincts. Les branchements seront effectués lorsque tu passeras aux
essais ou à la collecte, comme convenu.
