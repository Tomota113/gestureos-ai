# Interface LCD 1602 — préparation logicielle M8

Le module `firmware/src/lcd_ui.*` construit deux lignes de 16 caractères
exactement, complétées par des espaces et terminées pour le code C++. Il est
indépendant d’Arduino, des broches et du modèle ML. Les deux profils ESP32 le
compilent et son comportement est vérifié par un test C++ sur ordinateur.

Les états disponibles sont démarrage, prêt, enregistrement, geste accepté,
UNKNOWN et erreur capteur. Les étiquettes sont affichées en majuscules ; les
soulignements deviennent des espaces et les caractères de contrôle sont
neutralisés. Les textes trop longs sont coupés à 16 caractères. UNKNOWN
affiche « TRY AGAIN » et ignore tout score fourni. Aucun pourcentage de
confiance n’est affiché : les scores actuels ne sont pas calibrés et aucun
modèle de gestes réel n’est encore entraîné.

Cette étape **ne prouve pas que le LCD fonctionne physiquement**. Aucun pilote
GPIO, adresse I2C ou brochage n’a été ajouté et rien n’a été flashé. Lors des
essais matériels, il faudra identifier le contrôleur et les niveaux logiques
du LCD à 16 broches, fixer les connexions, écrire l’adaptateur matériel, puis
vérifier lisibilité, mise à jour et absence d’effet sur la cadence du capteur.

Commandes validées pour cette étape :

```bash
g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src \
  tests/native/lcd_ui_test.cpp firmware/src/lcd_ui.cpp -o work/lcd_ui_test
./work/lcd_ui_test
pio run -d firmware -e esp32dev
pio run -d firmware -e dataset
```
