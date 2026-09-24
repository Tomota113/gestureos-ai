# Ton kit de collecte sans Wi-Fi

Tout le logiciel nécessaire est présent sur **cet ordinateur**. Tu feras les
gestes devant le capteur, puis choisiras/confirmeras leurs étiquettes. Tu n’as
pas à saisir les mesures à la main : les six axes sont enregistrés par USB.

À la préparation du kit : 69 tests logiciels réussis, aucun test MPU6050 réalisé.
**Mise à jour M6 : trois captures réelles de gauche revérifiées, 87 tests logiciels
réussis.** Le rapport de banc de 60 s conservé est en échec ; le refaire avec
de nouveaux noms. Aucun flashage n’a été effectué par l’agent pendant M6.

## Avant de partir

Emporte l’ordinateur, son chargeur, l’ESP32, le MPU6050, un câble USB de données
et les fils de connexion. Le LCD n’est pas nécessaire à la collecte.
Conserve le dossier du projet à son emplacement actuel, ainsi que `.venv` et
`/home/ibrahim-tomota/.platformio` : les outils y sont déjà installés.
Ne lance pas de réinstallation de paquets une fois hors ligne.

Ouvre un terminal dans le dossier du projet, ou copie cette commande :

```bash
cd /home/ibrahim-tomota/Documents/Codex/2026-09-24/tu
```

Vérifications locales, sans téléchargement et sans toucher à la carte :

```bash
bash outputs/LANCER_COLLECTE.sh --check
bash outputs/INSTALLER_ESP32.sh bench --check
bash outputs/INSTALLER_ESP32.sh dataset --check
```

Ces trois vérifications ont réussi ici. « Aucun port USB » indique seulement
qu’il faut connecter la carte avant les essais. Un test réel avant le départ
serait utile pour résoudre un problème de câble ou de module tant que nous
pouvons encore échanger.

## 1. Branchement et premier essai

Lis le [guide local du premier test](first-mpu6050-test.md), en particulier la
condition d’alimentation du module. Son modèle exact reste inconnu : il faut
confirmer qu’il accepte 3,3 V sur VCC et que ses lignes I2C restent à 3,3 V.
Le câblage prévu **sous cette condition**, USB débranché, est :

| MPU6050 | ESP32 |
|---|---|
| VCC | 3V3 |
| GND | GND |
| SDA | GPIO21 |
| SCL | GPIO22 |
| AD0 | GND |
| INT, XDA, XCL | Non connectées |

Ne pas essayer du 5 V pour résoudre une erreur. Si les caractéristiques du
module ne sont pas connues, conserve sa référence et clarifie-les avant de
l’alimenter. Le guide local contient le détail des contrôles d’axes et cadence.

Après connexion USB, retrouve le port avec :

```bash
bash outputs/LANCER_COLLECTE.sh --check
```

Les exemples suivants emploient `/dev/ttyUSB0` : remplace-le si un autre port
USB est affiché. Ferme tout autre moniteur série.

Installe d’abord le firmware de banc déjà compilé :

```bash
bash outputs/INSTALLER_ESP32.sh bench --port /dev/ttyUSB0
```

Ce script remplace le programme de la carte uniquement après que tu as tapé
`INSTALLER`. Il sauvegarde d’abord les 4 Mo de Flash dans un nouveau dossier
`backups/flash_.../before.bin`. Si cette sauvegarde échoue, il ne flashe pas.
Les images sont destinées uniquement à l’ESP32 classique 4 Mo identifié ici.
Elles sont vérifiées par SHA256 et installées avec l’esptool déjà présent,
sans compilation, téléchargement ou option de forçage.

Mesure ensuite 60 secondes :

```bash
.venv/bin/python scripts/check_stream.py \
  --port /dev/ttyUSB0 --seconds 60 --rate 100 \
  --output reports/hardware/bench-offline-001.serial \
  --report reports/hardware/bench-offline-001.json
```

Change `001` en `002`, etc. pour un nouvel essai. Les fichiers existants sont
protégés contre l’écrasement. Le rapport doit donner `passed: true` ; réalise
aussi les contrôles au repos, d’axes et de mouvements du guide de banc.
Ne collecte pas des centaines de gestes si le capteur ou la cadence échouent.

## 2. Passer à la collecte

Une fois le banc validé, installe le firmware de collecte :

```bash
bash outputs/INSTALLER_ESP32.sh dataset --port /dev/ttyUSB0
```

Puis lance le menu :

```bash
bash outputs/LANCER_COLLECTE.sh
```

Choisis le port USB affiché, puis un identifiant comme `user01`. Utilise le même
identifiant pour toi à chaque séance. Une nouvelle séance est nommée
automatiquement. Décris brièvement la main, la position/fixation du module et
le repère choisi ; ces notes sont conservées sur disque.

Le menu propose gauche, droite, haut, bas, cercle horaire, secousse et `unknown`.
Les directions doivent toujours employer le même repère physique ; note-le et
évite de retourner le capteur entre deux prises sans changer/documenter la séance.

1. Tape le numéro du geste.
2. Attends le compte à rebours, puis fais **un seul geste au signal GO**, dans
   la fenêtre d’environ deux secondes. Le retour au repos doit suivre la même
   consigne d’une prise à l’autre.
3. Tape `o` si tu as fait le bon geste pendant la capture ; `n` si tu t’es trompé.
4. Le menu affiche combien de prises confirmées existent pour chaque geste.
   Tape `q` pour arrêter.

Une capture techniquement valide n’est pas forcément bien étiquetée : ta
confirmation sert précisément à écarter les prises ratées. Une réponse autre
que `o` ne publie pas la prise dans les RAW d’entraînement.

Pour `unknown`, collecte réellement du repos et des mouvements ordinaires
différents des six gestes. Ne l’utilise pas simplement comme poubelle pour
des gestes ratés. Commence par quelques prises de chaque classe pour vérifier
le déroulement, puis répartis les répétitions entre plusieurs vraies séances.
Varie progressivement vitesse et amplitude en documentant les conditions.
Les sessions doivent correspondre à des séances réellement distinctes, pas à
des copies destinées à remplir artificiellement train/validation/test.

Pour reprendre **la même séance interrompue**, utilise son nom affiché :

```bash
bash outputs/LANCER_COLLECTE.sh --subject user01 --session NOM_DE_LA_SEANCE
```

Pour une nouvelle séance, omets `--session`. Aucun quota Internet n’intervient.

## 3. Retrouver et sauvegarder tes données

| Dossier du projet | Contenu |
|---|---|
| `data/raw/` | Prises confirmées, utilisables plus tard après revérification |
| `data/pending/` | Originaux de toutes les tentatives, même ratées ou non confirmées |
| `data/session_notes/` | Notes de montage et de séance |
| `reports/hardware/` | Logs et rapports de banc |
| `backups/` | Sauvegardes du programme ESP32 avant installation |

Chaque prise conserve le log brut, les métadonnées, les contrôles d’intégrité
et, si complète, le CSV des six axes. La publication dans `raw/` est une copie
vérifiée ; l’original reste dans `pending/`. **Ne supprime pas ces dossiers.**
Une prise abandonnée à la confirmation reste dans `pending/` ; refais-la par
le menu, sans déplacer manuellement les fichiers vers `raw/`.

Copie régulièrement les dossiers `data`, `reports/hardware` et `backups` sur
une clé USB ou un autre disque. Git ne sauvegarde pas les données. Les captures
confirmées ont temporairement deux copies locales ; cela ne remplace pas une
sauvegarde sur un autre support.

À ton retour, garde le même dossier et dis « j’ai collecté les données ».
Nous vérifierons les prises, construirons les partitions puis entraînerons les
modèles. Aucun modèle de gestes n’existe encore à ce stade.

## Si quelque chose bloque hors ligne

| Message/symptôme | Action |
|---|---|
| Aucun port USB | Rebrancher, vérifier un câble de données, relancer `--check` |
| Accès refusé au port | Vérifier les droits série et fermer les autres programmes ; ne pas changer les permissions de tous les périphériques |
| `No dataset-firmware READY` | Vérifier que le profil `dataset` a été installé et que le port est correct |
| `Device initialization failed` / `imu_init` | Couper l’alimentation et vérifier module, alimentation, masse, SDA/SCL |
| Erreurs I2C, cadence, saturation | Conserver les logs, corriger le montage ou le mouvement, refaire le banc |
| Déconnexion ou Ctrl+C | Prise conservée dans `pending/`, non ajoutée automatiquement au dataset |
| Fichier/dossier déjà présent | Choisir un nouveau nom ; ne pas écraser la sauvegarde |

Si tu ne peux pas résoudre un problème, conserve les fichiers et le message
exact pour le retour. Il n’est pas nécessaire d’inventer ou de saisir des
mesures pour remplacer une capture manquante.
