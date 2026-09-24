# Antigravity — diagnostic CLI et revue M9

Date : 2026-09-24. La connexion `agy` fonctionne. Le premier appel en mode
`--print` a été bloqué parce qu'Antigravity demandait `run_command` avec
`pwd && ls -la src/gestureos`. Cette commande composée ne faisait pas partie
des permissions déjà autorisées. Le mode sans interface refuse la demande
plutôt que d'afficher une invite. Ce n'était ni une erreur réseau ni une preuve
de quota épuisé.

Solution vérifiée : déléguer en `--mode plan --effort low` et demander
explicitement **seulement `view_file`** pour les fichiers nécessaires, sans
`run_command` ni outil d'édition. Les chemins absolus `/proc/self/cwd/...`
ont été lus dans ce même dépôt. Le test court a lu
`configs/augmentation-rotation-v1.json` et répondu `1`, sans action refusée.
Puis Antigravity a lu exactement `src/gestureos/augment.py` et
`src/gestureos/train.py`, et répondu `No concrete findings.` Aucune revue
des autres fichiers n'est impliquée par cette réponse.

Après la revue, le statut Git ne montre aucune modification par Antigravity.
La suite Python complète a été relancée : 102 tests OK. Les modifications
utilisateur préexistantes sont restées en place. Aucune permission globale ni
option d'approbation automatique n'a été ajoutée.

Pour les prochaines revues en mode sans interface, garder un périmètre de
fichiers court et un délai adapté. Demander `view_file`/`grep_search` seulement,
inspecter les outils réellement appelés et ne considérer la revue comme reçue
que si la réponse finale est non vide. Une réponse sur deux fichiers n'est pas
une validation générale du projet.
