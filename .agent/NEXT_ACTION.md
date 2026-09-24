CURRENT PHASE:
M3-SOFTWARE terminé. Matériel et données réelles différés par demande utilisateur.

NEXT OBJECTIVE:
Prétraitement et caractéristiques reproductibles, sans entraîner sur de fausses données.

NEXT ACTION:
1. Lire les quatre fichiers .agent ; git status ; git log --oneline -n 5.
2. Vérifier le quota réel avant une opération longue : il restait 5 % sur 5 h avant clôture M3.
3. Lire dataset.py, split.py, prepare.py, tests/test_dataset.py et le guide outputs/dataset-preparation-guide.md.
4. Implémenter la lecture d'un manifeste ready en revérifiant les empreintes avant emploi.
5. Ajouter resampling/fenêtre et features nécessaires aux baselines. Scaler ajusté exclusivement sur train ; aucune augmentation du test.
6. Tester formes, cohérence temporelle et non-fuite avec fixtures clairement artificielles sous work/.
7. Vérifier disponibilité/compatibilité des dépendances ML avant installation ; ne produire aucune métrique de reconnaissance sans vrais exemples.
8. Documenter, sauvegarder les résultats de tests et créer le checkpoint du prochain jalon.

EXPECTED RESULT:
Pipeline logiciel prêt à recevoir les vraies données. Pas de précision fictive.

DO NOT REPEAT:
Pas de réinstallation, recompile ESP32 ou demande de câblage sans nécessité.
Ne pas relancer Antigravity automatiquement après son ancien timeout.

DEFERRED:
Câblage, validation MPU6050, collecte réelle et entraînement/évaluation réels.

QUOTA STOP — dernier contrôle officiel après commit ff0c11e :
Fenêtre5h utilisée à100 % ; resetsAt fourni par le client : 1790226268 (Unix UTC).
M3 entièrement sauvegardé, 30 tests OK, aucun crédit/reset consommé.
Ne démarrer aucune fonctionnalité. À la prochaine reprise, relire le quota réel puis NEXT_ACTION.
Consommation observée depuis le départ83 % :17 points, dans le plafond de20 demandé.
