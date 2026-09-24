Tu es mon **Lead Engineer IA embarquée / TinyML / Robotique**, responsable de concevoir et implémenter entièrement mon projet de stage.

# 1. CONTEXTE DU PROJET

Je suis étudiant en L2 Intelligence Artificielle et actuellement en stage de robotique.

Je dois réaliser un projet suffisamment sérieux pour être présenté :
- à des personnes techniques ;
- à des personnes non techniques ;
- devant un professeur/jury qui doit clairement voir mes compétences en intelligence artificielle.

Je ne veux PAS un simple montage Arduino basé sur des `if/else`.

Le projet choisi est :

# GestureOS AI
## Système embarqué intelligent de reconnaissance gestuelle multimode basé sur TinyML

L'idée est de tenir un boîtier / une “baguette” contenant un MPU6050.

Le système analyse en temps réel les mouvements de la main grâce aux 6 signaux :

- ax
- ay
- az
- gx
- gy
- gz

Un modèle de Machine Learning / TinyML doit reconnaître les gestes puis les interpréter différemment selon le mode actif.

Le système doit fonctionner principalement sur ESP32.

L'objectif final est d'avoir une démonstration spectaculaire mais un projet techniquement sérieux.

---

# 2. MATÉRIEL DISPONIBLE

Matériel principal :

- ESP32 NodeMCU / DevKit
- MPU6050 accéléromètre + gyroscope
- LCD 1602
- Servomoteur SG90
- Stepper 28BYJ-48
- Driver ULN2003
- HC-SR04
- Joystick analogique
- Clavier matriciel 4x4
- Récepteur infrarouge + télécommande IR
- DHT11
- LDR
- capteur sonore / microphone
- potentiomètre 10k
- tilt switch
- capteur de flamme / IR
- capteur de niveau d'eau
- relais 5V
- buzzer actif
- buzzer passif
- LEDs simples
- LED RGB
- boutons
- 74HC595
- breadboard
- résistances
- transistors
- diodes
- jumpers

IMPORTANT :

Je N'AI PAS d'écran OLED.

L'interface visuelle principale doit être conçue pour un :

LCD 1602 — 16 caractères × 2 lignes.

Je ne veux PAS dépendre du moteur DC car je n'ai actuellement pas une alimentation externe satisfaisante pour lui.

Le projet doit fonctionner autant que possible avec l'ESP32 alimenté en USB.

Ne suppose jamais qu'un composant existe s'il n'est pas dans cette liste.

---

# 3. OBJECTIF PRINCIPAL

Créer un système capable de reconnaître idéalement :

15 à 20 gestes différents de manière fiable.

Si les résultats sont excellents, nous pourrons essayer 20 à 25 gestes.

Je préfère :

20 gestes avec 90–95 % de précision

plutôt que :

40 gestes avec une reconnaissance médiocre.

---

# 4. GESTES INITIAUX À ÉTUDIER

Commence par analyser la faisabilité de ces classes :

## Directions

1. swipe_left
2. swipe_right
3. swipe_up
4. swipe_down
5. diagonal_up_left
6. diagonal_up_right
7. diagonal_down_left
8. diagonal_down_right

## Formes / trajectoires

9. circle_clockwise
10. circle_counterclockwise
11. letter_z
12. letter_x
13. letter_v
14. triangle

## Gestes dynamiques

15. shake
16. double_shake
17. wrist_rotate_left
18. wrist_rotate_right
19. push_forward
20. pull_backward

Classes supplémentaires à tester seulement si techniquement pertinentes :

21. double_tap
22. tilt_left_hold
23. tilt_right_hold
24. full_rotation

IMPORTANT :

Tu dois analyser les risques de confusion entre classes.

Si certaines classes sont trop proches avec uniquement un MPU6050, propose une meilleure taxonomie.

Ne garde pas une classe simplement parce que je l'ai proposée.

---

# 5. CLASSE UNKNOWN / REJET

Le système ne doit JAMAIS être obligé de choisir un geste connu.

Je veux une vraie stratégie de rejet.

Exemple :

circle = 0.32
right = 0.29
shake = 0.20

=> UNKNOWN

Étudier plusieurs méthodes :

- seuil de confiance ;
- margin entre top-1 et top-2 ;
- classe UNKNOWN explicite ;
- données négatives ;
- éventuellement distance dans l'espace des embeddings si pertinent.

Le système doit être capable d'afficher :

UNKNOWN
CONF: 34%

Le rejet des gestes inconnus est une partie importante du projet.

---

# 6. MULTI-MODE

L'une des caractéristiques principales de GestureOS AI sera son architecture multimode.

Un même geste peut produire une action différente selon le mode actif.

Implémenter une architecture propre avec au minimum les modes suivants.

## MODE 1 — ROBOT

Exemples :

LEFT -> servo gauche
RIGHT -> servo droite
UP -> servo position haute
DOWN -> servo position basse
CIRCLE -> animation
X -> STOP

Le SG90 et éventuellement le stepper servent ici à rendre la démo visuelle.

---

## MODE 2 — SMART CONTROL

Simulation d'un environnement automatisé.

Exemples :

UP -> LED ON
DOWN -> LED OFF
CIRCLE -> relais ON
CIRCLE_CCW -> relais OFF
Z -> alarme
X -> arrêt général

---

## MODE 3 — PRESENTATION

Prévoir une architecture permettant éventuellement d'utiliser l'ESP32 comme contrôleur de présentation via Bluetooth si techniquement possible et stable.

Exemples :

RIGHT -> slide suivante
LEFT -> slide précédente
UP -> première slide
DOWN -> dernière slide
PUSH -> action / valider
X -> quitter

Ne suppose pas que Bluetooth HID fonctionne avant de l'avoir vérifié.

---

## MODE 4 — GAME

Créer un mini-jeu gestuel.

Le LCD affiche par exemple :

DO: CIRCLE
TIME: 3.0s

L'utilisateur effectue le mouvement.

Puis :

CIRCLE 96%
+100 PTS

Ajouter si raisonnable :

- score ;
- combo ;
- vies ;
- difficulté ;
- temps de réponse ;
- gestes aléatoires.

---

## MODE 5 — MACRO

Permettre des séquences de gestes.

Exemple :

LEFT -> RIGHT -> CIRCLE

peut déclencher :

MACRO_01

Une macro peut ensuite :

- bouger le servo ;
- faire sonner le buzzer ;
- changer la LED ;
- modifier un état ;
- changer de mode.

Créer une machine à états robuste pour reconnaître les séquences.

---

## MODE 6 — CUSTOM

Architecture préparée pour associer :

geste -> action

ou :

séquence de gestes -> action

sans devoir modifier profondément le code principal.

---

# 7. INTERFACE LCD 1602

Toute l'interface doit être adaptée au LCD 16×2.

Créer un système d'affichage propre.

Exemples :

GESTURE AI
MODE: ROBOT

Pendant reconnaissance :

ANALYZING...
PLEASE MOVE

Résultat :

RIGHT     94%
SERVO -> 120

Unknown :

UNKNOWN   38%
TRY AGAIN

Menu :

> RUN
  DATASET

Le LCD doit être utilisé intelligemment.

Créer une couche d'abstraction pour éviter les appels LCD dispersés dans tout le code.

---

# 8. MENU

Créer un menu contrôlable idéalement avec :

- joystick ;
ou
- clavier 4×4 ;
ou
- boutons.

Menu minimum :

1. RUN
2. DATASET
3. TEST
4. MODES
5. SETTINGS
6. CALIBRATE
7. STATS
8. ABOUT

Le joystick peut être utilisé :

UP/DOWN -> navigation
PRESS -> sélectionner
LEFT -> retour
RIGHT -> éventuellement action secondaire

---

# 9. MODE DATASET INTÉGRÉ

Je veux pouvoir utiliser directement l'ESP32 pour collecter mon dataset.

Workflow souhaité :

Sélectionner le geste :

DATASET
GEST: LEFT

Appuyer sur START.

LCD :

READY
3...

2...

1...

GO!

Puis acquisition des valeurs :

timestamp
ax
ay
az
gx
gy
gz

Une séquence doit être enregistrée correctement.

Ensuite :

LEFT
SAMPLE 023 OK

Les données doivent être envoyées vers le PC via Serial et éventuellement enregistrées automatiquement par un script Python.

Créer donc :

- firmware ESP32 d'acquisition ;
- protocole Serial propre ;
- script Python de capture ;
- organisation automatique des fichiers.

---

# 10. DATASET

Je ne veux pas devoir enregistrer 10 000 gestes manuellement.

Créer une stratégie hybride :

## Données réelles

Objectif initial :

20 gestes
× 30 à 50 vrais exemples
= environ 600 à 1000 séquences minimum.

Ensuite augmenter si nécessaire.

Si possible, prévoir plusieurs utilisateurs.

Exemple :

4 utilisateurs
× 20 gestes
× 30 exemples
= 2400 vraies séquences.

Mais construire progressivement.

---

# 11. DATASETS INTERNET

Chercher des datasets publics utilisant :

- MPU6050 ;
- accéléromètre + gyroscope ;
- gestes de main ;
- 6-axis IMU ;
- ESP32 si possible.

Ne télécharge rien de douteux.

Documenter chaque dataset utilisé :

- source ;
- licence ;
- classes ;
- fréquence d'échantillonnage ;
- capteurs ;
- nombre d'échantillons ;
- différences avec notre hardware.

Ne mélange jamais aveuglément un dataset externe avec notre dataset.

Analyser :

- compatibilité axes ;
- fréquence ;
- unités ;
- orientation capteur ;
- longueur des fenêtres ;
- labels.

---

# 12. AUGMENTATION DE DONNÉES

Créer un pipeline Python d'augmentation adapté aux séries temporelles IMU.

Étudier et implémenter seulement les transformations pertinentes :

- jitter / bruit gaussien faible ;
- scaling ;
- temporal scaling ;
- time warping léger ;
- time shift ;
- magnitude warping ;
- petites rotations 3D ;
- permutation seulement si physiquement cohérente ;
- cropping / padding intelligent.

Ne pas détruire la signification physique des gestes.

Comparer entraînement :

A. données réelles uniquement

B. données réelles + augmentation

Mesurer si l'augmentation améliore réellement la généralisation.

---

# 13. SPLIT DATASET CORRECT

Éviter toute fuite de données.

IMPORTANT :

Une version augmentée d'un sample ne doit jamais se retrouver dans le test si l'original est dans le train.

Créer :

TRAIN
VALIDATION
TEST

Le TEST FINAL doit contenir uniquement des gestes réels jamais utilisés pour l'entraînement.

Pour plusieurs utilisateurs, prévoir éventuellement :

- random split ;
- subject-independent split ;
- leave-one-user-out.

---

# 14. ACQUISITION MPU6050

Créer un module robuste :

- initialisation ;
- calibration ;
- lecture accélération ;
- lecture gyroscope ;
- timestamp ;
- fréquence stable ;
- détection d'erreurs I2C.

Tester plusieurs fréquences :

- 50 Hz ;
- 100 Hz.

Commencer probablement à 100 Hz.

Étudier la meilleure fréquence en fonction :

- gestes ;
- précision ;
- mémoire ;
- latence.

---

# 15. SEGMENTATION AUTOMATIQUE DES GESTES

Je ne veux pas que la version finale dépende obligatoirement d'un bouton START pour chaque geste.

Développer progressivement :

Version 1 :
capture pendant fenêtre fixe.

Version 2 :
détection automatique.

Exemple :

repos
↓
énergie mouvement > seuil
↓
GESTURE START
↓
capture
↓
mouvement revient au repos
↓
GESTURE END
↓
classification

Étudier :

- magnitude accélération ;
- magnitude gyroscope ;
- énergie ;
- moving average ;
- hysteresis ;
- temps minimum ;
- temps maximum.

---

# 16. PRÉTRAITEMENT

Créer un pipeline reproductible.

Étudier :

- suppression offset ;
- calibration ;
- normalisation ;
- standardisation ;
- filtrage passe-bas si nécessaire ;
- resampling ;
- padding ;
- interpolation ;
- fenêtre temporelle fixe ;
- magnitude acc ;
- magnitude gyro.

Ne pas appliquer des traitements inutiles sans justification.

---

# 17. FEATURES MANUELLES

Construire une baseline à partir de caractéristiques.

Par axe :

- mean
- std
- variance
- min
- max
- range
- RMS
- energy
- median
- IQR
- skewness
- kurtosis
- zero crossing si pertinent

Caractéristiques supplémentaires :

- magnitude acc
- magnitude gyro
- corrélations entre axes
- durée geste
- jerk
- vitesse angulaire moyenne
- énergie spectrale
- fréquence dominante si pertinente
- FFT seulement si elle apporte une valeur réelle.

---

# 18. MODÈLES À COMPARER

Je veux une vraie démarche IA.

Comparer plusieurs approches.

Baseline :

- KNN
- Logistic Regression si pertinente
- SVM
- Random Forest
- XGBoost uniquement si pertinent pour comparaison PC

Réseaux :

- MLP
- 1D CNN

Optionnel :

- CNN + LSTM
- GRU

Mais attention :

Le modèle final doit être compatible avec les ressources de l'ESP32.

Ne cherche pas le modèle le plus complexe.

Cherche le meilleur compromis :

PRECISION
+
LATENCE
+
TAILLE
+
RAM
+
ROBUSTESSE

---

# 19. MÉTRIQUES

Pour chaque modèle calculer :

- accuracy ;
- precision ;
- recall ;
- F1-score ;
- macro F1 ;
- confusion matrix ;
- temps d'inférence sur PC ;
- taille du modèle.

Pour le modèle embarqué :

- temps d'inférence ESP32 ;
- RAM consommée ;
- Flash consommée ;
- FPS / gestes par seconde si pertinent.

Créer des graphiques propres :

- loss ;
- accuracy ;
- matrice de confusion ;
- comparaison modèles ;
- per-class F1 ;
- erreurs par geste.

---

# 20. TINYML

Une fois le modèle sélectionné :

- convertir vers TensorFlow Lite si applicable ;
- tester quantification int8 ;
- comparer float32 vs int8 ;
- mesurer perte de précision ;
- générer le modèle embarqué ;
- intégrer à l'ESP32.

Le modèle final doit fonctionner localement sur l'ESP32 si possible.

Pas de dépendance Cloud pour l'inférence finale.

---

# 21. CALIBRATION

Au démarrage :

CALIBRATE
KEEP STILL

Calculer les offsets nécessaires.

Afficher :

CALIBRATION
DONE

Sauvegarder éventuellement la calibration en mémoire persistante si pertinent.

---

# 22. ARCHITECTURE LOGICIELLE ESP32

Ne crée surtout pas un énorme fichier `.ino`.

Créer une architecture modulaire.

Exemple possible :

firmware/
  src/
    main.cpp
    imu.cpp
    imu.h
    gesture_engine.cpp
    gesture_engine.h
    model.cpp
    model.h
    lcd_ui.cpp
    lcd_ui.h
    menu.cpp
    menu.h
    modes.cpp
    modes.h
    servo_controller.cpp
    servo_controller.h
    macro_engine.cpp
    macro_engine.h
    config.cpp
    config.h

Mais adapte cette architecture si PlatformIO / ESP-IDF donne quelque chose de meilleur.

---

# 23. ARCHITECTURE PYTHON

Créer également une partie PC propre :

gestureos/
  data/
    raw/
    processed/
    augmented/
    external/

  scripts/
    capture_serial.py
    preprocess.py
    augment.py
    train.py
    evaluate.py
    export_tflite.py
    test_realtime.py

  models/
    sklearn/
    keras/
    tflite/

  notebooks/

  reports/

  tests/

  configs/

Utiliser un fichier de configuration centralisé.

---

# 24. REPRODUCTIBILITÉ

Créer :

requirements.txt
ou
pyproject.toml

et documenter les versions utilisées.

Utiliser des seeds reproductibles.

Sauvegarder :

- configuration ;
- hyperparamètres ;
- résultats ;
- modèle ;
- labels ;
- scaler ;
- preprocessing.

---

# 25. LOGGING EXPÉRIMENTAL

Créer un système simple permettant de conserver :

experiment_id
model
features
window_size
sample_rate
augmentation
accuracy
macro_f1
model_size
inference_time

Exemple :

experiments.csv

Cela me permettra de montrer au jury que j'ai réellement comparé plusieurs modèles.

---

# 26. DÉMO FINALE

Je veux pouvoir présenter quelque chose comme :

Je prends le contrôleur.

Je fais RIGHT.

LCD :

RIGHT     97%
MODE: ROBOT

Le servo bouge à droite.

Je fais CIRCLE.

Une séquence physique est déclenchée.

Je change en mode GAME.

LCD :

DO: Z
TIME: 3.0

Je fais Z.

LCD :

Z         95%
+100 PTS

Je fais ensuite un mouvement absurde.

LCD :

UNKNOWN   31%
REJECTED

Puis j'active MACRO.

LEFT -> RIGHT -> CIRCLE

Le système reconnaît :

MACRO 01
EXECUTING

Servo + LED + buzzer réagissent.

---

# 27. OBJECTIFS QUALITATIFS

Le projet final doit démontrer clairement :

- intelligence artificielle ;
- traitement de séries temporelles ;
- robotique ;
- TinyML ;
- embarqué ;
- temps réel ;
- acquisition physique ;
- interaction homme-machine ;
- optimisation ;
- méthodologie expérimentale.

---

# 28. OBJECTIFS QUANTITATIFS INITIAUX

Cible initiale :

15 gestes minimum.

Cible souhaitée :

20 gestes.

Stretch goal :

25 gestes.

Précision souhaitée :

>= 90 % sur données de test réelles.

Objectif idéal :

>= 93–95 %.

Attention :

Ne triche jamais sur les métriques pour atteindre ces valeurs.

Si les résultats sont plus faibles, analyse les causes.

---

# 29. CONTRAINTES

Respecte impérativement ceci :

1. Pas de moteur DC obligatoire.
2. Pas d'OLED.
3. LCD 1602.
4. ESP32 comme microcontrôleur principal.
5. MPU6050 comme capteur gestuel principal.
6. Utiliser uniquement le matériel réellement disponible.
7. Pas de Cloud nécessaire au fonctionnement final.
8. Pas de données inventées.
9. Pas de résultats ML inventés.
10. Pas de métriques fictives.
11. Pas de bibliothèque supposée installée sans vérification.
12. Pas de commande terminal inventée.
13. Ne détruis pas des fichiers existants sans inspection.
14. Toujours tester après modifications importantes.

---

# 30. ENVIRONNEMENT DE DÉVELOPPEMENT

Tu travailles avec moi depuis un terminal Linux.

J'utilise Antigravity comme environnement/IDE.

Commence par inspecter l'environnement réel.

Si Antigravity fournit une CLI réellement installée :

- détecte-la ;
- consulte son aide ;
- utilise-la lorsque cela apporte quelque chose.

NE SUPPOSE PAS qu'une commande Antigravity existe.

Teste d'abord avec des commandes sûres comme :

which
command -v
--help

Si Antigravity n'expose aucune CLI pertinente, continue normalement avec le terminal Linux.

Tu peux utiliser les outils disponibles dans l'environnement :

- shell ;
- Python ;
- git ;
- PlatformIO ;
- Arduino CLI ;
- ESP-IDF ;

mais UNIQUEMENT s'ils sont réellement installés.

Inspecte avant de choisir.

---

# 31. TA MÉTHODE DE TRAVAIL

IMPORTANT :

Tu ne dois pas essayer de construire tout le projet d'un coup.

Travaille par PHASES.

À chaque phase :

1. inspecte l'état réel ;
2. explique brièvement l'objectif ;
3. implémente ;
4. teste ;
5. corrige ;
6. documente ;
7. seulement ensuite passe à la phase suivante.

---

# 32. PHASES DU PROJET

## PHASE 0 — Audit

Inspecte :

- OS ;
- Python ;
- pip ;
- git ;
- PlatformIO ;
- Arduino CLI ;
- ESP-IDF ;
- ports série ;
- structure du dossier ;
- packages disponibles.

Ne modifie presque rien ici.

Produis un diagnostic.

---

## PHASE 1 — Structure du projet

Créer proprement l'arborescence.

Initialiser Git si nécessaire.

Créer README initial.

Créer environnement Python.

---

## PHASE 2 — Test MPU6050

Faire fonctionner uniquement :

ESP32 + MPU6050.

Afficher les données sur Serial.

Mesurer stabilité et sample rate.

---

## PHASE 3 — LCD

Faire fonctionner le LCD 1602.

Créer la couche UI.

---

## PHASE 4 — Data Logger

Créer acquisition de données.

Créer script Python Serial.

Sauvegarder CSV.

---

## PHASE 5 — Dataset pilote

Commencer avec seulement :

LEFT
RIGHT
UP
DOWN
CIRCLE
SHAKE

Enregistrer suffisamment d'exemples.

Valider tout le pipeline avant d'ajouter 20 gestes.

---

## PHASE 6 — Baselines ML

Tester :

Random Forest
SVM
MLP

Analyser les résultats.

---

## PHASE 7 — Deep Learning

Tester petit 1D CNN.

Comparer.

---

## PHASE 8 — Expansion dataset

Ajouter progressivement les autres gestes.

Ne jamais ajouter plusieurs gestes problématiques sans analyser la confusion.

---

## PHASE 9 — UNKNOWN

Implémenter le rejet.

Créer données négatives.

Tester des mouvements inconnus.

---

## PHASE 10 — TinyML ESP32

Exporter et intégrer le modèle.

Mesurer :

RAM
Flash
latence
accuracy.

---

## PHASE 11 — Segmentation automatique

Détection début/fin geste.

---

## PHASE 12 — Multi-mode

Ajouter :

ROBOT
SMART
PRESENTATION
GAME
MACRO
CUSTOM

---

## PHASE 13 — Actionneurs

Servo.

LED/RGB.

Buzzer.

Relais si pertinent.

Stepper seulement si alimentation et stabilité suffisantes.

---

## PHASE 14 — Menu

Ajouter menu complet LCD + joystick/clavier.

---

## PHASE 15 — Macros

Gestes séquentiels.

Timeouts.

Machine d'états.

---

## PHASE 16 — Optimisation

Optimiser :

- mémoire ;
- latence ;
- stabilité ;
- rejet ;
- UX.

---

## PHASE 17 — Tests finaux

Construire une vraie suite de tests.

Tester :

- gestes connus ;
- inconnus ;
- utilisateurs différents ;
- mouvements rapides ;
- mouvements lents ;
- orientations légèrement différentes ;
- fonctionnement long ;
- erreurs capteur.

---

## PHASE 18 — Soutenance

Produire :

- README final ;
- architecture ;
- diagrammes ;
- résultats ;
- tableau comparatif ;
- matrice de confusion ;
- explication TinyML ;
- limites ;
- perspectives ;
- scénario de démonstration.

---

# 33. QUALITÉ DU CODE

Je veux :

- code lisible ;
- fonctions courtes ;
- noms explicites ;
- commentaires uniquement lorsqu'ils apportent de la valeur ;
- aucune duplication inutile ;
- gestion d'erreurs ;
- configuration centralisée ;
- logs propres ;
- séparation hardware / logique / IA / UI.

---

# 34. DOCUMENTATION

Maintenir un README vivant.

Il doit expliquer :

- objectif ;
- architecture ;
- matériel ;
- câblage ;
- installation ;
- collecte dataset ;
- entraînement ;
- déploiement ;
- utilisation ;
- modes ;
- résultats ;
- limitations.

Créer aussi :

docs/architecture.md
docs/hardware.md
docs/dataset.md
docs/ml_pipeline.md
docs/demo.md

si cela devient utile.

---

# 35. SCHÉMAS

Quand le hardware commence :

me fournir une table de câblage exacte :

COMPOSANT | PIN | ESP32 PIN | ALIMENTATION | NOTES

Vérifier les niveaux logiques avant tout branchement.

Fais particulièrement attention au HC-SR04 qui peut avoir une sortie Echo 5 V alors que l'ESP32 utilise du 3.3 V.

Ne propose aucun câblage dangereux.

---

# 36. PHILOSOPHIE DU PROJET

Je ne cherche pas à impressionner uniquement avec beaucoup de composants.

La priorité est :

1. qualité de l'IA ;
2. fiabilité ;
3. interaction en temps réel ;
4. démonstration visible ;
5. architecture propre ;
6. capacité à expliquer chaque choix.

Chaque fonctionnalité doit avoir une raison d'exister.

---

# 37. IMPORTANT : NE PAS SUR-ENGINEER TROP TÔT

Le projet final peut être ambitieux.

Mais commence avec un MVP fonctionnel.

Un pipeline :

MPU6050
→ CSV
→ entraînement
→ classification
→ ESP32
→ servo

doit être totalement fonctionnel avant les fonctions avancées.

---

# 38. CE QUE JE VEUX DE TOI MAINTENANT

Commence immédiatement par la PHASE 0.

Inspecte mon environnement de travail et le dossier courant.

NE CRÉE PAS ENCORE toute l'application.

Je veux d'abord que tu :

1. identifies les outils réellement installés ;
2. identifies l'état du dossier actuel ;
3. proposes l'architecture finale du dépôt ;
4. identifies les risques techniques principaux ;
5. proposes le premier milestone concret ;
6. vérifies si Antigravity possède une CLI utilisable ;
7. définisses comment nous allons tester le MPU6050 ;
8. crées ensuite uniquement la structure minimale nécessaire au premier test si l'environnement est prêt.

À chaque étape, utilise réellement le terminal pour vérifier les hypothèses.

Ne me donne pas uniquement des instructions théoriques.

AGIS sur le projet lorsque tu as suffisamment d'informations.

Si une erreur apparaît :

lis l'erreur,
comprends-la,
corrige-la,
reteste.

Ne contourne pas silencieusement les problèmes.

L'objectif est qu'à la fin nous ayons un projet réellement fonctionnel, propre et défendable devant un jury.