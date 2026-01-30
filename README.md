# Agent IA de Déploiement Automatique

Un agent intelligent qui génère des applications complètes à partir de prompts et les déploie automatiquement sur Render.

## Fonctionnalités

- **Génération de code**: Utilise Claude (Anthropic) pour générer des projets complets
- **Multi-langages**: Supporte HTML/CSS/JS, React, Python (Flask/FastAPI), Node.js (Express)
- **Déploiement automatique**: Déploie directement sur Render
- **Mode interactif**: Interface conversationnelle pour créer des projets

## Installation

```bash
# Cloner le repo
git clone https://github.com/VOTRE_USERNAME/Site-mau.git
cd Site-mau

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les clés API
cp .env.example .env
# Éditez .env avec vos clés API
```

## Configuration

Créez un fichier `.env` avec vos clés API:

```env
ANTHROPIC_API_KEY=votre_clé_anthropic
RENDER_API_KEY=votre_clé_render
```

### Obtenir les clés API

1. **Anthropic (Claude)**: https://console.anthropic.com/
2. **Render**: https://dashboard.render.com/u/settings#api-keys

## Utilisation

### Commande simple

```bash
# Générer et déployer un projet
python main.py create "Crée un site portfolio moderne avec une section projets"

# Avec un nom personnalisé
python main.py create "Une API REST pour gérer des tâches" --name mon-api

# Sans déploiement automatique
python main.py create "Un blog simple" --no-deploy
```

### Mode interactif

```bash
python main.py interactive
```

### Voir les exemples

```bash
python main.py examples
```

### Lister vos services Render

```bash
python main.py list-services
```

## Exemples de prompts

### Site web statique
```
Crée un portfolio personnel moderne avec:
- Page d'accueil avec présentation
- Section projets avec grille de cartes
- Formulaire de contact
- Design minimaliste et responsive
- Animations CSS fluides
```

### Application React
```
Crée une application de gestion de tâches React avec:
- Interface moderne avec Tailwind CSS
- Ajout, modification, suppression de tâches
- Filtrage par statut (toutes, actives, complétées)
- Sauvegarde dans localStorage
- Mode sombre/clair
```

### API Python
```
Crée une API REST Flask pour une bibliothèque:
- Endpoints CRUD pour les livres
- Authentification JWT
- Base SQLite avec SQLAlchemy
- Validation des données avec Marshmallow
- Documentation OpenAPI/Swagger
```

## Structure du projet

```
Site-mau/
├── agent/
│   ├── __init__.py
│   ├── code_generator.py    # Génération de code avec Claude
│   └── deployer.py          # Déploiement sur Render
├── generated_projects/      # Projets générés (gitignore)
├── main.py                  # Interface CLI
├── requirements.txt
├── .env.example
└── README.md
```

## Workflow

1. **Prompt** → L'utilisateur décrit le projet souhaité
2. **Génération** → Claude génère tous les fichiers nécessaires
3. **Sauvegarde** → Les fichiers sont enregistrés localement
4. **Déploiement** → Le projet est déployé sur Render
5. **URL** → L'utilisateur reçoit le lien du site/API déployé

## Modèles Claude supportés

- `claude-opus-4-5-20250514` (par défaut) - Le plus puissant
- `claude-sonnet-4-20250514` - Bon équilibre vitesse/qualité
- `claude-3-5-haiku-20241022` - Le plus rapide

## Contribuer

Les contributions sont les bienvenues! N'hésitez pas à ouvrir une issue ou une PR.

## Licence

MIT
