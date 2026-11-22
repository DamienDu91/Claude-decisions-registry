# Journal des versions

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et le projet suit le [versionnage sémantique](https://semver.org/lang/fr/).

## [1.2.0] - 2026-11-22

### Ajouté
- `build_graph.py` : génère depuis le registre une page HTML autonome (graphe de forces interactif, frise « vrai au » et « connu au », synthèse, registre, contradictions), le handover et le .json.
- Dépôt de la page dans Google Drive avec historique des versions précédentes.
- Mise à jour automatique par tâche planifiée.
- Onglet `Config` lu par le générateur.
- Contrôles d'intégrité et bi-temporels faits par le générateur.
- Plugin Claude Code et exemple fictif complet.

### Modifié
- La page artifact devient facultative et reprend le même fichier HTML.

## [1.1.0] - 2026-11-22

### Ajouté
- Modèle bi-temporel repris de Graphiti : `valid_at`, `invalid_at`, `recorded_at`, `expired_at`.
- Règles de fin d'effet, migration des anciens registres, curseur « vrai au » et « connu au ».

## [1.0.0] - 2026-11

### Ajouté
- Première version des skills `graphe-decisions-projet` et `consigner-decision`.
