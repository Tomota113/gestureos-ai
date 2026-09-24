# GestureOS AI — audit de phase 0

Audit du 24 septembre 2026. La préparation minimale est réalisée ; le premier
jalon matériel reste à valider après câblage par l'utilisateur.

## Environnement observé

| Élément | Constat vérifié |
|---|---|
| OS | Ubuntu 26.04 LTS, x86_64, noyau 7.0.0-31-generic |
| Dossier | `/home/ibrahim-tomota/Documents/Codex/2026-09-24/tu` |
| État initial | Uniquement `work/` et `outputs/`, pas de dépôt Git |
| Git | 2.53.0 ; dépôt local initialisé sur `main`, aucun remote ajouté |
| Python par défaut | 3.14.4 dans le venv interne PlatformIO |
| Python du projet | `.venv`, créé depuis `/usr/bin/python3` 3.14.4 |
| pip initial | 26.2.1 dans PlatformIO ; environnement projet séparé |
| Acquisition Python | pyserial 3.5 installé ; `pip check` passe |
| ML dans `.venv` | numpy/scipy/pandas/sklearn/TensorFlow/PyTorch/matplotlib absents |
| PlatformIO | 6.2.0 ; plateforme ESP32 7.0.1 et Arduino ESP32 2.0.17 installés |
| Toolchain ESP32 | Xtensa 8.4.0+2021r2-patch5 ; esptool 4.11.0 |
| Arduino CLI / ESP-IDF CLI | `arduino-cli`, `idf.py` non trouvés ; `IDF_PATH` absent |
| CMake / Ninja | Non trouvés dans PATH ; inutiles pour ce premier build Arduino |
| USB initial | Aucun périphérique ESP32 détecté |
| USB après branchement | CP2102, `/dev/ttyUSB0`, accès autorisé, utilisateur dans `dialout` |
| Carte, interrogation ROM | ESP32-D0WDQ6 révision 1.0, 240 MHz, cristal 40 MHz, Flash 4 Mo |
| LCD | L'utilisateur confirme un LCD 1602 à 16 broches |
| MPU6050 | Référence précise et câblage non vérifiés ; utilisateur câblera ensuite |

Les détections USB et ROM sont des observations matérielles réelles. Aucun
flashage, test MPU6050, test LCD ou test d'actionneur n'a été effectué.

## Travail réalisé et vérification

- Mémoire persistante `.agent/` créée dès le début, brief original archivé,
  consignes de reprise dans `AGENTS.md` et checkpoints Git locaux.
- Firmware minimal modulaire compilé avec succès : acquisition I2C, contrôle
  d'identité et de configuration, flux série horodaté avec compteur d'erreurs.
- Rapport du linker : **21 808 octets de RAM statique**, **287 585 octets de
  Flash pour l'application**. Ce ne sont ni la RAM d'exécution mesurée ni
  l'empreinte d'un modèle TinyML. Partition application : 1 310 720 octets.
- Six tests logiciels passent : flux régulier, perte série, trou temporel
  malgré compteur continu, redémarrage, corruption/NaN/capture courte et
  erreurs I2C/saturation. Les fixtures sont artificielles et ne servent pas au ML.
- Script de banc prêt : conservation exclusive du log, rapport JSON, cadence,
  discontinuités, saturation, moyenne et dispersion des axes.

## Collaboration Antigravity et quotas

`/home/ibrahim-tomota/.local/bin/agy` existe. Son aide confirme `--print`,
`--mode plan`, `--print-timeout` et `models`. `agy models` et une revue de
conception en mode plan ont réussi (code retour 0). La revue a été journalisée
puis analysée ; aucun fichier du projet n'a été confié en écriture à cet agent.

Les points retenus concernent l'identification de carte, la tension du module,
le débit série et la confusion entre geste et retour au repos. Nous conservons
pour ce premier test un polling DATA_RDY à I2C 100 kHz et UART 230400 bauds ;
INT/FIFO seront envisagés si les mesures montrent des pertes, avant collecte
massive. Les suggestions d'Antigravity ne sont pas des validations matérielles.

L'aide consultée ne prouve pas la disponibilité de `/usage`, `/quota` ou
`/resume` : ces commandes n'ont pas été utilisées, quota Antigravity inconnu.
L'outil officiel Codex indiquait au début 6 % utilisés sur la fenêtre de 5 h et
35 % sur la semaine. C'est un instantané. Aucun reset de quota, achat ou
changement de compte effectué.

## Architecture proposée

Le dépôt séparera `firmware/` (capteur, segmentation, IA, LCD, modes,
actionneurs), `src/gestureos/` (pipeline Python), `scripts/`, `configs/`,
`data/`, `models/`, `experiments/`, `reports/`, `tests/` et `docs/`.
L'arborescence détaillée figure dans `docs/architecture.md`.

Le trajet principal sera : acquisition → segmentation → prétraitement partagé
→ modèle local → rejet UNKNOWN → interprétation selon mode → action/UI.
Le trajet expérimental sera : données réelles → split → entraînement et
augmentation du train → validation → test réel final → export embarqué.
Les autres modules n'ont pas été créés prématurément.

## Risques et taxonomie initiale

L'IMU mesure accélération et rotation ; elle ne fournit pas directement une
trajectoire 3D absolue fiable. Une petite dérive intégrée peut déformer une
reconstruction. Le projet classera donc des signatures temporelles, sans
promettre de tracer les lettres dans l'espace.

| Classes | Risque et décision de conception |
|---|---|
| left/right/up/down | Pilote prioritaire ; fixer repère du capteur, prise et retour au repos |
| quatre diagonales | Extension après directions ; variations d'angle proches des cardinales |
| circle CW/CCW | Commencer par horaire ; définir plan et point de vue, puis sens opposé |
| Z/X/V/triangle | Étudier séparément ; le X exige deux traits et un retour conventionnel |
| shake/double_shake | Garder shake au pilote ; nombre/durée facilement confondus, double plutôt futur événement séquentiel |
| wrist rotate left/right | Extension pertinente, amplitudes et retour standardisés ; confusion avec rotation large |
| push/pull | Axe avant/arrière explicite ; départ et freinage peuvent inverser les signatures |
| double_tap | Différer : choc/couplage au boîtier, bande passante et saturation |
| tilt holds | États d'orientation persistants distincts des gestes brefs, confusion avec position de repos |
| full_rotation | Différer : recouvrement avec cercle/rotation de poignet et dérive |

La faisabilité de 15–20 classes sera décidée sur matrices de confusion et
tests entre sessions/utilisateurs. 90–95 % reste une cible, pas une garantie.

Les autres risques principaux et leur réponse :

- **UNKNOWN** : la probabilité maximale seule n'est pas une preuve de
  familiarité. Collecter repos, transitions et mouvements hors classes ;
  choisir seuil et marge sur validation, puis mesurer les faux acceptés sur
  des inconnus réservés. La classe explicite négative est à comparer, pas à
  considérer comme une couverture exhaustive du monde ouvert.
- **Fuite de données** : grouper par utilisateur/session, garder les fenêtres
  parentes ensemble, ajuster scaler et augmentation sur train seulement.
- **Données externes** : recherche et audit licence/axes/unités/fréquence
  prévus avant tout import. Aucun dataset externe téléchargé ni mélangé.
- **Alimentation** : USB suffit comme hypothèse au test ESP32 + IMU, à vérifier.
  Servo, stepper et relais restent hors montage initial ; leur courant peut
  perturber l'acquisition. Pas d'alimentation moteur via GPIO/3V3.
- **LCD 16 broches** : vérifier référence, logique et rétroéclairage avant
  câblage ; ne pas supposer un module I2C présent. R/W à GND pour une interface
  en écriture seule, si le contrôleur confirme ce mode.
- **Ressources ML** : Python 3.14 n'est pas supposé compatible avec toutes
  les futures roues ML. Vérifier versions disponibles avant installation et
  isoler un autre environnement si nécessaire ; mesurer RAM/Flash/latence.
- **BLE HID** : puce compatible Bluetooth détectée, application HID non testée.
- **Segmentation** : les limites début/fin changent le signal reconnu ; comparer
  acquisition fixe et automatique, notamment pendant le retour au repos.

## Premier milestone concret : M1

Valider **ESP32 + MPU6050 → six axes cohérents → flux réel stable à 100 Hz**.
Le guide séparé contient le câblage conditionné au module réel et les commandes.

Acceptation prévue : 60 s de temps capteur, taux moyen 98–102 Hz, au moins
95 % des intervalles entre 8 et 12 ms, aucun intervalle supérieur à 20 ms,
aucune erreur I2C ni discontinuité série observée, pas de saturation. Examiner
aussi un repos de 10 s et les axes dans des orientations contrôlées ; la norme
d'accélération au repos doit être proche de 1 g, sans soustraire la gravité.
Ce sont des critères proposés, **pas des résultats obtenus**.

Après succès : documenter biais et orientation, puis aborder LCD et logger
labellisé. Si échec : diagnostiquer alimentation, adresse, axes et timing avant
de collecter le pilote. L'utilisateur a demandé de faire les branchements plus
tard ; nous nous arrêtons au jalon logiciel prêt à tester.

## Sources primaires vérifiées

- Le profil de compilation et ses limites proviennent de [PlatformIO — esp32dev](https://docs.platformio.org/en/stable/boards/espressif32/esp32dev.html), complété par les manifests locaux et le build réel.
- Les réglages de cadence, plages et registres se fondent sur le [registre MPU6000/6050 de TDK](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf).
- Les contraintes électriques de la puce se vérifient sur [TDK — MPU6050](https://product.tdk.com/en/search/sensor/mortion-inertial/imu/info?part_no=MPU-6050) ; elles ne remplacent pas le schéma du module acheté.
- Les GPIO et l'alimentation sont à contrôler avec la [fiche ESP32](https://documentation.espressif.com/esp32_datasheet_en.html) et le [guide DevKitC](https://documentation.espressif.com/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html), en tenant compte de la carte réelle.
