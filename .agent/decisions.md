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
