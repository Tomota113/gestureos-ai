# Fenêtres gestuelles candidates — M12 logiciel

`firmware/src/gesture_engine.*` est un détecteur de début et de fin de geste
indépendant d'Arduino. Il reçoit des échantillons horodatés (`uint64_t`,
accélération en g avec gravité, gyroscope en degrés/s) et conserve au plus
256 points, plus 32 points de préambule. Pour l'ESP32, instancier l'objet de
façon statique ou globale : ses tableaux internes occupent environ 9 Ko et
ne doivent pas être alloués sur une petite pile de tâche.

L'énergie expérimentale est
`abs(norm(accélération) - 1 g) + norm(gyroscope) / gyroScaleDps`.
Le constructeur exige des seuils explicites : début au-dessus de
`startEnergy`, fin après `quietSamples` échantillons au-dessous de
`stopEnergy`, avec `startEnergy > stopEnergy`. Les bornes de longueur,
le préambule et l'écart maximal entre timestamps sont également explicites.
Une fenêtre trop courte, trop longue, invalide ou avec une interruption du
flux est écartée. Après `Completed`, la fenêtre est lisible jusqu'au
prochain `Started` ou `reset()`.

La formule et les valeurs utilisées dans les tests sont des hypothèses
logicielles, **pas des seuils calibrés pour le MPU6050**. La longueur est
bornée en nombre d'échantillons ; elle ne remplace pas encore une validation
de durée physique et de taux d'échantillonnage sur la carte. Le module ne
rééchantillonne pas, ne classe pas les gestes et ne déclenche aucune action.
Il est compilé dans les deux profils PlatformIO, mais n'est pas encore
raccordé à `Imu::read()` ni à un modèle. Avant intégration physique, il faudra
mesurer le bruit/biais au repos, ajuster les seuils, vérifier les pertes
et le délai, puis garder la politique `action_authorized` à la sortie d'un
modèle réellement validé.
