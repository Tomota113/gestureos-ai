# Menu LCD 1602 — M11 logiciel

`firmware/src/menu.*` fournit une navigation déterministe et indépendante du
matériel. Le menu contient RUN, DATASET, TEST, MODES, SETTINGS, CALIBRATE,
STATS et ABOUT. Deux entrées sont rendues par page dans un `lcd_ui::Frame` de
deux lignes de 16 caractères ; `>` marque l'entrée sélectionnée. Haut et bas
parcourent les huit entrées avec retour au début/à la fin. Une pression ouvre
la page logique sélectionnée, puis gauche revient au menu. Droite est réservée
et ignorée. Sur une page, les autres entrées de navigation sont ignorées.

L'événement `OpenPage` est seulement une demande de navigation. Il ne lance
ni collecte, ni inférence, ni moteur, ni relais. Aucun lecteur de joystick,
bouton ou clavier, aucun pilote de LCD 16 broches et aucune affectation de
broches n'ont été ajoutés. Le matériel reste à connecter et à caractériser
avant cette intégration. Le rendu logiciel ne mesure pas la latence ni la
fiabilité d'un LCD physique.

Test natif : `tests/native/menu_test.cpp`. Les deux profils PlatformIO
compilent le module ; les 102 tests Python existants restent inchangés.
