---
name: "graphe-decisions-projet"
description: "Graphe de connaissances (page HTML autonome lisible sans Claude), handover et registre des décisions daté et historisé de n'importe quel projet (dossier Drive ou sujet sur plusieurs chats), tenus dans un Google Drive dédié."
---

# Graphe de décisions et de connaissances d'un projet

Pour consigner une seule décision ou un seul fait en cours de conversation, utiliser la skill légère `consigner-decision`. Celle-ci sert à construire ou mettre à jour le registre complet, le graphe, le handover et le diff d'un projet.

## Posture

Le livrable est un **audit daté des décisions et de la connaissance** : qui a décidé quoi, quand, sur quelle preuve, ce qui reste ouvert, ce qui a été remplacé, ce qui a périmé, où les sources se contredisent, et **ce qui a changé depuis la dernière fois**.

Principes :
- **Un seul système de référence par projet : le registre dans le Google Drive du projet.** Les mémoires des LLM et la mémoire partagée ne sont que des index : un lien, une ligne de résumé, une date. En cas d'écart, le registre fait foi et l'index est corrigé.
- **Rien ne s'efface, tout se date, sur deux axes** (modèle bi-temporel repris de Graphiti) :
  - *temps du monde* : `valid_at`, la date d'effet (quand c'est devenu vrai ou a été décidé), et `invalid_at`, la fin d'effet (quand ça a cessé d'être vrai) ;
  - *temps du registre* : `recorded_at`, consigné le (quand on l'a noté), et `expired_at`, clos le (quand le registre a enregistré la fin).
  Une case vide veut dire inconnu ou toujours en cours, jamais « vrai pour toujours ». La date « revoir le » est une date de travail, pas une fin d'effet. Un changement crée une nouvelle ligne et clôt l'ancienne. Les deux axes permettent de répondre à deux questions distinctes, « qu'est-ce qui était vrai le X ? » et « qu'est-ce qu'on savait le X ? ». Ils servent aussi au diff, à la détection du périmé et à la boucle d'apprentissage.
- **Identifiants stables.** Une entité garde son identifiant d'un passage à l'autre ; on rattache avant de créer.
- **Une synthèse de LLM n'est jamais une preuve.** Chaque élément porte son auteur et son niveau de preuve.
- **Les nœuds les plus connectés ne sont pas les plus décisifs.** Toujours mettre en regard le classement par nombre de liens et la liste des vrais blocages.
- **Le registre trace, il ne décide pas.** Ne jamais arbitrer à la place du décideur légitime.

Ce qui prouve que le travail est juste vient de l'extérieur : une décision confirmée par son décideur, un rappel mesuré sur un étalon annoté à la main, et le test de reprise à froid.

## Quand l'utiliser

- **Création** : premier graphe d'un projet, à partir d'un dossier Drive, d'un sujet discuté sur plusieurs chats, ou des deux.
- **Mise à jour** : un registre existe ; on ne traite que ce qui est nouveau depuis le dernier snapshot, et on produit le diff.
- **Revue** : lister ce qui est échu, périmé, à revoir ou à valider.
- **Migration** : transférer un projet d'un compte à un autre (par exemple d'un compte personnel vers un compte d'entreprise).

## Outils

Les noms d'outils changent selon le compte. Raisonner en fonctions et utiliser ce qui est disponible : recherche dans les conversations passées (par mots-clés, par période, lecture à un endroit précis) ; connecteur Google Drive et Google Sheets (chercher, lire, créer, mettre à jour) ; mémoire de Claude et mémoire partagée si elle existe ; messagerie uniquement en requêtes ciblées ; outil Artifact (guide des pages, publication, déclaration de capacités) ; shell avec Python, Node et un Chrome headless pour vérifier. Si un outil manque, le dire en une ligne et continuer.

## Confidentialité

- Les données d'entreprise vont dans le Drive de l'entreprise. Si le seul Drive accessible est personnel et que le contenu est confidentiel, le signaler **avant** d'écrire et demander confirmation.
- Jamais de mot de passe, de clé, de donnée client brute dans le registre, la mémoire ou la page : référencer par lien.
- Un artifact est privé à sa création ; ne jamais le partager sans demande explicite.

## Configuration du projet (dans « 00 Commencer ici »)

Remplie au premier passage, relue à chaque passage :
- nom du projet, objectif en une phrase, périmètre ;
- mots-clés et alias pour chercher dans les chats ;
- dossier Drive du projet et lien du registre (système de référence) ;
- niveau de confidentialité (personnel, entreprise) et compte autorisé ;
- décideurs par domaine (voir onglet Rôles) ;
- cadence de revue (par défaut hebdomadaire) et date du dernier snapshot.

Le registre porte aussi un onglet **Config** (`cle` | `valeur`), lu par le générateur de la page : `projet`, `objectif`, `constat` (la phrase de titre, à réécrire à chaque passage pour qu'elle reste vraie), `centre` (identifiant de l'entité au centre du graphe), `cadence_jours`, `registre_url`.

## Structure du Drive du projet

```
<Projet>/
  00 Commencer ici            Google Doc : configuration, point de reprise, ordre de lecture
  01 Registre                 Google Sheet : système de référence (voir ci-dessous)
  02 Connaissance             Google Docs thématiques, rédigés à partir du registre, évolution par ajouts datés
  03 Livrables                productions, et les pages de décision pour les décideurs
  04 Sources et preuves       liens et exports de preuves ; sous-dossier « À traiter »
  05 Graphe et handovers      « Graphe – <Projet>.html » (version en cours, lisible sans Claude), graphe-AAAA-MM-JJ.json,
                              handover-AAAA-MM-JJ.md, etalon.md ; sous-dossier « Historique » pour les pages précédentes
  90 Archives                 originaux et versions remplacées
```

Le sous-dossier **04 Sources et preuves / À traiter** est la boîte de dépôt pour ce qui se décide hors des chats : comptes rendus, mails exportés, notes de réunion, captures. Chaque passage le vide : son contenu part dans l'onglet À valider, puis le fichier est déplacé dans 04.

Si le projet a déjà sa propre organisation, la garder et n'ajouter que ce qui manque. Ne jamais réorganiser ni supprimer sans accord.

## Le registre (Google Sheet)

Dates au format AAAA-MM-JJ. Identifiants jamais réutilisés.

- **Entités** : id (E001…) | libellé (30 caractères au plus) | type | alias | fiche (1 à 3 phrases, troisième personne) | bloquant (oui/non) | statut (actif, fusionné dans Exxx, remplacé par Exxx, clos) | créé le | mis à jour le
- **Liens** : id (L001…) | source (Exxx) | cible (Exxx) | relation (verbe court) | statut | date d'effet (valid_at) | fin d'effet (invalid_at) | consigné le (recorded_at) | clos le (expired_at) | revoir le | source (repère) | auteur | niveau de preuve | remplace (Lxxx) | remplacé par (Lxxx)
- **Décisions** : id (D001…) | énoncé | domaine | statut (à trancher, proposé, décidé, remplacé, abandonné) | décideur | proposé par | niveau de preuve | preuve (lien ou citation verbatim) | date d'effet (valid_at) | fin d'effet (invalid_at) | consigné le (recorded_at) | clos le (expired_at) | remplace | remplacé par | alternatives écartées | prédiction ou critère de succès | revoir le | résultat observé | entités (Exxx)
- **Faits** : id (F001…) | énoncé | type (fait, inférence, hypothèse) | entités | source | auteur | niveau de preuve | date d'effet (valid_at) | fin d'effet (invalid_at) | consigné le (recorded_at) | clos le (expired_at) | revoir le | statut (actif, contesté, remplacé, périmé) | remplace
- **Actions** : id (A001…) | action | responsable | échéance | statut | décision liée | mis à jour le
- **Contradictions** : id (C001…) | sujet | version A (source, date) | version B (source, date) | statut (ouverte, tranchée) | tranchée par (Dxxx)
- **Rôles** : domaine | décideur légitime | consultés | source
- **Sources** : repère | titre | auteur (personne nommée, Claude, ChatGPT…) | famille (chat, drive, mail, réunion, registre) | date | URL
- **À valider** : date | onglet cible | ligne proposée | source | proposé par | statut (à valider, appliqué, rejeté)
- **Journal** : date | entrée | auteur
- **Snapshots** : date | version | entités | liens | décisions | fichier .json | artifact

Statuts de lien : `decide`, `fait`, `propose`, `hyp`, `ouvert`, `remplace`, `perime`.

Niveaux de preuve : **primaire** (écrit ou parole du décideur ou de la source d'origine), **rapporté** (quelqu'un rapporte ce qu'un autre a dit ou décidé), **synthèse** (résumé rédigé par un LLM ou un tiers).

Règles d'écriture :
1. `décidé` seulement si la personne qui décide est le décideur légitime du domaine (onglet Rôles) et que la preuve est citable. Si l'utilisateur rapporte la décision d'un autre, écrire `décidé` avec le niveau de preuve `rapporté` et créer l'action « obtenir la confirmation écrite ».
2. Une recommandation de Claude, de ChatGPT ou d'un consultant reste `proposé`, même bien accueillie.
3. Ce que l'utilisateur dit lui-même s'écrit directement. Ce qui est extrait de sources anciennes, d'autres LLM ou de la boîte À traiter va dans **À valider**.
4. Jamais d'écrasement : on crée une nouvelle ligne et on clôt l'ancienne (statut `remplacé`, « remplacé par », `expired_at` = aujourd'hui). L'`invalid_at` de l'ancienne ligne prend :
   - la date d'effet de la nouvelle ligne si le changement vaut à partir de cette date ;
   - la vraie date de fin si elle est connue et différente ;
   - sa propre date d'effet si l'ancienne ligne était fausse dès le départ (correction) : elle n'apparaît alors jamais en mode « vrai au ».
   Une décision abandonnée sans remplaçante prend `invalid_at` = date de l'abandon. Si la fin est inconnue, laisser `invalid_at` vide et noter « fin inconnue » au Journal, sans inventer de date. Une information apprise après coup garde sa vraie date d'effet, même si celle-ci est antérieure à `recorded_at`.
5. Toute information qui vieillit (prix, réglementation, statut d'un tiers, effectif, tarif) reçoit une date « revoir le ». Passée cette date sans revue, elle devient `périmé` au passage suivant. `périmé` veut dire « non revérifié », pas « faux » : cela ne justifie pas de renseigner `invalid_at`.
6. Toute décision importante reçoit une prédiction ou un critère de succès et une date de revue. À la revue, noter le résultat observé.
7. Toute contradiction va dans Contradictions, même si la bonne réponse semble évidente.
8. Chaque passage ajoute une ligne au Journal et une ligne à Snapshots.
9. Si une mémoire partagée existe, y écrire seulement l'index : lien du registre, date du snapshot, une ligne de résumé.

## Déroulé

### 0. Cadrage

Chercher d'abord un projet existant (« 00 Commencer ici », « Registre », « graphe- »). S'il existe, lire la configuration et le dernier snapshot : c'est une mise à jour. Sinon, remplir la configuration ; une seule question si une information indispensable manque (périmètre, Drive cible, confidentialité).

### 1. Collecte

- **Chats** : plusieurs recherches par mots de contenu et par alias, jamais par mots méta. En mise à jour, limiter aux chats postérieurs au dernier snapshot. Lire 1 ou 2 passages par chat, à l'endroit du hit.
- **Drive** : inventaire complet et paginé du dossier. Lire d'abord les documents de pilotage et les registres existants, puis les sources originales selon le budget. Noter l'auteur réel de chaque document.
- **Boîte À traiter** : lire chaque fichier déposé.
- **Mémoire** : lire l'index du projet.
- **Messagerie** : seulement pour prouver une décision ou trancher une contradiction précise.

Remplir l'onglet Sources au fur et à mesure.

### 2. Extraction et rattachement

- **Rattacher avant de créer** : pour chaque entité repérée, chercher dans Entités par libellé et alias. Si elle existe, réutiliser son id et ajouter l'alias. Sinon, créer un nouvel id. En cas de doute, créer un lien `hyp` « même chose ? » plutôt que fusionner.
- Chaque lien et chaque fait ont une source, un auteur, un niveau de preuve, une date d'effet si elle est connue et la date de consignation du jour.
- Quand deux LLM ou deux documents proposent des choses différentes, créer une entité par position et un lien `ouvert` « contredit », plus une ligne dans Contradictions.
- Une action échue dont le statut n'a pas bougé est signalée, sans conclure qu'elle n'a pas été faite.
- Viser 40 à 90 entités affichées ; au-delà, découper par sous-sujet.

### 3. Mise à jour temporelle

- Passer en `périmé` ce dont la date de revue est dépassée.
- Appliquer la règle 4 à chaque ligne `remplacé` ou `abandonné` qui n'a ni `invalid_at` ni mention « fin inconnue ».
- Registre créé avant les colonnes bi-temporelles : le migrer une fois, avec accord. Scinder « valable jusqu'au / revoir le » en `revoir le` (y recopier la valeur) et `invalid_at` (laissé vide), puis ajouter `expired_at`. Renseigner l'`invalid_at` des lignes remplacées avec la date d'effet de leur remplaçante, et noter au Journal la migration et le fait que ces fins sont déduites.
- Lister les décisions dont la date de revue est atteinte, pour noter leur résultat observé.
- Lister les lignes À valider en attente depuis plus de deux cadences de revue.

### 4. Diff (sortie principale d'une mise à jour)

Comparer au snapshot précédent, par identifiant et sur le temps du registre (`recorded_at` ou `expired_at` postérieurs au snapshot) :
- lignes dont la fin d'effet a été datée après coup (correction rétroactive) ;
- nouvelles décisions, décisions tranchées, décisions remplacées ;
- nouvelles questions ouvertes et contradictions, contradictions résolues ;
- faits périmés ou contestés ;
- actions échues, actions faites ;
- entités nouvelles, fusionnées, closes.

### 5. Analyse

- Classement par nombre de liens (programme exclu) en regard des vrais blocages, avec responsables et échéances ; repérer les échéances qui tombent la même semaine.
- Contradictions entre chats, documents et LLM.
- Ce que cette version corrige dans la précédente, erreurs de Claude comprises.
- Couverture et biais : ce qui a été lu, ce qui ne l'a pas été, part de synthèses de LLM, part de preuves primaires.

### 6. Écriture dans le Drive

Mettre à jour le registre (règles ci-dessus), l'onglet Config (`constat` en particulier), « 00 Commencer ici » (point de reprise, date du snapshot), produire et déposer dans 05 la page, le .json et le .md datés (étape 7), ajouter la ligne Snapshots. Pour chaque décision `à trancher` importante, proposer une page de décision d'une page dans 03 : la question, les positions côte à côte avec leurs sources, ce que chaque option implique, qui décide, pour quand.

### 7. Graphe HTML autonome, handover et .json

La page, le handover et le .json sont produits par le générateur `build_graph.py`, jamais écrits à la main. La page est un fichier HTML unique (environ 500 Ko) qui s'ouvre hors ligne dans n'importe quel navigateur, sans Claude, sans compte et sans artifact : d3, polices et données y sont intégrés, elle ne charge rien et n'envoie rien (politique de sécurité de contenu stricte).

1. **Obtenir le générateur.** Si `scripts/build_graph.py` existe à côté de ce fichier (installation par plugin ou dépôt cloné), l'utiliser. Sinon, télécharger la version 1.2.0, figée par son commit :
   ```
   mkdir -p /tmp/gdp && curl -sSL https://codeload.github.com/DamienDu91/Claude-decisions-registry/tar.gz/31c5c5f986ef3735099527c2198004907524f667 | tar xz -C /tmp/gdp --strip-components=4 --wildcards '*/skills/graphe-decisions-projet/scripts'
   ```
   Vérifier les empreintes avec `sha256sum` ; le script vérifie lui-même d3 et les polices (`vendor/SHA256SUMS`). En cas d'écart ou d'échec du téléchargement, s'arrêter et le dire : ne jamais réécrire le générateur de mémoire.
   - `build_graph.py` : `e50504aa96d06b01d9ddebc7dcdf2ea5de21ac38065fae1b39292e955b4b1ba3`
   - `graphe_template.html` : `4633075886c41d41ccad4a3a5d5fda069b9d680b07a2a3a8efff26860036aa94`
2. **Exporter le registre** : lire chaque onglet avec Google Sheets `get_values` (plage `'<onglet>'!A1:Z`) et écrire `registre.json` au format `{"Onglet": [[en-têtes], [ligne], ...]}`, exactement comme renvoyé. Onglets et en-têtes sont reconnus sans tenir compte des accents ni de la casse ; « date d'effet (valid_at) » et « valid_at » sont équivalents.
3. **Générer** : `python3 build_graph.py registre.json sortie/ --precedent graphe-<date précédente>.json`. Le .json du snapshot précédent, téléchargé depuis 05, alimente « Ce qui a changé ». Sorties : `graphe.html`, `graphe.json`, `handover.md`. Chaque alerte d'intégrité imprimée est traitée ou signalée.
4. **Déposer dans 05.** Le connecteur Drive ne remplace pas le contenu d'un fichier existant : le lien stable est celui du dossier 05, pas celui du fichier.
   - Renommer la page en cours « Graphe – <Projet> – <sa date>.html » et la déplacer dans 05/Historique (jamais de suppression).
   - Créer la nouvelle « Graphe – <Projet>.html » : `create_file`, `text/html`, `disableConversionToGoogleType: true`, contenu passé par référence de fichier (`sha256:<empreinte>:<chemin absolu>`) plutôt qu'en base64.
   - Déposer `graphe-AAAA-MM-JJ.json` et `handover-AAAA-MM-JJ.md`.
   - Retélécharger la page et comparer son empreinte à celle du fichier généré.
   Dire au lecteur que Drive n'affiche pas une page HTML : il la télécharge, puis l'ouvre dans son navigateur.
5. **Artifact, facultatif** : pour une page consultable dans Claude, publier le même `graphe.html` comme `index.html` d'un artifact, après avoir déclaré la capacité `downloads` (la page s'en sert si elle est disponible et copie dans le presse-papiers sinon). Pour une mise à jour, republier le même artifact.

La page contient, sans rien à réinventer : une note de synthèse (constat, compteurs cliquables, ce qui a changé, ce qui bloque) ; un graphe de forces interactif (glisser un nœud, survoler pour isoler ses voisins, chercher, filtrer par statut et par niveau de preuve) avec un panneau de détail et une frise temporelle à deux couloirs, « vrai » et « connu », dont le curseur se déplace à la souris, au doigt ou au clavier ; le registre des décisions ; les contradictions côte à côte ; ce qui est à revoir ; l'intégrité et la couverture ; les sources. Modes clair et sombre, mobile, impression, navigation au clavier.

Handover à la troisième personne, lisible sans contexte : en-tête (projet, date de génération, date du registre) ; comment lire (statuts, niveaux de preuve, règle « ne présenter comme décidé que ce qui porte le statut Décidé ») ; programme ; ce qui a changé ; ce qui bloque ; contradictions ; décisions par statut avec date d'effet, fin d'effet s'il y en a une, décideur et preuve ; faits actifs ; périmé et remplacé ; fiches par type ; rôles ; sources ; limites.

Le .json reprend le registre (entités, liens, décisions, faits, actions, contradictions, sources) avec ses identifiants et ses quatre dates (`valid_at`, `invalid_at`, `recorded_at`, `expired_at`) : il doit permettre de reconstruire le registre dans un autre compte.

### 8. Mise à jour automatique

Sur demande, créer une tâche planifiée par projet, à la cadence de l'onglet Config (hebdomadaire par défaut). Son prompt est autonome : identifiants du dossier du projet, du registre et du dossier 05, puis les étapes 7.1 à 7.4, et une ligne au Journal. La tâche régénère la page à partir du registre ; elle ne modifie jamais le registre, à part cette ligne de Journal. Son message final donne les alertes d'intégrité et le lien du dossier 05.

## Migration vers un autre compte

1. Dans le compte d'origine : générer le .json complet et le handover ; retirer tout ce qui est personnel.
2. Vérifier la confidentialité : le contenu peut-il aller dans le compte cible ? Signaler ce qui devrait d'abord passer par le DPO ou l'IT.
3. Dans le compte cible : créer la structure Drive, reconstruire le registre depuis le .json en gardant identifiants et dates, consigner la migration dans le Journal.
4. Les chats du compte d'origine restent inaccessibles depuis le compte cible : leurs repères de source restent, marqués « source externe, non consultable ici ».

## Vérification (toujours, en dernier)

- Intégrité par script : identifiants uniques, liens vers des entités existantes, statuts valides, sources connues, aucun nœud isolé, aucune chaîne « remplace » cassée, aucun `décidé` sans décideur ni preuve. Contrôles bi-temporels :
  - `invalid_at` postérieur ou égal à `valid_at`, et `expired_at` postérieur ou égal à `recorded_at` ;
  - toute ligne `remplacé` a un `invalid_at` ou la mention « fin inconnue » ;
  - aucune ligne `périmé` n'a d'`invalid_at` sans preuve ;
  - une ligne et sa remplaçante ne sont jamais valides à la même date, sauf correction notée au Journal.
  Le générateur fait ces contrôles et imprime ses alertes ; les traiter avant de publier.
- Rendu : si un navigateur headless est disponible, ouvrir la page hors ligne en 1440 et 390 px, vérifier l'absence d'erreur JavaScript et de requête réseau ; relire le début du handover.
- Faits : relire chaque `décidé` et chaque chiffre contre sa source.
- Test bi-temporel, sur une décision remplacée :
  - en mode « vrai au », la veille de sa date d'effet montre l'ancienne ligne et le lendemain la nouvelle ;
  - en mode « connu au », une date antérieure à sa consignation montre encore l'ancienne ligne comme active.
- **Étalon** : au premier passage, proposer d'annoter à la main un chat ou un document représentatif (les décisions qu'il contient vraiment) et le ranger dans 05 sous `etalon.md`. À chaque passage, mesurer combien de ces décisions l'extraction retrouve, et l'écrire dans le Journal.
- Pour un projet à fort enjeu, **test de reprise à froid** : donner le seul handover à un agent séparé et lui poser 5 questions (qui décide de X, qu'est-ce qui bloque, qu'est-ce qui a changé, qu'est-ce qui est périmé…). Chaque erreur signale un trou à combler.

## Restitution

Courte : d'abord ce qui a changé, puis les 3 ou 4 constats qui demandent une action (blocages, contradictions, échéances, périmé), ce que cette version corrige, l'angle mort principal, le rappel mesuré sur l'étalon s'il existe, et une seule prochaine étape. Pas de récapitulatif des étapes.

## Historique des versions

- v1.2 (2026-11-22) : graphe HTML autonome généré par `build_graph.py` (lisible sans Claude ni artifact, hors ligne, d3 et polices intégrés), dépôt dans le Drive avec historique, mise à jour automatique par tâche planifiée, onglet Config, contrôles d'intégrité faits par le générateur. Code publié sur github.com/DamienDu91/Claude-decisions-registry.
- v1.1 (2026-11-22) : modèle bi-temporel repris de Graphiti (`valid_at`, `invalid_at`, `recorded_at`, `expired_at`), règles de fin d'effet, migration des anciens registres, curseur « vrai au » / « connu au », contrôles et test bi-temporels.
- v1.0 (2026-11) : version initiale.

À chaque modification : ajouter une ligne ici, avec la date et ce qui change, et conserver une copie datée de la version précédente.