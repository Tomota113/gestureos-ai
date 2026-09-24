CURRENT PHASE:
Phase 0 terminée ; M1 matériel préparé mais non validé.

RESUME STATUS:
Reprise effectuée depuis a02bf6b ; correction de détection des premières trames perdue testée.
Sept tests logiciels passent ; firmware inchangé. Revue Antigravity interrompue au délai
sans résultat : ne pas relancer automatiquement. Question matériel envoyée, encore sans réponse.

NEXT OBJECTIVE:
Identifier le module MPU6050 et obtenir une capture physique exploitable à 100 Hz.

NEXT ACTION:
1. Dans /home/ibrahim-tomota/Documents/Codex/2026-09-24/tu, lire les quatre fichiers .agent.
2. Exécuter git status puis git log --oneline -n 5.
3. Lire outputs/first-mpu6050-test.md, firmware/include/config.h, firmware/src/imu.cpp,
   firmware/src/main.cpp et scripts/check_stream.py. Vérifier si reports/hardware existe déjà.
4. L'utilisateur a demandé de câbler plus tard. Obtenir le marquage/schéma du module MPU6050
   et confirmer que VCC et les pull-ups I2C conviennent au plan 3,3 V. Ne pas supposer un GY-521.
5. Vérifier le câblage hors tension : GND commun, SDA GPIO21, SCL GPIO22, AD0 GND,
   alimentation validée ; aucun actionneur/LCD pour ce premier essai.
6. Recontrôler le port réel : .venv/bin/python -m serial.tools.list_ports -v
7. Inspecter/sauvegarder le programme actuellement présent avant de le remplacer si nécessaire.
   Commande d'upload disponible mais PAS encore exécutée :
   pio run -d firmware -t upload --upload-port /dev/ttyUSB0
8. Seulement après ces vérifications et upload, choisir deux noms de sortie inexistants :
   .venv/bin/python scripts/check_stream.py --port /dev/ttyUSB0 --seconds 60 --rate 100 --output reports/hardware/bench-001.serial --report reports/hardware/bench-001.json
   Cette commande réinitialise la carte. Fermer tout autre moniteur série.

EXPECTED RESULT:
Rapport passed=true pour durée capteur >=60 s, 98-102 Hz, 95 % des dt dans 8-12 ms,
aucun dt >20 ms, aucune perte série observée/erreur I2C/saturation.
Puis repos 10 s et orientations des axes cohérentes : ces contrôles physiques restent indispensables.

IF SUCCESS:
Conserver log + JSON ; noter tension, repère, firmware, biais et conditions réels.
Mettre à jour checkpoint et commit. Aborder ensuite calibration, LCD et logger labellisé
selon les phases ; ne pas sauter directement au ML sans dataset réel.

IF FAILURE:
Conserver la sortie brute ; diagnostiquer port, tension, pull-ups, identité, bus et timing.
Ne jamais considérer cela automatiquement comme un quota ; ne pas falsifier la cadence.
Si le câblage manque encore, conserver l'état prêt et expliquer le prérequis matériel précis.

FILES INVOLVED:
outputs/first-mpu6050-test.md ; firmware/* ; scripts/check_stream.py ; reports/hardware/* ; .agent/*.

USER STEERING — priorité sur le précédent prérequis de câblage :
L’utilisateur fera les branchements plus tard, lors des tests ou de l’ajout des données.
Poursuivre les jalons logiciels sans attendre cette information. Aucun flashage.
NEXT SOFTWARE MILESTONE: protocole de capture bornée + logger PC avec provenance,
protection contre l’écrasement et tests sans capteur. Ne pas prétendre M1 physique validé.
