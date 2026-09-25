# M11 — vérification logicielle du menu LCD

Le 25 septembre 2026 :

- `g++ -std=c++11 -Wall -Wextra -Werror -Ifirmware/src tests/native/menu_test.cpp firmware/src/menu.cpp -o work/menu_test` : compilation réussie ; `./work/menu_test` : réussi.
- `pio run -d firmware -e esp32dev` : SUCCESS.
- `pio run -d firmware -e dataset` : SUCCESS.
- `.venv/bin/python -m unittest discover -s tests` : 102 tests OK.

Le premier essai de compilation du test natif manquait
`<initializer_list>` ; l'en-tête a été ajouté et la vérification relancée.
Aucun téléversement, câblage, essai LCD physique ou mesure ML n'a eu lieu.
Les modifications utilisateur préexistantes et les captures RAW sont restées
hors de ce jalon.
