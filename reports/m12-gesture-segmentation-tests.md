# M12 — vérification logicielle de la segmentation candidate

Le 25 septembre 2026 :

- Test natif `gesture_engine_test.cpp` compilé en C++11 avec
  `-Wall -Wextra -Werror` et exécuté avec succès. Il couvre préambule,
  hystérésis, fenêtre complète, longueur trop courte ou trop longue,
  timestamps répétés, interruption du flux, NaN et configuration invalide.
- `pio run -d firmware -e esp32dev` : SUCCESS.
- `pio run -d firmware -e dataset` : SUCCESS.
- La dernière suite Python complète reste celle de M11 : 102 tests OK ;
  aucun fichier Python n'a changé dans M12.

Les échantillons du test natif sont synthétiques. Aucun seuil physique,
score ML, actionneur, téléversement ou essai de segmentation réelle n'a été
validé.
