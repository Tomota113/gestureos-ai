# Reprise GestureOS AI

Le [kit de collecte sans Wi-Fi](COLLECTE_SANS_WIFI.md) est prêt côté logiciel
pour cet ordinateur avec ESP32 et MPU6050. **69 tests logiciels réussis.**
Le capteur et les branchements restent à tester ; aucun flashage réalisé.

Lanceur : `bash outputs/LANCER_COLLECTE.sh`, depuis le dossier du projet.
Les mesures sont saisies automatiquement par USB ; tu choisis/confirme le geste.
Les prises confirmées vont dans data/raw, les originaux/tentatives dans data/pending.

M5 baselines terminé ; M6 inférence/rejet sauvegardé en cours mais pas terminé.
Aucun modèle de gestes entraîné et aucune précision ML mesurée.
Dernier quota observé :92 % utilisés sur5h. Aucun crédit/reset consommé.
