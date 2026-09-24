CHECKPOINT ID:
M4-software_preprocessing-verified

PHASE:
Prétraitement et features PC terminés ; matériel différé.

OBJECTIVE:
Préparer les entrées des futures baselines en protégeant intégrité et partitions.

COMPLETED:
Manifestes ready revérifiés (config, SHA, contenu, couverture, groupes, IDs, effectifs).
Snapshots de données validées réutilisés sans relire des CSV potentiellement modifiés.
Interpolation temporelle de durée complète, sans retrait de gravité, padding, crop ou décimation.
64 features documentées ; standardisation exclusivement ajustée sur train et sauvegardée.
CLI preprocess et guide, paramètres versionnés, sortie exclusive hors RAW.

TESTED:
.venv/bin/python -m unittest discover -s tests -v : 43 tests OK.
.venv/bin/python -m gestureos.preprocess --help : OK.
Cas analytiques : rampe, signal constant, timestamps irréguliers, dérivée avec durée physique.
Tests d’intégrité, déplacement RAW, fuite de groupes, perturbation des holdouts, reproductibilité et non-écrasement.
Preuves : reports/m4-preprocessing-tests.txt.

TEST RESULTS:
Tests logiciels seulement. Aucun entraînement, précision ML ou test matériel.
Les fixtures qui imitent des métadonnées hardware restent uniquement sous work/ et ne représentent jamais des mesures physiques.

FAILED / UNRESOLVED:
Aucun test en échec. Pas d’anti-aliasing : réduction du nombre de points refusée.
Normalisation temporelle et features à évaluer sur données réelles ; pas de garantie de précision.
Scalers séquentiels CNN et parité C++ non implémentés. Pipeline en mémoire pour le pilote.

FILES CHANGED:
src/gestureos/{dataset,manifest,features,preprocessing,preprocess}.py ; configs/preprocessing.json ;
tests/test_preprocessing.py ; README.md ; docs/architecture.md ; outputs/preprocessing-guide.md ;
outputs/resume-status.md ; reports/m4-preprocessing-tests.txt ; .agent/*.

CURRENT GIT STATUS:
Base cec4951 propre avant reprise. Lot M4 à sauvegarder dans « feat: add verified preprocessing and train-only feature scaling ».
Vérifier le statut réel à la prochaine reprise.

QUOTA:
Pause précédente levée après contrôle officiel : 4 % utilisés au départ, 20 % après tests sur5h.
Aucun reset/crédit de réinitialisation utilisé par l’agent.

NEXT EXACT STEP:
Logiciel de baselines et expériences selon NEXT_ACTION.md ; aucune nouvelle demande de câblage.

SAFE TO RESUME:
YES

REASON:
Code, configuration, preuves et limites persistants ; RAW préservés ; aucun état matériel modifié.
