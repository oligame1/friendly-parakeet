# Friendly Parakeet

Agent automatisé basé sur Gemini pour analyser des devis de construction au Québec. Le système extrait le contenu d'un PDF, regroupe les informations par projet, sélectionne les passages les plus pertinents (section 25 du DDN ou autre) et produit une réponse détaillée avec confiance et références aux pages.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Utilisation

```bash
friendly-parakeet \
  --pdf chemin/vers/devis.pdf \
  --question "Quelles sont les exigences de la section 25?" \
  --section 25 \
  --json
```

Paramètres importants :

- `--section` : filtre les pages contenant la section (ex: 25).
- `--top-k` : nombre de passages fournis au modèle Gemini.
- `--json` : affiche une réponse structurée par projet avec confiance et sources.
- `--model` : permet de spécifier un modèle Gemini différent ou `mock` pour les tests hors ligne.

Configurez la clé API avec la variable d'environnement `GEMINI_API_KEY`.

## Développement

Exécuter la suite de tests :

```bash
pytest
```
