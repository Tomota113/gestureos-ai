# Prompt général de relais vers Antigravity

À utiliser seulement quand Codex est arrêté ou son quota est indisponible.
L'utilisateur envoie le texte ci-dessous à Antigravity ; aucun numéro de
jalon n'est figé dans le prompt.

> Tu prends temporairement la responsabilité d'ingénierie du dépôt GestureOS AI
> dans ce même répertoire. Codex est arrêté et n'édite aucun fichier en
> parallèle. L'utilisateur t'autorise explicitement à modifier les fichiers
> nécessaires au prochain travail inachevé pendant ce relais ; cette
> autorisation remplace la limite locale « revue en lecture seule » qui
> s'appliquait aux délégations concurrentes.
>
> Lis d'abord `AGENT_STATE.md`, puis `.agent/PROJECT_STATE.md`,
> `.agent/NEXT_ACTION.md`, `.agent/CHECKPOINT.md`, `.agent/decisions.md`,
> `AGENTS.md`, le statut Git et les cinq derniers commits. Si les checkpoints
> semblent datés, réconcilie-les avec le code et Git ; ne recommence pas les
> jalons terminés. Prends la première tâche inachevée que tu peux faire sans
> attendre le câblage, et mène-la jusqu'à un résultat concret.
>
> Travaille par jalon borné. Préserve les captures RAW, pending, les notes et
> toute modification utilisateur préexistante. N'invente ni données réelles,
> ni score ML, ni test matériel, ni niveau de quota. Ne flashe pas l'ESP32 et
> n'achète pas de crédits. Pour chaque changement, réalise toi-même les tests
> et builds appropriés, corrige les échecs et contrôle le diff avant un commit
> ciblé. Les validations logicielles restent distinctes des validations
> physiques. Si un outil ou un quota te bloque, note la cause exacte et la
> tâche inachevée.
>
> Mets `AGENT_STATE.md` et les trois fichiers de checkpoint `.agent/` à jour
> après chaque tâche majeure et avant de t'arrêter. Termine par un compte
> rendu court : fichiers changés, tests réellement réussis, limites et
> première prochaine action. Ne demande à l'utilisateur que les informations
> réellement indispensables ; poursuis tout travail indépendant entre-temps.
