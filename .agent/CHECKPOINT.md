CHECKPOINT ID:
OFFLINE-COLLECTION-ready-M6-in-progress

COMPLETED:
M5 baselines reste terminé. Nouvelle priorité utilisateur satisfaite : kit de collecte entièrement local sur cet ordinateur, menu français, notes de séance, confirmation o/n, publication des prises valides dans raw, conservation de toutes les tentatives dans pending.
Firmwares bench/dataset fusionnés depuis les builds déjà validés, empreintes sauvegardées. Installateur local avec backup intégral avant écriture, sans téléchargement. Guide outputs/COLLECTE_SANS_WIFI.md et deux lanceurs.

TESTED:
69 tests Python OK, incluant13 tests nouveaux (acceptation, rejet, interruption, reprise sans écrasement, corruption, provenance synthétique exclue, absence de réseau au check, sauvegarde avant flash et arrêt sur backup incomplet).
LANCER_COLLECTE.sh --check et INSTALLER_ESP32.sh bench/dataset --check : OK, esptool4.11.0.
Preuves reports/offline-collection-tests.txt ; log brut work/offline-tests.log.
M6 : py_compile uniquement. Aucun modèle entraîné, aucun geste physique collecté, aucun capteur testé, aucun flashage.

UNFINISHED:
M6 inférence/rejet commencé avant demande du kit ; quatre nouveaux fichiers sauvegardés sans validation fonctionnelle. Reprendre leurs tests et revue selon NEXT_ACTION.md.
La référence/tension du module MPU et le premier test physique restent à confirmer avant collecte. Aucun port USB détecté pendant ce jalon.

GIT:
Base8bba07f propre avant session. Sauvegarder M6 en commit checkpoint séparé, puis kit hors ligne en commit cohérent. Vérifier git status/log à la reprise.

QUOTA:
Dernier contrôle officiel92 % utilisés sur5h (8 % restants), semaine64 %. Aucun reset/crédit utilisé. Priorité à la sauvegarde, pas de nouvelle fonctionnalité maintenant.

SAFE TO RESUME:
YES — données utilisateur préservées ; kit documenté ; M6 explicitement inachevé.
