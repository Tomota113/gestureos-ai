# Revue Antigravity — phase 0

Requête bornée via `agy --mode plan --print-timeout 60s --output-format text -p`.
Code retour 0. Pas d’édition déléguée. Modèle laissé sur le réglage par défaut ;
quota non mesuré. La revue a précédé le branchement USB et ses hypothèses
d’absence de carte ne décrivent donc plus l’état final.

## Arbitrages du responsable

- Carte effectivement identifiée ensuite par ROM : ESP32-D0WDQ6, 4 Mo.
- L’utilisateur appartient déjà au groupe dialout ; ne pas modifier les droits.
- Valider le module capteur avant alimentation ; ne jamais interpréter AD0
  vers VCC comme une permission de lui appliquer 5 V. Niveau haut 3,3 V maximum.
- Conserver polling DATA_RDY, I2C 100 kHz et UART 230400 pour le banc minimal.
  INT/FIFO et 400 kHz seront évalués si les mesures le justifient.
- Horodatage ESP32 64 bits retenu pour éviter le débordement de micros 32 bits.
- Une pose statique ne suffit pas à distinguer tous les offsets accéléromètre
  de la gravité : ne pas soustraire aveuglément la moyenne des trois axes.
- Revue conceptuelle uniquement : aucune précision ML ni validation matérielle.

## Réponse originale de l’agent (avis, non preuve de mesure)

## Revue critique indépendante — GestureOS AI (Phase 0)

### 1. Risques majeurs
* **Blocage matériel & USB :** Aucun ESP32 n'est détecté. Les causes probables sont l'utilisation d'un câble « charge uniquement » (sans lignes data), l'absence d'autorisations sur le port série sous Linux (groupe `dialout`), un pilote UART manquant (CH340/CP2102) ou une puce hors tension.
* **Inadéquation de cible PlatformIO :** Forcer `esp32dev` est dangereux tant que le composant physique n'est pas identifié. S'il s'agit d'un ESP32-S2, S3 ou C3, les broches par défaut pour l'I2C ne sont pas GPIO 21 et 22, ce qui provoquera un échec d'initialisation du bus.
* **Alimentation et niveaux logiques MPU6050 :** Les breakouts classiques (ex. GY-521) disposent généralement d'un régulateur LDO 3,3 V et de résistances pull-up I2C pré-soudées. Si alimenté en 3,3 V sur `VCC`, la chute de tension du LDO peut sous-alimenter le capteur. À l'inverse, si alimenté en 5 V alors que les pull-ups tirent vers `VCC`, du 5 V sera injecté sur les GPIO de l'ESP32.
* **Saturation du lien série à 100 Hz :** L'envoi de lignes CSV ASCII horodatées à 100 Hz de manière synchrone bloque la boucle d'exécution si le baudrate UART est trop bas, dégradant la fréquence d'échantillonnage et créant des pertes.

---

### 2. Corrections et compléments pour le test Phase 0
* **Identification préalable de la puce :** Diagnostiquer la connexion USB (`dmesg`, `lsusb`) et adapter la directive `board` dans `platformio.ini` au modèle exact avant tout flashage.
* **Validation du schéma du module capteur :** Mesurer ou identifier le câblage du breakout : alimenter en 5 V seulement si les pull-ups I2C sont tirés au 3,3 V interne du régulateur ; sinon alimenter directement la broche 3,3 V (si exposée). Vérifier le câblage physique de `AD0` pour fixer l'adresse I2C (0x68 sur GND, 0x69 sur VCC).
* **Interruption matérielle plutôt que scrutation :** Câbler la broche `INT` du MPU6050 sur un GPIO externe avec `attachInterrupt()` pour capturer `DATA_RDY` sans solliciter inutilement le bus I2C par polling.
* **Optimisation de la communication :** Configurer l'I2C à 400 kHz (Fast Mode). Régler l'UART à haut débit (≥ 115 200 bauds, idéalement 921 600 bauds) et horodater via `micros()` pour mesurer précisément la gigue (jitter).
* **Vérification de plage dynamique :** Contrôler lors du test d'axes l'absence de saturation sur les échelles configurées (±4g, ±500°/s).

---

### 3. Gestes potentiellement confondables (MVP)
* **`left` vs `right` et `up` vs `down` :** Forte ambiguïté si la fenêtre temporelle inclut le retour du bras à sa position de repos, qui présente une accélération et une vitesse angulaire inverses du geste initial.
* **`circle_clockwise` vs gestes directionnels :** Un cercle décompose séquentiellement les accélérations des quatre axes cardinaux. Une segmentation ou un fenêtrage partiel risque d'isoler un arc de cercle et de le classer à tort en `left`, `right`, `up` ou `down`.
* **`shake` :** Risque de saturation des plages ±4g et ±500°/s. Sa variabilité inter-essais et sa signature haute fréquence peuvent se confondre avec des mouvements parasites ou du bruit issu des données négatives.

---

### 4. Conditions préalables indispensables avant de passer au ML
1. **Validation matérielle stricte du flux de données :** Test de 60 secondes validé sans erreur d'arbitrage/timeout I2C, sans perte de paquets série, avec une cadence de $100 \pm 2\text{ Hz}$ et une gigue temporelle maîtrisée.
2. **Caractérisation du bruit et calibration :** Détermination des offsets statiques (biais accéléromètre et gyroscope au repos) et fixation rigide du capteur pour éliminer les vibrations mécaniques parasites.
3. **Protocole de segmentation et déclenchement :** Choix clair entre fenêtrage glissant continu ou déclenchement par seuil d'énergie, incluant une gestion explicite de la phase de retour au repos.
4. **Stratégie de partitionnement des données :** Définir et verrouiller une séparation stricte par session et par sujet (ex. Leave-One-Subject-Out) pour la validation/test avant toute collecte massive.
5. **Cahier des charges mémoire/latence :** Fixer les limites d'empreinte RAM et Flash allouées au futur moteur d'inférence sur l'ESP32 afin d'adapter la taille du modèle en amont.
