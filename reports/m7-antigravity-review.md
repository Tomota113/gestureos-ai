# Revue indépendante Antigravity — M7

Le 24 septembre 2026, `agy` en mode `plan` a relu le commit `862af07` en
lecture seule, sans modifier le dépôt. Il a relancé la suite Python : **98 tests
réussis** avant les corrections ci-dessous. Les données matérielles et les
modifications de collecte préexistantes sont restées intactes.

Quatre remarques exploitables ont été retenues :

1. `validate_contract` ne contrôlait pas le format de
   `source_manifest_sha256`. Un contrat construit directement sans cette clé
   pouvait échouer plus tard par `KeyError`. La validation refuse désormais
   cette absence ou une empreinte mal formée.
2. Le chemin positif d’une politique liée au bon manifeste et au bon split
   n’était pas testé. Il l’est maintenant, avec vérification de l’absence
   d’autorisation d’action matérielle.
3. Les seuils de scores SVM signés manquaient de couverture. Un test analytique
   vérifie maintenant les conventions binaires et multiclasse, y compris les
   seuils négatifs.
4. La CLI n’était pas testée lorsque les contraintes rendent la sélection
   impossible. Ce chemin vérifie maintenant le code de retour `1`, les rapports
   conservés et l’absence de `policy.json` et de décisions publiées.

Après ces corrections, la suite complète passe avec **100 tests** ; voir
`reports/m7-antigravity-followup-tests.txt`. Les tests utilisent des doubles et
des scores analytiques : ni seuil réel, ni performance ML, ni mesure matérielle
n’ont été produits par cette revue.
