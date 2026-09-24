CURRENT PHASE:
Kit de collecte hors ligne terminé côté logiciel. 69 tests OK. M6 inférence commencé mais non terminé.

PRIORITÉ UTILISATEUR:
Il part sans Wi-Fi avec cet ordinateur + ESP32 + MPU6050. Le guide outputs/COLLECTE_SANS_WIFI.md contient toutes les commandes locales, premier banc, installation et collecte. Aucun port USB détecté pendant cette session, aucun flashage/test MPU réel.

NEXT ACTION:
1. Lire .agent/* et git status/log ; vérifier quota officiel (dernier contrôle92 % utilisés sur5h). Ne pas acheter de crédits ni consommer de reset.
2. Si l’utilisateur revient avec données : préserver data/raw, data/pending, data/session_notes et reports/hardware ; revérifier et sauvegarder sans écrasement. Seules les prises confirmées sont publiées dans raw. Ne jamais employer pending comme dataset automatiquement.
3. Sinon reprendre M6 : src/gestureos/inference.py, rejection.py, predict.py, configs/rejection.json sont sauvegardés, syntaxe contrôlée mais pas testés fonctionnellement. M6 NE DOIT PAS être présenté comme terminé.
4. Écrire les tests d’inférence sans fit, parité du scaler, bundles/versions/corruption, indices de classes et scores RF/MLP/SVM binaires/multiclasses, ties/conflits predict, UNKNOWN, refus du test final. Revoir la robustesse du contrat avant usage.
5. Documenter M6 après validation. Seuils expérimentaux non calibrés ; politique par défaut rejette tout et aucune action matérielle.
6. Choix de seuils sur validation, test final et entraînements réels restent à venir. Aucun apprentissage sur fixtures.

OFFLINE:
Lanceur bash outputs/LANCER_COLLECTE.sh ; --check ne touche pas au matériel.
INSTALLER_ESP32.sh bench|dataset --port PORT utilise esptool déjà installé, pas le réseau, sauvegarde Flash4Mo avant écriture. Confirmation INSTALLER demandée par le script lorsqu’il est lancé par l’utilisateur.
Images outputs/firmware-offline issues des builds M2 existants, SHA256 vérifiés. Ne pas reflasher automatiquement.
69 tests logiciel réussis, ne pas relancer sans motif. Aucun appel Antigravity après son précédent timeout.
