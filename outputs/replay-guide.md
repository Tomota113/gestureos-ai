# Relecture des captures — M13 logiciel

L'outil `gestureos.replay` vérifie d'abord les quatre fichiers d'une capture
RAW avec le validateur habituel (identité, CRC, SHA256, séquence et cadence),
puis transmet les échantillons horodatés au **même moteur C++**
`firmware/src/gesture_engine.cpp` que celui compilé pour l'ESP32. Il compile
temporairement ce moteur avec `g++` et écrit le résultat JSON sur la sortie
standard. Les fichiers de capture ne sont jamais modifiés.

Depuis la racine du dépôt, après avoir choisi des valeurs *expérimentales* :

```bash
.venv/bin/python -m gestureos.replay \
  --capture user01/SESSION/ID_CAPTURE \
  --start-energy 0.5 --stop-energy 0.2 --gyro-scale-dps 100 \
  --min-samples 5 --max-samples 256 --quiet-samples 2 \
  --pre-roll-samples 2 --max-gap-us 20000
```

Le chemin suit `data/raw/<sujet>/<session>/<id>/`. Les valeurs numériques
ci-dessus sont **un exemple de test**, non des seuils validés pour le capteur.
Il faut choisir les paramètres à partir des mesures réelles au repos et en
mouvement avant d'évaluer le comportement. Tous les paramètres sont obligatoires
pour éviter une calibration implicite.

La sortie inclut l'empreinte du RAW, les paramètres et les événements `started`,
`completed`, `too_short`, `too_long`, `invalid_sample` et
`unfinished_at_end`. Ce dernier signifie que la capture fixe s'est arrêtée
avant la fin candidate du geste ; ce n'est pas un geste reconnu. Un événement
`completed` décrit seulement une fenêtre détectée. Aucun label, score ML,
mesure de précision ou autorisation d'action n'est calculé. Le replay ne
remplace pas le test continu sur la carte ni la validation des seuils physiques.
