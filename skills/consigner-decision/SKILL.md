---
name: "consigner-decision"
description: "Consigne en quelques secondes une décision, une action, un fait ou une correction dans le registre daté du projet (Google Drive), dès qu'ils apparaissent dans la conversation."
---

# Consigner une décision

Geste léger et fréquent, à faire au fil de l'eau. Le registre est celui défini par la skill `graphe-decisions-projet` (Google Sheet « 01 Registre » dans le dossier Drive du projet). Ne pas construire de graphe ici.

## Quand

- L'utilisateur tranche (« on part sur… », « c'est validé », « non, on abandonne… »).
- Il rapporte la décision d'un autre (« la directrice a dit oui »).
- Une échéance, un responsable ou une action est fixé.
- Il corrige un fait ou une décision antérieure.
- Il dit « consigne », « note la décision », « ajoute au registre ».

Si la conversation porte sur un projet qui a un registre et qu'une de ces situations apparaît, proposer la ligne en une phrase, sans attendre la fin de l'échange.

## Comment

1. **Trouver le registre** : chercher le dossier du projet et son registre dans le Drive. S'il n'existe pas, proposer de le créer avec `graphe-decisions-projet`, ou d'écrire la ligne dans un nouveau registre minimal (onglets Décisions, Actions, Journal).
2. **Lire avant d'écrire** : vérifier si la décision ou l'entité existe déjà, pour réutiliser son identifiant ou clôturer l'ancienne ligne.
3. **Choisir l'onglet** : Décisions, Actions, Faits, Contradictions, ou À valider.
4. **Remplir** :
   - date d'effet (`valid_at`, quand c'est devenu vrai, même si c'est antérieur à aujourd'hui) et date de consignation (`recorded_at`, aujourd'hui), au format AAAA-MM-JJ ; laisser vides `invalid_at` et `expired_at` ;
   - décideur et niveau de preuve : **primaire** si le décideur l'écrit ou le dit lui-même ; **rapporté** si l'utilisateur rapporte la décision d'un autre (ajouter alors l'action « obtenir la confirmation écrite ») ; **synthèse** si cela vient d'un résumé de LLM ;
   - preuve : citation verbatim de l'utilisateur ou lien ;
   - pour une décision importante : la prédiction ou le critère de succès, et la date de revue ;
   - pour une information qui vieillit : la date « revoir le » (une date de travail, distincte de la fin d'effet).
5. **Remplacer sans écraser** : une décision qui change crée une nouvelle ligne ; l'ancienne passe en `remplacé`, avec l'identifiant de la nouvelle et `expired_at` = aujourd'hui. Son `invalid_at` prend la date d'effet de la nouvelle ligne, ou sa propre date d'effet si elle était fausse dès le départ. Une décision abandonnée sans remplaçante prend `invalid_at` = date de l'abandon. Si la fin est inconnue, laisser `invalid_at` vide et le noter au Journal, sans inventer de date. Si le registre n'a pas encore ces colonnes, le signaler et proposer la migration décrite dans `graphe-decisions-projet`.
6. **Journal** : une ligne datée.
7. **Page du graphe** : si le dossier 05 du projet contient une page « Graphe – <Projet>.html », proposer en une phrase de la régénérer (étape 7 de `graphe-decisions-projet`), sans le faire d'office.
8. **Index** : si une mémoire partagée existe, y mettre à jour seulement le lien du registre et la date. Pas de contenu confidentiel.

## Règles

- `décidé` seulement sur la parole ou l'écrit du décideur. Une recommandation de Claude ou d'un autre LLM reste `proposé`, même bien accueillie.
- Ce qui ne vient pas directement de l'utilisateur va dans À valider.
- Données d'entreprise dans le Drive de l'entreprise ; si seul un Drive personnel est accessible et que le contenu est confidentiel, demander avant d'écrire.
- Jamais de mot de passe, de clé ou de donnée client brute.

## Réponse

Une ligne : ce qui a été consigné, avec son identifiant (par exemple « D014 consignée : zone US, décidée par X le 27 nov., preuve rapportée ; confirmation écrite à obtenir, A022 »). Si l'écriture échoue, le dire et donner la ligne à copier.

## Historique des versions

- v1.2 (2026-11-22) : alignée sur `graphe-decisions-projet` v1.2 ; après une consignation, proposer de régénérer la page du graphe si le projet en a une.
- v1.1 (2026-11-22) : dates bi-temporelles (`valid_at`, `recorded_at` à la création ; `invalid_at`, `expired_at` au remplacement ou à l'abandon), alignées sur `graphe-decisions-projet` v1.1.
- v1.0 (2026-11) : version initiale.

À chaque modification : ajouter une ligne ici et garder cette skill alignée sur la version de `graphe-decisions-projet`.