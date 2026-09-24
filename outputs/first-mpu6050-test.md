# Premier test réel — ESP32 + MPU6050

**Prêt côté logiciel, non exécuté sur le capteur.** La carte a été identifiée
comme ESP32-D0WDQ6 avec Flash 4 Mo sur `/dev/ttyUSB0`. Le programme actuel de la
carte est conservé. L'utilisateur fera le câblage ultérieurement.

## 1. Matériel et alimentation à confirmer

La référence du module MPU6050 reste inconnue. La puce MPU6050 seule fonctionne
sous 2,375–3,46 V ; l'entrée VCC d'un module dépend de son régulateur et de ses
résistances I2C. Ne pas confondre la tension de la puce et celle du module.
Voir [la fiche TDK](https://product.tdk.com/en/search/sensor/mortion-inertial/imu/info?part_no=MPU-6050).

Le tableau suivant est le plan pour **un module acceptant effectivement 3,3 V
sur VCC et dont SDA/SCL sont tirées vers 3,3 V**. Avant de l'appliquer, vérifier
le marquage et le schéma du module. Si ces propriétés restent inconnues, fournir
sa référence ou une photo lisible avant mise sous tension. Un GY-521 peut avoir
des variantes ; son nom seul ne documente pas tous ses composants.

Ne pas essayer du 5 V pour corriger un échec d'initialisation. Certains modules
ont une chute de tension de régulateur qui exige une vérification spécifique.
Les GPIO ESP32 doivent rester dans leurs limites 3,3 V, selon [Espressif](https://documentation.espressif.com/esp32_datasheet_en.html).

## 2. Plan de câblage du test

Débrancher l'USB pendant les branchements. Les nombres ci-dessous désignent
les **GPIO sérigraphiés**, pas la position de la broche sur le connecteur.

| Composant | Broche | Broche ESP32 | Alimentation/niveau | Notes |
|---|---|---|---|---|
| Module MPU6050 compatible 3,3 V | VCC | 3V3 | 3,3 V uniquement selon condition ci-dessus | Référence à vérifier avant branchement |
| MPU6050 | GND | GND | Masse commune | Liaison indispensable |
| MPU6050 | SDA | GPIO21 | I2C 3,3 V | Fils courts ; pull-ups vers 3,3 V |
| MPU6050 | SCL | GPIO22 | I2C 3,3 V | Bus initial à 100 kHz |
| MPU6050 | AD0 | GND | Niveau bas | Adresse 0x68 ; firmware sonde aussi 0x69 |
| MPU6050 | INT | Non connecté | — | Polling DATA_RDY pour ce premier test |
| MPU6050 | XDA / XCL | Non connectées | — | Bus auxiliaire inutilisé |
| ESP32 DevKit | USB | PC | Alimentation et données USB | Une seule source d'alimentation |

Si aucune résistance de rappel I2C n'est présente, prévoir une résistance
de l'ordre de 4,7 kΩ de SDA vers 3V3 et une de SCL vers 3V3, après vérification
des valeurs disponibles. Ne pas empiler aveuglément plusieurs jeux de pull-ups.

**Montage de ce test : uniquement ESP32 + MPU6050.** Garder LCD, servo, stepper,
relais, HC-SR04 et autres capteurs déconnectés. Le LCD 1602 à 16 broches sera
utilisé à la phase 3 ; aucun achat d'un modèle I2C n'est nécessaire maintenant.
Ne jamais relier directement une sortie Echo 5 V de HC-SR04 à un GPIO ESP32.

## 3. Retrouver l'état et le port

Depuis la racine du projet :

```bash
git status
git log --oneline -n 5
ls -l /dev/serial/by-id/
.venv/bin/python -m serial.tools.list_ports -v
```

Le lien actuellement observé est :

```text
/dev/serial/by-id/usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0
```

Le port peut changer après reconnexion. Ne pas sélectionner un `/dev/ttyS*`
inconnu. Fermer tout moniteur série concurrent avant capture ou upload.

## 4. Construire puis charger le test

La commande suivante a déjà réussi :

```bash
pio run -d firmware
```

Avant le premier flashage, inspecter le firmware présent et conserver une
sauvegarde si son contenu doit être préservé. La reprise assistée prévoit cette
étape ; aucun flashage n'a été effectué pendant l'audit.

Une fois le câblage confirmé et l'ancien programme sauvegardé si nécessaire :

```bash
pio run -d firmware -t upload --upload-port /dev/ttyUSB0
```

Cette commande **remplace l'application actuellement dans la carte**. Elle n'a
pas encore été exécutée. Le premier essai vérifiera l'initialisation du capteur,
pas un geste reconnu par IA.

## 5. Mesurer et conserver 60 secondes

Créer une capture avec des noms inutilisés. Le script refuse tout écrasement
et réinitialise la carte par DTR/RTS au début pour recevoir le protocole complet.

```bash
.venv/bin/python scripts/check_stream.py \
  --port /dev/ttyUSB0 \
  --seconds 60 --rate 100 \
  --output reports/hardware/bench-001.serial \
  --report reports/hardware/bench-001.json
```

Attendre environ une minute. Le flux est sauvegardé à chaque ligne. À 100 Hz,
environ 6 001 lignes de mesures couvrent 60 s entre première et dernière mesure.
Le script s'arrête au plus tard après 75 s hors initialisation du port.

Le format des lignes de données est :

```text
seq,timestamp_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,i2c_errors
```

Les lignes `#` portent le protocole et les diagnostics. `timestamp_us` est
l'instant de lecture sur l'ESP32, sur 64 bits ; il ne correspond pas à
l'horodatage USB du PC ni à une interruption matérielle de l'IMU.

Les valeurs sont en **g** et **degrés/s**, non calibrées, avec gravité conservée.
La configuration centrale est `firmware/include/config.h` ; changer
`kSampleRateHz` de 100 à 50 pour une comparaison ultérieure, puis recompiler,
reflasher et lancer le vérificateur avec `--rate 50`.

## 6. Critères d'acceptation de M1

Le rapport doit indiquer `passed: true` pour l'intégrité du flux :

- durée capteur ≥ 60 s ; fréquence moyenne 98–102 Hz ;
- au moins 95 % des intervalles dans 8–12 ms, aucun au-delà de 20 ms ;
- aucun compteur de séquence discontinu, redémarrage ou ligne corrompue ;
- aucune erreur I2C rapportée ; aucun axe proche de sa pleine échelle.

Puis vérifier physiquement :

1. **Repos 10 s** : noter moyenne et bruit ; norme d'accélération proche de 1 g,
   gyroscope près de zéro avec biais mesuré. Écart important : investiguer,
   ne pas masquer le défaut avec une normalisation.
2. **Six orientations statiques** : pour chaque axe, orienter alternativement
   le sens positif puis négatif vers le haut ; confirmer axe, signe et ordre.
3. **Rotations lentes** : confirmer les axes et signes gyroscopiques ; consigner
   le repère qui sera utilisé pour définir gauche/droite/haut/bas.
4. **Mouvements de test** : contrôler saturation et gaps ; les plages actuelles
   sont ±4 g et ±500 °/s. Ce ne sont pas encore des exemples ML labellisés.
5. **Absence de capteur**, lors d'un essai séparé et recâblé hors tension :
   firmware en erreur explicite, aucune fausse ligne de mesure valide.

Le firmware n'utilise pas encore FIFO ni compteur d'interruptions. Un rapport
valide caractérise le flux observé ; il ne prouve pas absolument l'absence de
tout échantillon interne manqué. Si les timings échouent, évaluer INT/FIFO
avant la collecte massive. Aucun offset accéléromètre complet ne peut être
estimé honnêtement en soustrayant toute la moyenne d'une seule pose.

## 7. En cas d'échec

| Symptôme | Diagnostic suivant |
|---|---|
| Port absent | Câble de données, alimentation, `lsusb`, droits du port |
| `imu_init` | Référence, VCC réel, masse, SDA/SCL, AD0, pull-ups et WHO_AM_I |
| Pas de protocole après capture | Réinitialisation EN, bon firmware/port, UART 230400 ; conserver le log |
| Erreurs I2C | Fils courts, alimentation, pull-ups, timeout ; garder l'erreur visible |
| Trous/cadence incorrecte | Charge série/I2C, resets, cadence du capteur ; puis INT/FIFO si besoin |
| Saturation | Adapter plage et facteurs de conversion ensemble, refaire le test |

Ne pas interpréter une erreur de capteur ou de port comme un problème de quota.
Préserver le log brut et mettre à jour `.agent/` avant de corriger. Ne pas
commencer la collecte de gestes tant que M1 n'est pas réellement validé.
