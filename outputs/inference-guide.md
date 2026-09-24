# Inférence PC et rejet UNKNOWN — M6

Le logiciel d’inférence est testé avec des estimateurs factices et des scores
analytiques. **Aucun classificateur de gestes n’a encore été entraîné.**
Au contrôle de reprise, trois captures réelles `swipe_left` étaient valides,
sur deux séances. Il faut poursuivre la collecte des autres gestes et de
`unknown` avant de construire le dataset complet.

Le rapport de banc actuellement conservé (`bench-offline-001.json`) indique
`passed: false`, avec une erreur `imu_init`. Les captures courtes ultérieures
validées ne prouvent pas une acquisition stable pendant 60 secondes. Garder
ce rapport et refaire le [banc](first-mpu6050-test.md) avec de nouveaux noms
lors de la prochaine séance matérielle. Le [kit hors ligne](COLLECTE_SANS_WIFI.md)
reste utilisable pour la collecte.

## Fonctionnement

Une capture complète est revérifiée depuis ses fichiers RAW : identité,
provenance, checksum, cadence, unités et CSV. L’inférence reprend exactement
l’interpolation et les 64 features du pipeline enregistré dans le modèle.
RF reçoit les features brutes ; SVM et MLP reçoivent la standardisation figée
du train. **Aucun fit ni ajustement du scaler à l’inférence.**

La fenêtre reste une capture bornée, pas un flux temps réel segmenté
automatiquement. Les horodatages de l’événement sont ceux de l’ESP32, en
microsecondes ; ils ne représentent pas l’heure civile.

## Charger un modèle local après son entraînement

Le [lanceur de baselines](baselines-guide.md) produira le dossier d’expérience
nécessaire. Les commandes ci-dessous sont destinées à cette future étape ;
elles ne désignent pas un modèle déjà présent.

```bash
.venv/bin/python -m gestureos.predict \
  --experiment experiments/baselines-v1 \
  --model random_forest \
  --raw-root data/raw \
  --capture data/raw/user01/NOM_SEANCE/IDENTIFIANT_CAPTURE \
  --policy configs/rejection.json \
  --output reports/inference/diagnostic-001.json
```

Choix disponibles : `random_forest`, `svm`, `mlp`. Adapter les chemins aux
fichiers réels. Une sortie existante ou située dans les RAW/l’expérience est
refusée. Les captures de test final, leurs copies de signal et les nouveaux
enregistrements appartenant à un groupe réservé au test sont refusés avant
toute prédiction par cette CLI. Le groupe dépend du split choisi : sujet ou
couple sujet/séance. Une capture d’entraînement peut être diagnostiquée, mais
sa prédiction ne constitue pas une mesure de généralisation.

Le chargement contrôle : résultat du modèle terminé et sans besoin de revue,
empreinte/taille du bundle, versions Python et bibliothèques, empreintes du
code de prétraitement, paramètres, labels/classes, dimensions, pipeline,
scaler et partitions. Un modèle terminé peut être inspecté même si les autres
modèles du lot ont été interrompus. Un modèle marqué `needs_review` est refusé.

Les bundles joblib doivent venir d’une expérience locale **de confiance** :
une empreinte détecte une corruption, mais n’authentifie pas un fichier malveillant.
La désérialisation peut exécuter du code. La compatibilité entre versions n’est
pas garantie, d’où les contrôles stricts. [Persistance scikit-learn](https://scikit-learn.org/stable/model_persistence.html).

## Scores et décisions

| Famille | Convention enregistrée | Signification |
|---|---|---|
| RF / MLP | `predict_proba_uncalibrated_v1` | Sorties de `predict_proba`, sans preuve de calibration |
| SVM à deux classes | `svc_binary_signed_v1` | Vecteur `[-d, d]`, dans l’ordre des classes du modèle |
| SVM multiclasse | `svc_ovr_decision_v1` | Scores de décision OVR, qui ne sont pas des probabilités |

Le candidat est celui de `predict`. Son score est celui de sa classe ; sa
marge vaut ce score moins le plus grand score des autres classes. Une égalité
ou un candidat moins bien classé par le vecteur de scores provoque UNKNOWN.
Cette précaution traite notamment les différences possibles entre `predict`
et les scores OVR lors d’égalités de votes SVM. [Contrat officiel SVC](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html).

La politique livrée est **`unconfigured`**, avec des seuils `null` : elle produit
toujours UNKNOWN. Cela permet d’inspecter les scores sans prétendre que des
seuils pertinents ont déjà été trouvés.

Une politique `experimental` permet de tester manuellement `min_score` et
`min_margin`. Elle doit porter le SHA256 du modèle et sa convention de score.
Elle ne peut pas être transférée silencieusement vers un autre modèle. Les
deux seuils doivent être atteints ; la marge doit aussi être strictement
positive, et la classe `unknown` est toujours rejetée. Aucun seuil « optimal »
n’est fourni. L’optimisation sur validation et la mesure des faux acceptés
restent le prochain jalon ; ne pas choisir les seuils sur le test final.

## Événement sauvegardé

Le JSON contient le candidat, les scores par classe, le score et la marge,
la décision `ACCEPTED` ou `UNKNOWN`, le label final, les raisons du rejet,
les horodatages, les empreintes du modèle/capture/politique et la politique
utilisée. `probability_calibrated` reste faux et `action_authorized` reste
faux, même lorsqu’une politique expérimentale accepte le candidat.

Les erreurs d’intégrité ou les sorties invalides du modèle interrompent la
commande ; elles ne créent pas un faux événement de geste. Aucune commande
de servo, moteur, clavier ou autre actionneur n’est envoyée.

## Limites et suite

L’API bas niveau `FrozenBaseline.score_rows` est destinée aux lignes déjà
validées par le chargeur de captures/manifeste. Pour un diagnostic sur fichiers,
utiliser la CLI, qui impose ces contrôles et protège le test final.

Les tests vérifient le code et les contrats avec des doubles sans apprentissage.
La reconnaissance réelle, le taux de faux acceptés/rejetés, la calibration,
le lissage temporel, la segmentation continue et l’inférence ESP32 restent à
mesurer ou développer. La classe supervisée `unknown` ne garantit pas à elle
seule le rejet de tous les mouvements inconnus.
