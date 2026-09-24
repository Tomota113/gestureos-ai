# 39. PROTOCOLE CRITIQUE DE CHECKPOINT, QUOTA ET REPRISE

Ce projet sera développé sur plusieurs longues sessions.

Il est possible que :

- le quota Codex soit atteint ;
- le quota Antigravity soit atteint ;
- un modèle devienne temporairement indisponible ;
- une session soit interrompue ;
- le terminal soit fermé ;
- la machine redémarre ;
- je doive reprendre plusieurs heures ou plusieurs jours plus tard.

LE PROJET DOIT ÊTRE CONÇU POUR SURVIVRE À TOUTES CES INTERRUPTIONS.

Je veux pouvoir revenir plus tard et écrire simplement :

`continue`

et que tu puisses reprendre le travail exactement là où il s'était arrêté.

---

# 40. NE JAMAIS DÉPENDRE UNIQUEMENT DE LA MÉMOIRE DE CONVERSATION

Ne considère jamais l'historique du chat comme la seule source d'état du projet.

L'état important doit être sauvegardé DANS LE PROJET.

Créer dès le début :

```text
.agent/
    PROJECT_STATE.md
    NEXT_ACTION.md
    CHECKPOINT.md
    decisions.md
```

Optionnellement :

```text
.agent/checkpoint.json
```

pour une représentation structurée exploitable automatiquement.

Ces fichiers deviennent la mémoire persistante du projet.

---

# 41. PROJECT\_STATE.md

Maintenir en permanence :

`.agent/PROJECT_STATE.md`

Ce fichier doit contenir au minimum :

```text
PROJECT: GestureOS AI

CURRENT PHASE:
...

CURRENT MILESTONE:
...

STATUS:
...

LAST COMPLETED TASK:
...

CURRENT TASK:
...

LAST SUCCESSFUL COMMAND:
...

LAST SUCCESSFUL TEST:
...

FILES MODIFIED:
...

HARDWARE CURRENTLY TESTED:
...

HARDWARE NOT YET TESTED:
...

MODEL CURRENTLY USED:
...

DATASET STATUS:
...

KNOWN BUGS:
...

BLOCKERS:
...

IMPORTANT DECISIONS:
...

DO NOT FORGET:
...

NEXT ACTION:
...
```

Le fichier doit toujours refléter la réalité.

Ne prétends jamais qu'une étape est terminée si elle n'a pas été testée.

---

# 42. NEXT\_ACTION.md

Maintenir :

`.agent/NEXT_ACTION.md`

Ce fichier doit être extrêmement précis.

Exemple :

```text
CURRENT PHASE:
Phase 4 - Data Logger

NEXT OBJECTIVE:
Verify serial acquisition at 100 Hz for MPU6050.

NEXT ACTION:
Run:

python scripts/capture_serial.py --port /dev/ttyUSB0 --rate 100

EXPECTED RESULT:
100 +/- acceptable tolerance samples per second.

IF SUCCESS:
Save 3 test sequences and inspect timestamps.

IF FAILURE:
Inspect serial timing and ESP32 sampling loop.

FILES INVOLVED:
firmware/src/imu.cpp
firmware/src/main.cpp
scripts/capture_serial.py
```

Une nouvelle session doit pouvoir comprendre immédiatement ce qu'elle doit faire simplement en lisant ce fichier.

---

# 43. CHECKPOINTS FRÉQUENTS

NE PAS attendre une erreur de quota pour sauvegarder l'état.

Créer un checkpoint :

- après chaque fonctionnalité terminée ;
- avant une opération importante ;
- après un test concluant ;
- après une correction importante ;
- avant de lancer un travail potentiellement long ;
- avant d'appeler un autre agent/modèle de manière intensive ;
- avant une grosse modification architecturale ;
- avant un entraînement ML long ;
- au minimum après chaque milestone significatif.

Chaque checkpoint doit mettre à jour :

```text
.agent/PROJECT_STATE.md
.agent/NEXT_ACTION.md
.agent/CHECKPOINT.md
```

---

# 44. CHECKPOINT.md

`.agent/CHECKPOINT.md` doit représenter le dernier état connu comme sûr.

Format recommandé :

```text
CHECKPOINT ID:
2026-XX-XX_phase-X_step-Y

PHASE:
...

OBJECTIVE:
...

COMPLETED:
- ...
- ...
- ...

TESTED:
- ...
- ...

TEST RESULTS:
...

FAILED / UNRESOLVED:
- ...

FILES CHANGED:
- ...

COMMANDS THAT WORKED:
- ...

COMMANDS THAT FAILED:
- ...

CURRENT GIT STATUS:
...

NEXT EXACT STEP:
...

SAFE TO RESUME:
YES / NO

REASON:
...
```

---

# 45. UTILISER GIT COMME FILET DE SÉCURITÉ

Si le projet est sous Git :

faire des commits logiques régulièrement.

Exemples :

```text
checkpoint: MPU6050 acquisition stable at 100Hz

checkpoint: dataset serial logger working

checkpoint: six-gesture baseline dataset ready

checkpoint: Random Forest baseline evaluated
```

Ne fais PAS un commit après chaque ligne modifiée.

Fais un commit quand un état cohérent et utile est atteint.

Avant une modification risquée :

1. vérifier `git status` ;
2. sauvegarder l'état ;
3. créer un checkpoint si nécessaire ;
4. seulement ensuite modifier.

NE JAMAIS :

- utiliser `git reset --hard` sans raison explicite ;
- supprimer des modifications utilisateur ;
- écraser silencieusement des fichiers ;
- supprimer des données collectées.

---

# 46. DÉTECTION DU QUOTA ANTIGRAVITY

Si Antigravity CLI est réellement disponible :

vérifier quelles commandes sont effectivement supportées.

La documentation actuelle indique notamment :

```text
/usage
```

ou :

```text
/quota
```

pour afficher/rafraîchir l'utilisation des modèles.

Utilise cette information UNIQUEMENT si cette version installée d'Antigravity supporte réellement ces commandes.

Ne suppose jamais qu'elles fonctionnent sans vérification.

Si possible, avant une opération Antigravity particulièrement longue :

1. vérifier son quota ;
2. déterminer si le travail peut raisonnablement être commencé ;
3. sauvegarder un checkpoint ;
4. lancer le travail.

---

# 47. QUOTA CODEX

Ne prétends jamais connaître le quota restant de Codex si le client ne fournit pas réellement cette information.

Si une commande ou interface officielle permet de lire l'utilisation :

tu peux l'utiliser.

Sinon :

ne devine pas.

Les messages tels que :

- quota exceeded ;
- usage limit reached ;
- rate limit ;
- insufficient quota ;
- too many requests ;
- credits exhausted ;
- model unavailable because of quota ;

doivent être traités comme une interruption potentiellement liée aux limites d'utilisation.

Distingue autant que possible :

TEMPORARY RATE LIMIT

de :

QUOTA / USAGE LIMIT EXHAUSTED

de :

NETWORK ERROR

de :

AUTHENTICATION ERROR.

Ne mélange pas les causes.

---

# 48. SI LE QUOTA ANTIGRAVITY EST ÉPUISÉ

Si Antigravity répond clairement que son quota est épuisé :

NE BOUCLE PAS.

NE RÉESSAYE PAS 20 FOIS.

NE CHANGE PAS AUTOMATIQUEMENT DE COMPTE.

NE CONSOMME PAS DE CRÉDITS PAYANTS SANS MON AUTORISATION.

NE BASCULE PAS SILENCIEUSEMENT SUR UN AUTRE SERVICE PAYANT.

Fais ceci :

1. conserver tous les résultats déjà obtenus ;
2. mettre à jour PROJECT\_STATE.md ;
3. mettre à jour NEXT\_ACTION.md ;
4. mettre à jour CHECKPOINT.md ;
5. enregistrer le message d'erreur utile ;
6. faire un commit Git si l'état courant est cohérent ;
7. arrêter proprement cette branche de travail.

Inscrire notamment :

```text
BLOCKER:
ANTIGRAVITY_QUOTA_EXHAUSTED

LAST SUCCESSFUL STEP:
...

FAILED STEP:
...

NEXT STEP AFTER QUOTA RESET:
...
```

---

# 49. SI LE QUOTA CODEX EST PROCHE OU ÉPUISÉ

Si tu peux détecter de manière fiable que ton quota Codex approche d'une limite :

PRIORITÉ ABSOLUE AU CHECKPOINT.

Arrête de démarrer de nouvelles fonctionnalités.

Fais d'abord :

1. état du projet ;
2. fichiers modifiés ;
3. résultats de tests ;
4. problèmes connus ;
5. prochaine action ;
6. commit si possible.

Si le quota tombe brutalement et empêche toute nouvelle action, les checkpoints réguliers créés AVANT cette interruption doivent permettre la reprise.

C'est précisément pour cela que tu dois sauvegarder fréquemment l'état.

---

# 50. NE PAS ATTENDRE LA DERNIÈRE SECONDE

IMPORTANT :

Il est possible qu'une limite soit atteinte avant que tu puisses écrire un dernier message.

Donc :

NE PAS utiliser cette stratégie :

```text
travailler pendant plusieurs heures
↓
quota atteint
↓
essayer seulement maintenant de sauvegarder
```

Utiliser plutôt :

```text
travail
↓
checkpoint
↓
travail
↓
checkpoint
↓
travail
↓
checkpoint
↓
quota éventuel
```

Ainsi, au pire, seule une petite quantité de travail est perdue.

---

# 51. ARRÊT PROPRE SUR QUOTA

Lorsqu'un quota empêche réellement la continuation et que tu peux encore répondre, termine par un message très court de cette forme :

```text
PAUSED — QUOTA

Provider:
Antigravity / Codex / autre

Current phase:
...

Last completed:
...

Checkpoint:
.agent/CHECKPOINT.md

Next action:
.agent/NEXT_ACTION.md

When quota is available again:
write "continue"
```

Ne me donne pas à ce moment un énorme résumé si toutes les informations sont déjà sauvegardées dans les fichiers.

---

# 52. COMMANDE UTILISATEUR "continue"

Lorsque je dis simplement :

`continue`

TU DOIS INTERPRÉTER CELA COMME :

reprendre GestureOS AI exactement depuis le dernier état persistant.

AVANT TOUTE MODIFICATION :

1. vérifier le dossier courant ;
2. lire :

```text
.agent/PROJECT_STATE.md
.agent/NEXT_ACTION.md
.agent/CHECKPOINT.md
.agent/decisions.md
```

3. exécuter :

```text
git status
git log --oneline -n 5
```

si Git est utilisé ;

4. inspecter les fichiers mentionnés dans NEXT\_ACTION.md ;
5. vérifier que l'environnement correspond encore à celui attendu ;
6. seulement ensuite reprendre.

NE PAS reconstruire le projet depuis zéro.

NE PAS répéter les phases déjà terminées sauf si une vérification est nécessaire.

---

# 53. SI LA CONVERSATION EST NOUVELLE

Même si la nouvelle session ne possède aucun souvenir de la conversation précédente :

les fichiers `.agent/` doivent permettre la reprise.

Procédure :

```text
READ PROJECT STATE
↓
READ CHECKPOINT
↓
READ NEXT ACTION
↓
CHECK GIT
↓
VERIFY ENVIRONMENT
↓
CONTINUE
```

Les fichiers du dépôt sont la source de vérité.

---

# 54. REPRISE ANTIGRAVITY

Si Antigravity possède toujours la conversation précédente et si sa commande `/resume` est disponible :

tu peux l'utiliser lorsque cela apporte réellement du contexte.

Cependant :

NE DÉPENDS PAS de `/resume`.

Même si l'ancienne conversation Antigravity a disparu, le projet doit rester reprenable grâce à :

```text
.agent/
Git
code
tests
documentation
```

---

# 55. PROTECTION CONTRE LES DOUBLES EXÉCUTIONS

Lors d'une reprise, vérifie toujours si l'étape indiquée dans NEXT\_ACTION.md n'a pas déjà été réalisée partiellement.

Exemple :

si NEXT\_ACTION dit :

```text
train Random Forest
```

mais que :

```text
models/random_forest.pkl
reports/rf_results.json
```

existent déjà,

inspecte-les avant de relancer l'entraînement.

Évite :

- doublons ;
- écrasement de datasets ;
- remplacement de modèles ;
- répétition inutile de captures physiques.

---

# 56. DATASET = DONNÉE CRITIQUE

Les datasets collectés manuellement sont précieux.

NE JAMAIS les supprimer automatiquement.

Avant toute opération de preprocessing, conserver :

```text
data/raw/
```

comme source originale immuable autant que possible.

Les transformations vont dans :

```text
data/processed/
data/augmented/
```

Ne jamais remplacer les données RAW par des données transformées.

---

# 57. EXPÉRIENCES ML REPRENABLES

Chaque entraînement important doit produire un dossier ou identifiant d'expérience.

Exemple :

```text
experiments/
    exp_001/
        config.json
        metrics.json
        model.*
        confusion_matrix.png
        notes.md
```

Ainsi, si le quota ou la session tombe après l'entraînement, les résultats restent présents.

Ne dépends pas uniquement d'un affichage terminal pour conserver les métriques.

---

# 58. TÂCHES LONGUES

Avant une tâche longue :

1. écrire ce qui va être exécuté ;
2. sauvegarder le checkpoint ;
3. sauvegarder la configuration de l'expérience ;
4. lancer la tâche.

Lorsque possible, les sorties doivent être écrites progressivement sur disque.

Exemple :

```text
logs/
experiments/
reports/
```

---

# 59. ERREUR != QUOTA

Ne considère pas automatiquement chaque erreur comme une limite de quota.

Exemples :

```text
ModuleNotFoundError
Permission denied
Serial port unavailable
I2C failure
Compilation error
Connection refused
```

doivent être diagnostiqués normalement.

Le protocole QUOTA doit être utilisé seulement lorsqu'il existe une indication crédible de limite d'utilisation.

---

# 60. PAS DE BOUCLE DE RETRY INFINIE

Pour les services IA externes :

si une requête échoue pour rate limit temporaire :

un petit nombre de retries raisonnables peut être tenté si recommandé.

Mais :

PAS DE BOUCLE INFINIE.

Si l'erreur indique clairement un quota épuisé jusqu'à une date/heure future :

arrêter les appels à ce fournisseur.

Sauvegarder le checkpoint.

---

# 61. NE PAS INVENTER LA DATE DE RESET

Si le fournisseur affiche :

```text
Reset in 2h 14m
```

ou une date précise :

tu peux l'enregistrer.

Sinon :

ne devine pas quand le quota reviendra.

Écris seulement :

```text
Quota exhausted.
Reset time unknown.
```

---

# 62. PRIORITÉ EN FIN DE SESSION

Lorsque tu sens qu'une session doit s'arrêter pour une raison quelconque, l'ordre des priorités devient :

1. NE PAS CASSER LE PROJET
2. SAUVEGARDER LE CODE
3. SAUVEGARDER L'ÉTAT
4. SAUVEGARDER LES RÉSULTATS
5. ÉCRIRE LA PROCHAINE ACTION
6. COMMIT SI APPROPRIÉ
7. ARRÊTER

et non :

```text
commencer encore une nouvelle fonctionnalité.
```

---

# 63. CONTRAT DE REPRISE

Le critère de réussite de ce protocole est le suivant :

Je dois pouvoir :

- fermer le terminal ;
- atteindre un quota ;
- redémarrer Linux ;
- revenir le lendemain ;
- ouvrir le même dossier ;
- relancer Codex ;
- écrire :

`continue`

et le développement doit reprendre sans que j'aie à réexpliquer tout GestureOS AI.

Si ce n'est pas possible, le système de checkpoint est insuffisant.

---

# 64. À FAIRE DÈS MAINTENANT

Avant de poursuivre les autres phases de GestureOS AI :

1. crée le dossier `.agent/` ;
2. crée les fichiers de suivi ;
3. initialise leur contenu avec l'état réel actuel ;
4. vérifie Git ;
5. établis le premier checkpoint ;
6. seulement ensuite continue la phase technique en cours.

À partir de maintenant, ce protocole reste actif pendant TOUT le développement de GestureOS AI.
