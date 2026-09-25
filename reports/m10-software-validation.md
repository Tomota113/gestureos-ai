# M10 — validation logicielle du moteur multimode et des macros

Vérifié le 25 septembre 2026 dans le dépôt local, avant intégration. Les nouveaux
fichiers `firmware/src/modes.*` et `firmware/src/macro_engine.*` restent
indépendants du matériel ; le profil `esp32dev` les compile, sans les relier à
une inférence de geste ni à des broches physiques. Le profil `dataset` conserve
son chemin de collecte.

- Test C++ natif multimode : compilation C++11 avec `-Wall -Wextra -Werror`,
  exécution réussie.
- Test C++ natif macros : mêmes options, exécution réussie.
- Python : 102 tests unitaires réussis.
- PlatformIO : `esp32dev` et `dataset` compilés avec succès.
- Inventaire RAW en lecture seule : 3 captures valides, 0 rejetée, toutes
  `swipe_left`, 1 sujet et 2 séances. Split par séance bloqué (2 groupes, 3
  minimum), split par sujet bloqué (1 groupe, 3 minimum). Aucun modèle réel
  entraîné, aucune métrique ML mesurée.

Le contrôle de M10 refuse `UNKNOWN`, les gestes marqués rejetés et les scores
non finis ou hors de l'intervalle accepté. Cette couche n'établit pas à elle
seule qu'un score est calibré ou qu'une action physique est autorisée. Tout
futur adaptateur d'action devra appliquer la politique de rejet et
`action_authorized` avant de raccorder des actionneurs. Les sorties C++ sont
des intentions et callbacks logiciels, pas des tests matériels.

Les fichiers RAW, pending, notes de séance et les modifications utilisateur
de collecte préexistantes n'ont pas été changés. Le rapport antérieur de
l'équipe de revue est conservé sous `.agents/` comme contexte ; les vérifications
ci-dessus ont été relancées dans cette reprise.
