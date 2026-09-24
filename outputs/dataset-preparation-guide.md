# Préparation du dataset — jalon logiciel M3

La lecture des captures et les splits sont implémentés. **30 tests logiciels
passent sur des fixtures artificielles**. Aucune donnée physique ou performance
ML n'a été produite, et aucun branchement n'est requis maintenant.

## Utilisation future

Après collecte de vraies captures et depuis la racine du projet :

```bash
.venv/bin/python -m gestureos.prepare \
  --root data/raw \
  --config configs/collection.json \
  --group-by session --seed 42 \
  --output data/processed/split-001.json
```

L'aide est disponible sans dataset :

```bash
.venv/bin/python -m gestureos.prepare --help
```

Le programme lit les RAW sans les modifier et refuse d'écraser un manifeste
existant ou d'écrire sa sortie dans le dossier RAW.

## Captures acceptées

Chaque dossier doit correspondre à `sujet/session/capture_id`, avec ses quatre
fichiers de collecte. Le chargeur vérifie identité, label, provenance matérielle
déclarée, capture complète, unités/configuration, SHA256, protocole et CRC du
flux brut, ainsi que l'égalité des valeurs CSV avec ce flux. Les métriques
enregistrées sont recalculées depuis les RAW.

Les fixtures déclarées synthétiques, captures partielles, liens symboliques,
données transformées ou dérivées et fichiers incohérents sont refusés. Des
copies avec de nouveaux identifiants sont détectées par une empreinte du signal,
indépendante du temps absolu. Les deux copies sont signalées ; rien n'est supprimé.
Un signal exactement identique peut aussi être une répétition légitime : examiner
le diagnostic avant toute exclusion, sans contourner le contrôle automatiquement.

Ces vérifications détectent des incohérences ; elles ne prouvent pas l'origine
physique si quelqu'un falsifie toutes les métadonnées ni la justesse d'un label.

## Partitions sans mélange des groupes

- `--group-by session` : une paire sujet/session reste dans une seule partition.
  Un même sujet peut être présent dans plusieurs partitions ; cela mesure la
  généralisation entre séances, pas entre utilisateurs inconnus.
- `--group-by subject` : toutes les séances d'un sujet restent ensemble. Ce
  mode exige au moins trois sujets pour train, validation et test.

Chaque label de la configuration, y compris `unknown`, doit exister dans au
moins trois groupes et apparaître dans chaque partition retenue. Enregistrer
tous les exemples pendant une seule séance ne permet donc pas ce split.

La cible est 60/20/20. Les groupes restent indivisibles : proportions réelles
approximatives, effectifs indiqués dans le manifeste. Une recherche bornée à
512 propositions utilise seulement labels et identités, jamais les signaux ou
les scores d'un modèle. Même entrée, même seed et même configuration donnent
les mêmes affectations, indépendamment de l'ordre des dossiers.

Si aucune proposition admissible n'est trouvée, le programme l'annonce sans
affirmer que toute solution est mathématiquement impossible. Il ne bascule
jamais vers un découpage aléatoire des lignes qui mélangerait les groupes.

## Résultats et reprise

Le manifeste conserve la taxonomie, son empreinte, les IDs, les chemins,
empreintes de fichiers et de signaux, les rejets, la seed et les partitions.

- Code 0, `status: ready` : manifeste et partitions disponibles.
- Code 1, `status: blocked` : diagnostic sauvegardé, aucune partition utilisable.
  Cela inclut toute capture rejetée et les groupes insuffisants.
- Code 2 : erreur d'arguments, dossier absent ou sortie déjà existante.

Le futur entraînement devra revérifier les empreintes avant d'utiliser ce
manifeste. Les RAW et partitions finales restent conservés ; scaler, sélection
de variables et augmentation seront ajustés sur le train uniquement au prochain
jalon. Le test final ne recevra jamais d'exemples augmentés.
