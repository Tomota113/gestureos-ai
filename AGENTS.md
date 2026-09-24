# GestureOS AI — reprise et collaboration

Avant toute modification, lire .agent/PROJECT_STATE.md, NEXT_ACTION.md,
CHECKPOINT.md et decisions.md ; inspecter git status et les cinq derniers commits.
Le brief complet se trouve dans docs/requirements/.

L'utilisateur a précisé à la reprise que le câblage sera réalisé plus tard,
lors des tests ou de l'ajout des données. Avancer par jalons logiciels sans
attendre le matériel. Valider chaque jalon par compilation/tests hors matériel,
et conserver séparément les validations physiques à faire. Ne jamais présenter
une simulation comme des mesures réelles ou des résultats ML.

Mettre à jour les trois fichiers de checkpoint avant une opération longue,
après un test significatif et avant la fin de session. Ne jamais inventer de
données, résultats ML, commandes disponibles ou niveaux de quota.
Conserver les captures brutes ; ne pas écraser les données ou les changements
de l'utilisateur. Ne pas acheter de crédits ni changer de compte.

Antigravity : CLI détectée `agy`. Utiliser seulement les options vérifiées via
l'aide. Revue indépendante en lecture seule, sans édition concurrente.
Une erreur réseau, de configuration ou d'authentification n'est pas une preuve
de quota épuisé. Arrêter les appels au fournisseur si le quota est épuisé.
