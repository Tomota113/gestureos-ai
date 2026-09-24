CHECKPOINT ID:
2026-09-24_resume_startup-frame-check

PHASE:
M0 terminé ; M1 acquisition réelle préparé, non validé.

OBJECTIVE:
Reprendre l'état persistant et fiabiliser le contrôle de capture avant le test physique.

COMPLETED:
- Quatre fichiers de reprise, sources et guide relus, Git propre au départ (a02bf6b).
- Versions inchangées ; CP2102 toujours sur /dev/ttyUSB0, aucun log physique existant.
- Défaut reproduit : une capture démarrant en séquence 1 pouvait être acceptée.
- Correction : séquence zéro exigée ; first_sequence inclus dans le rapport.
- Documentation actualisée. Question marquage et câblage MPU6050 envoyée.

TESTED:
Fixture artificielle omettant la première mesure ; test de régression ajouté.
.venv/bin/python -m unittest discover -s tests -v : 7 tests OK.
git diff --check : OK avant mise à jour documentaire.
Firmware C++ inchangé ; pas de recompile ou flashage inutile.

TEST RESULTS:
Le flux artificiel incomplet passe de passed=True (défaut) à passed=False (attendu).
Détails : reports/resume-stream-check-20260924.txt.
Aucune donnée MPU6050 réelle, précision ML ou validation électrique inventée.

FAILED / UNRESOLVED:
Antigravity a rendu le code 0 mais le seul texte indique :
[agy] print timeout after 1m0s with turn in progress; returning partial output
Revue INCOMPLETE_TIMEOUT ; aucune conclusion, aucun retry, aucun quota supposé épuisé.
Référence/module et branchements actuels toujours inconnus.

FILES CHANGED:
scripts/check_stream.py, tests/test_stream.py, README.md,
outputs/first-mpu6050-test.md, outputs/phase-0-audit.md,
reports/resume-stream-check-20260924.txt, .agent/*.

COMMANDS THAT WORKED:
.venv/bin/python --version ; import serial et énumération list_ports
pio --version ; agy --help
git status --short ; git log --oneline -n 5
.venv/bin/python -m unittest discover -s tests -v

COMMANDS THAT FAILED:
Revue agy --mode plan --print-timeout 60s : incomplète par délai, malgré code retour 0.

CURRENT GIT STATUS:
Base de reprise a02bf6b, propre avant travail. Modifications de cette reprise
regroupées dans le commit « fix: reject captures missing startup frames ».
Toujours vérifier git status et log à la reprise, ne pas déduire le statut des seuls textes.

NEXT EXACT STEP:
Obtenir marquage et câblage du MPU6050 ; appliquer .agent/NEXT_ACTION.md avant upload.
Si aucun matériel prêt, expliquer ce prérequis sans anticiper LCD/ML/actionneurs.

SAFE TO RESUME:
YES

REASON:
Correction testée, capture brute protégée, firmware matériel inchangé,
état et prochaine action sauvegardés. Les mesures physiques restent explicitement non réalisées.

USER STEERING — priorité sur le précédent prérequis de câblage :
L’utilisateur fera les branchements plus tard, lors des tests ou de l’ajout des données.
Poursuivre les jalons logiciels sans attendre cette information. Aucun flashage.
NEXT SOFTWARE MILESTONE: protocole de capture bornée + logger PC avec provenance,
protection contre l’écrasement et tests sans capteur. Ne pas prétendre M1 physique validé.
