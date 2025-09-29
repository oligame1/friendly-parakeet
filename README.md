# Friendly Parakeet

Agent automatise base sur Gemini pour analyser des devis de construction au Quebec. Le systeme extrait les pages d'un PDF, regroupe les informations par projet, selectionne les passages pertinents et produit des reponses detaillees avec un score de confiance et les sources.

## Installation

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
~~~

## Utilisation (CLI)

~~~bash
friendly-parakeet --pdf chemin/vers/devis.pdf --question "Quelles sont les exigences de la section 25?" --section 25 --json
~~~

Parametres importants :

- --section : filtre les pages contenant la section (ex: 25).
- --top-k : nombre de passages fournis au modele Gemini.
- --json : affiche une reponse structuree par projet avec confiance et sources.
- --model : permet de specifier un modele Gemini different ou mock pour les tests hors ligne.

Configurez la cle API avec la variable d'environnement GEMINI_API_KEY.

## Interface web

Lancez le serveur FastAPI inclus :

~~~bash
friendly-parakeet-web
~~~

Par defaut l'application ecoute sur http://localhost:8000. Fournissez la cle Gemini via la variable d'environnement GEMINI_API_KEY. Un endpoint JSON est disponible sur POST /api/analyze pour automatiser les appels.

## Docker

Construisez l'image locale :

~~~bash
docker build -t friendly-parakeet .
~~~

Demarrez l'interface web :

~~~bash
docker run --rm -p 8000:8000 -e GEMINI_API_KEY="votre_cle" friendly-parakeet
~~~

Pour utiliser le CLI dans le conteneur, montez vos PDF et changez la commande :

~~~bash
docker run --rm -e GEMINI_API_KEY="votre_cle" -v /chemin/local/pdf:/data friendly-parakeet friendly-parakeet --pdf /data/devis.pdf --question "..." --section 25 --json
~~~

## Developpement

Executez la suite de tests :

~~~bash
pytest
~~~
