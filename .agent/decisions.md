# Décisions persistantes

- 2026-09-24 — Limiter cette session au périmètre explicitement demandé : phase 0, puis structure minimale du premier test si possible.
- Le MVP précède les modes avancés. Démarrer avec six gestes et des données réelles ; les 20 gestes et 90–95 % sont des objectifs, jamais des résultats acquis.
- ESP32 + MPU6050 + LCD 1602 ; ni OLED, ni moteur DC obligatoire, ni composant supplémentaire supposé disponible.
- Antigravity sera utilisé via la CLI réellement détectée, pour une revue bornée sans modifications concurrentes du dépôt. Aucune commande /usage ou /quota supposée valide.
- Aucun crédit payant, changement de compte ou contournement de quota automatique.
- Les validations compilation, simulation logicielle et mesure physique seront toujours distinguées.
- L'état dans .agent et Git prime sur la mémoire de conversation. Les captures réelles et résultats d'expériences ne doivent jamais être écrasés silencieusement.

- 2026-09-24 — ESP32-D0WDQ6 et Flash 4 Mo vérifiés via ROM ; profil esp32dev confirmé pour le build.
- LCD 1602 à 16 broches confirmé par l’utilisateur ; pas d’achat d’adaptateur I2C à ce stade.
- L’utilisateur demande la préparation maintenant et effectuera les branchements ensuite. Ne pas flasher avant vérification du capteur/câblage.
- I2C à 100 kHz, polling DATA_RDY, UART 230400 et timestamps ESP32 64 bits pour le banc minimal. INT/FIFO si les mesures le justifient.
- Plages ±4 g/±500 degrés/s ; gravité et biais conservés. La calibration complète viendra après caractérisation, sans soustraction aveugle de la gravité.
- Les noms UNKNOWN et leurs scores ne sont pas encore produits par un modèle ; ils restent un objectif d’architecture.
- L’environnement Python 3.14.4 d’acquisition est séparé de PlatformIO. Compatibilité ML à vérifier dans un environnement dédié lors de la phase correspondante.
- Les traces de tests synthétiques ne sont jamais des datasets ni une preuve de performance matérielle.

- 2026-09-24, reprise — Le vérificateur exige la séquence initiale zéro après l’en-tête, pour rejeter aussi les pertes au démarrage. Sept tests logiciels passent.
- Une sortie agy de code 0 accompagnée de « print timeout » n’est pas une revue réussie. Aucun avis reçu à la reprise, aucun quota déduit, pas de relance automatique.
- Clarification utilisateur à la reprise : les branchements seront faits après le développement, lors des tests ou de la collecte. Cette instruction remplace le blocage des étapes logicielles par le matériel. Avancer par jalons testés hors matériel ; ne plus redemander le câblage pendant ces étapes. Les validations physiques et l'évaluation ML réelle restent en attente explicite.

- M2-SOFTWARE : profil dataset séparé du banc, commande CAPTURE bornée et CRC32 sur chaque ligne D (LF inclus). Les deux profils compilent, aucune écriture matérielle.
- Captures UUID par sujet/session, RAW immuables, CSV publié après validation, captures partielles conservées. Fixtures sous work/ uniquement avec provenance synthetic_test et entraînement interdit.
- Le jalon suivant traite le chargement/split reproductible avant tout entraînement réel. Les branchements ne seront demandés que lorsque l’utilisateur voudra passer aux essais physiques.

- M3 : standard library seulement. Revalidation complète des captures ; aucune écriture RAW ; refus par défaut si capture invalide ou doublon.
- Splits session=(sujet,séance) ou sujet, seed42, recherche512 essais, cible60/20/20 approximative, couverture de tous les labels dans chaque partition. Pas de fallback par lignes. Augmentations exclues du chargement RAW.
- Budget demandé : au plus20 points de quota5h ; 12 points consommés observés avant clôture (83→95 %). Priorité à la sauvegarde, aucune nouvelle fonctionnalité après M3.

- M4 : la pause quota est levée après vérification officielle (4 % utilisés au départ).
- Prétraitement v1 : interpolation linéaire sur toute la durée vers200 points, durée physique conservée, aucune décimation sans filtre anti-repliement. Gravité et unités conservées.
- 64 features explicables, ordre versionné ; scaler population ajusté uniquement au train, échelle1 pour variance nulle. Les séquences ne sont pas standardisées par canal.
- Le manifeste est figé : config et empreintes revérifiées, groupes/IDs/couverture contrôlés. Les samples proviennent du snapshot validé, pas d’une seconde lecture du CSV.

- M5 : bibliothèques ML optionnelles installées dans .venv, wheels Linux/Python3.14 vérifiées et versions figées ; PlatformIO inchangé.
- M5 : chaque entrée préparée est recalculée depuis les RAW revérifiés. RF sur features brutes ; SVM/MLP sur scaler train figé. Pas de validation interne MLP ni de probabilités SVM calculées via folds aléatoires.
- M5 : fit train, comparaison macro F1 validation, test jamais évalué. ConvergenceWarning conserve les artefacts mais exclut le modèle du choix automatique. Aucun candidat ne vaut validation embarquée.
- M5 : journal/paramètres/provenance par expérience, publication des bundles sans écrasement et sauvegarde progressive par modèle. Pas de relance automatique d’un lot interrompu.
- M5 : tests du lanceur avec estimateurs factices sans apprentissage, aucun classificateur réel entraîné sur les fixtures. Aucun score ML réel publié faute de données.

- Priorité utilisateur : préparer la collecte hors ligne avant son départ, avec cet ordinateur + ESP32 + MPU6050. M6 conservé en cours, non terminé.
- Collecte hors ligne : chaque prise reste dans pending ; seule une prise techniquement revalidée et humainement confirmée est copiée dans raw, sans supprimer les originaux. Notes de séance séparées et identifiants conservés.
- Deux images fusionnées issues des builds M2 existants sont disponibles localement ; l’installation sauvegarde d’abord les4Mo de Flash. Aucun flashage effectué par l’agent.

- M6 : trois captures réelles swipe_left revérifiées en lecture seule sur deux séances. Le seul rapport de banc60s disponible reste en échec ; ne pas confondre acquisition courte valide et validation matérielle complète.
- M6 : empreintes et versions strictes au chargement, code features/prétraitement figé ; aucun fit à l’inférence. SVM conserve le candidat predict et rejette les égalités/conflits de scores.
- M6 : politique unconfigured = UNKNOWN ; seuils experimental liés au modèle/convention, action_authorized toujours false. La CLI protège IDs, copies et groupes du test final. Calibration/choix automatique des seuils à venir sur validation seulement.
- M6 : les modifications de collecte déjà présentes à la reprise restent intactes et hors du commit M6 ;87 tests passent dans cet état de travail.

- M7 : sélectionner les seuils uniquement sur validation du manifeste figé avec modèle et RAW revérifiés. Les deux contraintes de taux doivent être renseignées explicitement ; aucune valeur par défaut de performance n’est inventée.
- M7 : une politique sélectionnée reste `experimental`, liée aux empreintes modèle/manifeste/IDs de validation et sans autorisation d’action. Les métriques affichent leurs dénominateurs ; absence de connus/inconnus ou contraintes impossibles bloquent sans politique. La calibration probabiliste et le test final sont distincts.
- M7 : tests initiaux avec scores analytiques et estimateurs factices,98 tests OK, aucun modèle réel ni résultat ML. La première tentative de revue Antigravity attendait l’authentification ; ce n’était pas une preuve de quota épuisé.
- M7, suivi : connexion Antigravity établie et revue indépendante en lecture seule reçue. Ses quatre remarques ont été vérifiées et traitées : garde du SHA manifeste dans le contrat, test de la politique liée valide, scores SVM négatifs, CLI bloquée. Suite complète :100 tests OK. Aucun chiffre ML réel ni test matériel ajouté.
