# Augmentation IMU optionnelle — jalon M9 logiciel

L'entraînement peut créer des copies **uniquement dans la partition train** avec
`--augmentation-config configs/augmentation-rotation-v1.json`. Sans cette option,
le comportement M5 reste inchangé. La configuration d'exemple demande une copie
par capture, avec une rotation aléatoire reproductible de ±3° autour de l'axe Z
du repère capteur. La limite logicielle est ±5°. La même rotation s'applique à
tous les instants et aux deux vecteurs 3D (accélération avec gravité et
gyroscope) ; durée et normes des vecteurs restent inchangées. Les features sont
recalculées ; le scaler demeure celui des captures train originales.

La rotation simule une petite différence d'orientation du capteur. La
conservation du label pour chaque geste réel reste une **hypothèse à vérifier**.
Les amplitudes de l'exemple sont des paramètres d'essai, pas des valeurs
mesurées ou optimisées. Aucune autre transformation n'est activée.

Le fichier `augmentation.json` de chaque expérience activée contient la
configuration, le nombre de copies et, pour chaque copie, `capture_id`,
`parent_capture_id`, angle et partition. Les copies n'entrent ni en validation
ni en test, ne sont jamais écrites dans RAW et ne modifient pas le dataset
préparé. Les prédictions et métriques restent calculées sur la validation réelle
du même split ; le test final reste réservé.

Quand assez de captures réelles et de groupes distincts existeront, comparer
deux **nouveaux** dossiers d'expérience, l'un sans option et l'autre avec
`--augmentation-config`, sur le même manifeste. Vérifier alors les métriques
par geste et la stabilité entre sujets/séances avant d'adopter l'augmentation.
Les tests actuels emploient des estimateurs factices : ils établissent le
fonctionnement logiciel, pas un gain de précision.
