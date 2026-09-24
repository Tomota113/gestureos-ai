CURRENT PHASE:
M6 terminé côté logiciel,87 tests OK. Trois captures réelles de gauche revérifiées au début de session, pas assez pour entraîner.

NEXT OBJECTIVE:
M7 logiciel : sélection et évaluation des seuils de rejet sur validation uniquement, sans prétendre à une calibration réelle sans dataset complet.

NEXT ACTION:
1. Lire .agent/*, git status et cinq derniers commits, quota officiel. Préserver les changements utilisateur non committés capture.py/dataset.py/test_dataset.py et reports/hardware/.
2. Vérifier en lecture seule si la collecte a avancé, sans modifier les RAW/pending/notes. Ne pas entraîner tant que labels/groupes restent insuffisants. Les captures courtes valides ne remplacent pas le banc60s (seul rapport actuel en échec).
3. Lire outputs/inference-guide.md, inference.py, rejection.py, predict.py et tests/test_inference.py. M6 ne nécessite plus de recommencer toute son implémentation.
4. Concevoir un outil utilisant uniquement les IDs de validation du manifeste figé, avec modèle/contrat/prétraitement revérifiés. Exclure tout test/train de la sélection de seuils ; distinguer sélection de seuils et calibration probabiliste.
5. Définir métriques de rejet avec dénominateurs : inconnus acceptés, connus rejetés, connus correctement acceptés, erreurs connues acceptées. Pas de taux par minute sans flux continu réellement enregistré.
6. Politique liée au SHA du modèle, manifeste et convention de score ; ne pas la marquer validée/embarquable par le seul fait qu’une recherche de seuils s’achève. Gérer les cas sans inconnus/connus et les contraintes irréalisables.
7. Tester avec scores analytiques/estimateurs factices sous work/, sans apprentissage réel sur fixtures. Documenter et mettre à jour les checkpoints après tests et avant fin.

OFFLINE / MATÉRIEL:
Lanceur bash outputs/LANCER_COLLECTE.sh. --check ne touche pas au périphérique.
INSTALLER_ESP32.sh bench|dataset --port PORT est disponible, ne pas lancer sans nécessité/autorisation de flash.
Collecte physique déjà commencée ; éviter les demandes répétées de câblage. Conserver anciennes traces d’échec et nouveaux résultats séparément.
Données exclues de Git : sauvegarde séparée sur autre support à maintenir par l’utilisateur. Jamais de suppression automatique.

ANTIGRAVITY:
Pas de relance automatique après son ancien timeout. Aucun quota supposé.
