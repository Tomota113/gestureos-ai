# Protocole de collecte v1

Statut : implémenté côté ESP32 et PC, compilé et testé avec fixtures de protocole.
Pas encore validé sur capteur réel. Le profil `esp32dev` conserve le flux de
banc initial ; le profil `dataset` fournit ce protocole. UART 230400, 8N1.

## Contrat

Au démarrage, le firmware envoie un objet JSON `ready` après initialisation IMU,
ou `error`. Le client attend au plus 10 s. Le texte ROM avant `ready` est
conservé mais n'est pas interprété comme une mesure. Le protocole attendu est
`gestureos-capture-v1` ; le client vérifie aussi la cadence.

Le PC transmet une ligne ASCII :

```text
CAPTURE <identifiant-hexadecimal-32-caracteres> <label> <nombre-echantillons>
```

Le label est borné à 32 caractères : première lettre minuscule, puis lettres
minuscules, chiffres et underscores. Le nombre est compris entre 50 et 500.
Le firmware borne la ligne de commande à 127 octets et refuse les commandes
malformées. `ABORT` interrompt une capture ; aucune reprise partielle automatique.

Le firmware produit successivement :

1. JSON `begin` : protocole, ID, label, nombre, cadence, unités, plages et état
   de calibration. Tout doit correspondre à la requête et au contrat logiciel.
2. N lignes `D,seq,timestamp_us,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps,i2c_errors`.
   Séquence de 0 à N−1, timestamps ESP32 croissants, gravité conservée.
3. JSON `end` : ID, nombre et `crc32` sous forme de huit caractères hexadécimaux.

Le CRC32 IEEE est calculé sur les octets ASCII exacts de toutes les lignes `D`,
**LF final inclus**, par ordre d'émission. Il ne couvre pas les objets JSON.
La vérification des métadonnées complète le contrôle CRC des mesures.
Un CRC protège contre des erreurs de transmission, pas contre un étiquetage
humain incorrect ou une IMU mal orientée.

Le client refuse les captures avec perte/duplication de trame, compteur initial
non nul, unité/configuration incompatible, I2C en erreur, NaN/inf, saturation,
timestamps incohérents, fin absente ou mauvais CRC. Il applique aussi les
tolérances de cadence du test de banc : moyenne ±2 %, 95 % des intervalles à
±20 % de la période, aucun intervalle supérieur à deux périodes.

Une capture de 200 mesures à 100 Hz couvre environ 1,99 s **entre première et
dernière mesure** ; le temps d'émission de la fenêtre est d'environ 2 s.
Ce calcul décrit le contrat, pas une durée physiquement mesurée ici.

## Conservation et provenance

Chaque dossier `data/raw/<subject>/<session>/<capture_id>/` est créé exclusivement.
Un ID déjà présent provoque un refus, jamais un écrasement. Il contient :

- `request.json` : sujet pseudonymisé, session, label, configuration demandée,
  heure UTC, version de l'outil, provenance, absence de calibration/prétraitement ;
- `serial.raw` : octets reçus, y compris diagnostics et flux partiel ;
- `samples.csv` : seulement après validation complète du protocole ;
- `result.json` : état, erreur éventuelle, SHA256 du log brut, configuration
  annoncée par le firmware et métriques d'intégrité si la capture est complète.

Le CSV est écrit dans un fichier temporaire du dossier, synchronisé puis publié
par lien dur atomique (Linux). Le log est vidé vers le système à chaque trame,
puis synchronisé sur disque à la fermeture. Une coupure électrique brutale
peut perdre les derniers octets encore dans les caches ; rien n'est reconstruit
ou inventé à la reprise. Un `result.json` absent/invalide signifie capture non
validée, même si un CSV existe. Conserver ces dossiers pour diagnostic.

Une déconnexion, Ctrl+C ou erreur de protocole donne `status: incomplete`,
avec log conservé et sans CSV publié. Le client tente un ABORT borné si le port
est encore ouvert. Il ne relance jamais automatiquement une capture physique.

`eligible_for_training` signifie uniquement provenance matérielle déclarée et
intégrité du protocole validée ; la qualité du geste et du label reste à
contrôler. Les fixtures ont `source_kind: synthetic_test` et restent toujours
inéligibles, même si leur protocole est valide. Les tests les écrivent seulement
sous `work/`, jamais sous `data/raw/`.

## Splits ultérieurs

Les IDs sujet/session seront conservés jusque dans les splits train/validation/test.
Les transformations ne modifieront pas les dossiers bruts. Toute augmentation
référencera le capture_id parent et sera effectuée après partitionnement.
La classe `unknown` est réservée aux vrais mouvements négatifs collectés ; ce
protocole ne fabrique aucun exemple de geste ou de mouvement inconnu.
