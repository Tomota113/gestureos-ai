# Collecte GestureOS AI — préparation logicielle

Les branchements seront faits plus tard, comme demandé. **Ce jalon est validé
par compilation et tests logiciels uniquement.** Aucun dataset physique,
modèle entraîné ou résultat de précision n'a encore été produit.

## Ce qui est prêt

- Deux profils ESP32 : test de banc continu et collecte de gestes sur commande.
- Capture fixe configurable de 50 à 500 échantillons, par défaut 200 à 100 Hz.
- Compte à rebours dans le terminal, puis signal `GO`.
- Identifiant unique, label, sujet, session, unités et configuration conservés.
- Contrôles de séquence, cadence, erreurs I2C, saturation et CRC32.
- Sauvegarde sans écrasement ; les captures interrompues restent identifiées.
- Vingt tests Python et tests C++ du parseur/CRC réussis, hors matériel.

## Utilisation maintenant, sans branchement

Depuis la racine du dépôt :

```bash
.venv/bin/python -m gestureos.capture --help
.venv/bin/python -m unittest discover -s tests -v
pio run -d firmware -e esp32dev -e dataset
```

Ces commandes ne flashent pas la carte. Les tests utilisent des fixtures
artificielles clairement séparées des futurs exemples d'apprentissage.
Pour recréer l'environnement s'il manque :

```bash
/usr/bin/python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Quand tu feras les branchements et les vrais tests

Le premier essai restera le test MPU6050 du guide `first-mpu6050-test.md`, afin
de vérifier l'alimentation, le câblage, les axes et la cadence réels. Ensuite,
pour installer le profil de collecte, après identification du port et sauvegarde
du programme précédent si nécessaire :

```bash
pio run -d firmware -e dataset -t upload --upload-port /dev/ttyUSB0
```

Ce flashage remplace le programme dans la carte ; il n'a pas été exécuté ici.

Une future capture réelle :

```bash
.venv/bin/python -m gestureos.capture \
  --port /dev/ttyUSB0 \
  --subject user01 \
  --session session01 \
  --label swipe_left
```

À chaque appel, le port est ouvert exclusivement et la carte réinitialisée pour
obtenir un en-tête frais. Le terminal affiche 3, 2, 1, puis `GO`. La capture ne
démarre qu'après le compte à rebours. Pour changer la durée : `--samples 300`.
Le port peut changer après reconnexion ; le recontrôler à ce moment-là.

La taxonomie pilote dans `configs/collection.json` contient :
`swipe_left`, `swipe_right`, `swipe_up`, `swipe_down`, `circle_clockwise`,
`shake`, ainsi que `unknown` pour les données négatives réelles.

Changer d'ID de session lorsqu'on recommence une séance ; conserver le même
ID pseudonymisé pour une même personne. Les retours du bras au repos doivent
suivre une consigne stable. Il faudra examiner quelques signaux réels avant
d'enregistrer des centaines d'exemples.

## Fichiers obtenus plus tard

```text
data/raw/user01/session01/<capture_id>/
  request.json
  serial.raw
  samples.csv     uniquement si le protocole complet est valide
  result.json
```

Le résultat indique `complete` ou `incomplete`. Un contrôle d'intégrité réussi
ne valide pas à lui seul la justesse du label ou la qualité du geste. Un dossier
sans résultat complet, un log partiel ou une fixture de test ne doit pas entrer
dans l'entraînement. Ne pas supprimer les logs d'échec : ils aident au diagnostic.

L'organisation des dossiers et les IDs permettent ensuite un split par
utilisateur/session, avant toute augmentation, et la conservation des données
brutes originales. Une sauvegarde séparée du disque sera nécessaire dès les
premières captures réelles : Git ignore volontairement `data/raw/`.

Le LCD, la calibration, les modèles et les modes seront ajoutés par les
prochains jalons logiciels. Leurs mesures et réglages réels resteront réservés
à la future séance matérielle.
