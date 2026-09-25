# M13 — tests de relecture logicielle

Date : 2026-09-25.

- Trois tests Python dédiés exercent le vrai moteur C++ avec des échantillons
  synthétiques : fenêtre complète, trou de timestamps, configuration invalide,
  et fenêtre encore ouverte à la fin du flux.
- Suite complète : 105 tests Python réussis.
- Builds PlatformIO `esp32dev` et `dataset` réussis.
- Une capture RAW existante a été relue sans écriture avec des paramètres
  expérimentaux : 200 échantillons acceptés par le validateur, un événement de
  début et une fenêtre encore ouverte à la fin. Cela vérifie le parcours de
  lecture ; ce n'est ni un seuil calibré ni une mesure de qualité de
  segmentation.

Aucun nouveau branchement, flashage, entraînement ML ou essai LCD n'a eu lieu.
