# Sélection des seuils UNKNOWN — M7

L’outil M7 choisit une **politique expérimentale** à partir de la partition de
validation d’un manifeste figé et d’un modèle local déjà entraîné. Il ne réentraîne
pas le modèle et ne lit aucune capture de la partition de test pour calculer les
seuils. Il ne réalise aucune calibration probabiliste.

**État actuel : aucun modèle de gestes entraîné n’est disponible.** Les quelques
captures physiques connues ne couvrent pas les classes nécessaires. Les tests
du logiciel emploient des scores calculables à la main et des estimateurs
factices ; ils ne mesurent pas la qualité de reconnaissance du projet.

## Avant une sélection réelle

Collecter les gestes connus et des mouvements `unknown` sur suffisamment de
séances ou de sujets distincts pour obtenir un manifeste valide et un modèle
entraîné. Conserver le test final à part. Lire les guides de [préparation du
dataset](dataset-preparation-guide.md) et des [baselines](baselines-guide.md).

Renseigner explicitement les objectifs dans une copie de
`configs/threshold_search.json` :

- `max_unknown_false_accept_rate` : fraction maximale d’inconnus acceptés sur
  la validation, entre 0 et 1 ;
- `min_known_correct_accept_rate` : fraction minimale de captures connues
  acceptées avec la bonne étiquette, entre 0 et 1 ;
- `max_candidates_per_axis` : nombre maximal de valeurs observées examinées
  par seuil, de 2 à 256.

Le fichier livré laisse les deux objectifs à `null` afin d’empêcher une
sélection fondée sur des valeurs arbitraires. Le taux de faux acceptés a pour
dénominateur les captures `unknown` de validation ; le taux de connus
correctement acceptés a pour dénominateur **toutes** les captures connues de
validation. Les erreurs connues acceptées et les connus rejetés sont rapportés
séparément. Les dénominateurs sont enregistrés avec chaque résultat : un faible
nombre de captures rend ces taux fragiles. Aucun taux de faux déclenchements
par minute n’est calculé sans enregistrement continu réel.

## Exécution future

La commande suivante illustre les chemins attendus après la collecte et
l’entraînement ; elle ne désigne pas des artefacts déjà présents :

```bash
.venv/bin/python -m gestureos.select_thresholds \
  --manifest data/processed/manifest.json \
  --prepared data/processed/prepared.json \
  --experiment experiments/baselines-v1 \
  --model random_forest \
  --config configs/threshold_search.json \
  --output reports/thresholds/selection-001
```

Utiliser `--raw-root` si les RAW ont été déplacés. Le modèle doit provenir
d’une expérience locale de confiance, car son bundle joblib est désérialisé.
Le chargeur revérifie les fichiers RAW, le dataset préparé, le manifeste, le
modèle, leurs empreintes et leurs contrats. La sortie doit être un nouveau
dossier situé hors des RAW et de l’expérience. Un dossier existant est refusé.

Le dossier de sortie contient la configuration, l’identifiant du modèle,
les scores et décisions de validation, les métriques et, seulement si les
contraintes sont satisfaites, `policy.json`. Sans captures connues et inconnues
sur validation ou sans paire de seuils admissible, le résultat est `blocked`
et aucune politique n’est créée.

La recherche teste les valeurs de score et de marge observées sur validation.
Si leur nombre dépasse le plafond configuré, elle prend un sous-ensemble
déterministe incluant les extrêmes et marque la recherche `exact_observed_breakpoints:
false`. La politique retenue est liée aux empreintes du modèle, du manifeste
et des IDs de validation ; une inférence sur un modèle ou split différent la
refuse. Son statut reste `experimental`, `action_authorized` reste faux, et
`test_evaluated`, `probability_calibrated` et `deployment_approved` restent
faux. Une fois le développement figé, il faudra évaluer une seule fois sur le
test réservé, puis mesurer le fonctionnement continu et le matériel séparément.
