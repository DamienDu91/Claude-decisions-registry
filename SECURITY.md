# Sécurité et confidentialité

## Où vont les données

- Le registre reste dans le Google Drive de l'utilisateur. Les skills n'envoient rien ailleurs.
- `build_graph.py` n'appelle aucun réseau et n'écrit que dans le dossier de sortie indiqué.
- La page générée porte une politique de sécurité de contenu (`default-src 'none'`) : elle ne charge aucune ressource externe et ne peut rien envoyer. Le texte du registre y est inséré comme du texte, jamais comme du HTML.

## Intégrité du générateur

- Les composants tiers sont vérifiés par empreinte SHA-256 à chaque génération.
- Sans copie locale des scripts, la skill télécharge une version figée par étiquette (`v1.2.0`) et compare les empreintes de `build_graph.py` et de `graphe_template.html` à celles écrites dans `SKILL.md` avant de l'exécuter.

## Données sensibles

Ne mettez ni mot de passe, ni clé, ni donnée client brute dans un registre : référencez-les par lien. Une page HTML partagée contient tout le registre au moment de sa génération : partagez-la comme vous partageriez le registre.

## Signaler une faille

Ouvrez une issue sans détail exploitable et demandez un contact privé, ou utilisez le signalement privé de vulnérabilités de GitHub s'il est activé sur ce dépôt.
