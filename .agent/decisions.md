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
