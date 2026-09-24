# Prétraitement GestureOS AI — M4 logiciel

Le pipeline de prétraitement et de caractéristiques est prêt. **43 tests
logiciels réussissent**, exclusivement sur des fixtures artificielles. Aucun
modèle n'est entraîné, aucun résultat de précision n'est revendiqué et le
matériel reste à tester plus tard.

## Commande future

Après une collecte réelle et la création d'un manifeste M3 `ready` :

```bash
.venv/bin/python -m gestureos.preprocess \
  --manifest data/processed/split-001.json \
  --collection-config configs/collection.json \
  --config configs/preprocessing.json \
  --output data/processed/prepared-001.json
```

L'aide fonctionne dès maintenant sans branchement ni données :

```bash
.venv/bin/python -m gestureos.preprocess --help
```

Le manifeste fige les captures et la configuration de collecte. Le chargeur
revérifie SHA256, CRC, CSV, labels et affectations avant utilisation. Il refuse
les captures modifiées, les doublons, les groupes traversant les partitions,
les IDs absents/répétés et les effectifs incohérents. De nouvelles captures
ajoutées après le split n'y entrent pas implicitement : créer un autre manifeste.

Si les RAW ont été déplacés, `--raw-root /nouveau/chemin` permet de les retrouver
sans abandonner les contrôles d'intégrité. Aucun fichier RAW n'est modifié.
Les sorties existantes sont refusées ; choisir un nouveau nom.

## Traitement des séquences

Le contrat `imu-features-v1` transforme chaque geste en **200 points par
défaut**, uniformément répartis entre son premier et son dernier timestamp.
L'interpolation linéaire utilise les timestamps, et non les numéros de ligne.
La durée physique originale est conservée séparément.

Il s'agit d'une normalisation temporelle sur la durée complète : deux gestes
de durées différentes ont la même longueur numérique, mais pas le même pas
de temps physique. Ce n'est donc pas une conversion universelle à 100 Hz.
L'intérêt de ce choix devra être évalué sur les données réelles.

- Les six axes, unités **g** et **degrés/s**, signes et gravité sont conservés.
- Pas de calibration inventée, soustraction automatique de moyenne, padding,
  découpage ou augmentation.
- Les timestamps doivent être strictement croissants et les valeurs finies.
- Si une capture contient plus de points que la cible, le pipeline refuse la
  réduction : aucun filtre anti-repliement n'est encore implémenté. Pour les
  captures longues, augmenter `target_points` jusqu'à 512 dans la configuration.
  Le format de collecte actuel accepte au plus 500 mesures.
- Interpoler davantage de points n'ajoute pas d'information physique.

## Les 64 caractéristiques

Pour chacun des six axes, puis pour les magnitudes accélération et gyroscope :
moyenne, écart-type population, minimum, maximum, RMS, médiane et IQR, soit
56 caractéristiques. Les quantiles utilisent une interpolation linéaire entre
valeurs ordonnées.

S'ajoutent la durée, la RMS de la dérivée du vecteur accélération (en g/s) et
six corrélations : trois paires d'axes accélération, trois paires gyroscope.
Une corrélation à variance nulle vaut zéro par convention. La dérivée inclut
les variations de gravité dues à l'orientation ; ce n'est pas une estimation
isolée de l'accélération de translation du boîtier.

L'ordre exact et les noms sont sauvegardés. FFT, moments d'ordre supérieur et
sélection de variables attendent une justification par les expériences.

## Normalisation sans fuite

La moyenne et l'écart-type de chaque caractéristique sont calculés uniquement
sur les exemples de la partition **train**. Ces paramètres sont ensuite figés
pour validation et test. Un écart-type nul utilise une échelle de 1 ; aucun
paramètre n'est réestimé sur les partitions réservées.

Le fichier produit contient configuration, empreinte du manifeste, provenance
des captures, labels et indices, séquences interpolées, durées, caractéristiques
brutes/standardisées et scaler avec la liste des IDs ayant servi à son ajustement.
Les séquences gardent leurs unités physiques : la normalisation par canal
destinée à un futur CNN n'est pas encore implémentée.

Le traitement est déterministe et conserve actuellement le dataset en mémoire,
ce qui convient au pilote prévu. Une sortie interrompue ou JSON invalide ne
doit pas être considérée comme exploitable ; elle reste sur disque pour examen,
sans écrasement automatique à la reprise.

La prochaine étape est le logiciel d'expérimentation des baselines, avec
vérification des dépendances. L'entraînement et l'évaluation attendront de
vrais exemples ; ces tests logiciels ne démontrent aucune précision gestuelle.
