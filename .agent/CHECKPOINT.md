CHECKPOINT ID:
2026-09-24_m2-software_capture-logger

PHASE:
Collecte logicielle prête ; validations physiques reportées par demande utilisateur.

OBJECTIVE:
Préparer les futures acquisitions sans attendre les branchements et sans inventer de données.

COMPLETED:
Package Python installé, protocole versionné borné avec CRC, firmware dataset,
logger conservant provenance/log brut/CSV validé/résultat, guides et tests.

TESTED:
- pio run -d firmware -e esp32dev -e dataset : 2 builds SUCCESS.
- .venv/bin/python -m unittest discover -s tests -v : 20 tests OK.
- g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/capture_protocol_test.cpp firmware/src/capture_protocol.cpp -o work/capture_protocol_test
- ./work/capture_protocol_test : parsing de commande et CRC OK.
- Installation pip éditable, aide CLI, pip check réussis.

TEST RESULTS:
Preuves conservées dans reports/logger-validation-20260924/.
Banc : RAM statique21808 / Flash application287585 octets.
Dataset : RAM statique22016 / Flash application315941 octets.
Aucun capteur, flashage, calibration, dataset réel ou modèle ML testé.

FAILED / UNRESOLVED:
- setuptools absent du venv au contrôle initial ; backend80.9.0 installé par pip en build isolé, installation réussie.
- Revue Antigravity à la reprise : timeout60s sans réponse exploitable, pas de retry.
- Matériel et données réels volontairement différés, pas un blocage logiciel.

FILES CHANGED:
pyproject.toml, requirements.txt, .gitignore, configs/collection.json, src/gestureos/*,
scripts/capture_serial.py, firmware/platformio.ini, firmware/src/capture_protocol.*,
firmware/src/dataset_main.cpp, tests/test_capture.py, tests/native/*,
README.md, docs/architecture.md, docs/dataset-protocol.md,
outputs/dataset-collection-guide.md, reports/logger-validation-20260924/*, .agent/*.

COMMANDS THAT WORKED:
Voir TESTED et les logs persistants.

COMMANDS THAT FAILED:
pip show setuptools : package absent (pas une panne de quota).
Revue agy : délai atteint (code0 ne constitue pas un succès de revue).

CURRENT GIT STATUS:
Base3d8dc7c. Ce jalon sera sauvegardé dans « feat: add bounded gesture capture protocol and PC logger ».
Vérifier le statut réel à la reprise ; ne pas se fier à une ancienne observation.

NEXT EXACT STEP:
Chargement contrôlé des captures et splits par groupe, selon NEXT_ACTION.md.
Aucune nouvelle demande de branchement pour cette étape logicielle.

SAFE TO RESUME:
YES

REASON:
Code et tests enregistrés, logs préservés, aucun firmware physique remplacé,
aucune donnée réelle écrasée, prochaine action définie et validations différées explicites.
