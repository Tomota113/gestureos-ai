CHECKPOINT ID:
2026-09-24_m3-software_validated-dataset-splits

PHASE:
M3-SOFTWARE terminé ; matériel différé.

OBJECTIVE:
Valider les captures originales et construire des partitions reproductibles sans fuite entre groupes.

COMPLETED:
Chargement strict, revalidation SHA256/CRC/protocole/CSV, refus des captures synthétiques ou partielles,
détection de doublons renommés, splits par session/sujet, manifeste et diagnostic bloquant,
guide utilisateur et 10 nouveaux tests (30 au total).

TESTED:
.venv/bin/python -m unittest discover -s tests -v : 30 tests OK, code 0.
.venv/bin/python -m gestureos.prepare --help : OK.
git diff --check : OK avant sauvegarde finale.
Preuves : reports/m3-dataset-tests-20260924.txt.

TEST RESULTS:
Fixtures artificielles uniquement sous work/. Certaines imitent explicitement les métadonnées hardware
pour tester le validateur ; elles ne sont pas des captures physiques et ne deviennent pas un dataset réel.
Aucune modification RAW réelle ; aucun firmware modifié/flashé ; aucun entraînement.

FAILED / UNRESOLVED:
Pas d'échec de test. Aucun dataset réel présent.
La recherche de split est bornée (512 essais), proportions approximatives à groupes indivisibles.
Provenance déclarée vérifiée, pas authentifiée cryptographiquement.

FILES CHANGED:
src/gestureos/dataset.py, split.py, prepare.py ; tests/test_dataset.py ; README.md ;
outputs/dataset-preparation-guide.md ; reports/m3-dataset-tests-20260924.txt ; .agent/*.

CURRENT GIT STATUS:
Base add2f1c propre avant travaux. Lot à sauvegarder dans « feat: validate raw captures and create grouped dataset splits ».
Vérifier git status/log à la reprise.

QUOTA:
5 h : 83 % utilisés au départ, 95 % avant clôture ; 12 points consommés à cet instant.
Semaine : 49 % utilisés. Aucun reset/crédit. Pas de nouvelle fonctionnalité démarrée après ce jalon.

NEXT EXACT STEP:
Prétraitement/manifestes selon NEXT_ACTION.md, lors de la prochaine reprise et après contrôle du quota.

SAFE TO RESUME:
YES

REASON:
Jalon testé, code/documentation/preuves persistants, prochaine action précise, RAW préservés.

QUOTA STOP — dernier contrôle officiel après commit ff0c11e :
Fenêtre5h utilisée à100 % ; resetsAt fourni par le client : 1790226268 (Unix UTC).
M3 entièrement sauvegardé, 30 tests OK, aucun crédit/reset consommé.
Ne démarrer aucune fonctionnalité. À la prochaine reprise, relire le quota réel puis NEXT_ACTION.
Consommation observée depuis le départ83 % :17 points, dans le plafond de20 demandé.
