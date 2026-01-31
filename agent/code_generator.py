"""
Générateur de code utilisant l'API Claude d'Anthropic
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict
from anthropic import Anthropic

# Configuration du logging
logger = logging.getLogger(__name__)


class CodeGenerator:
    """Génère du code complet à partir de prompts en utilisant Claude"""

    SYSTEM_PROMPT = """Tu es un expert en développement logiciel. Tu génères du code complet,
fonctionnel et prêt à déployer.

RÈGLES IMPORTANTES:
1. Génère TOUJOURS du code complet et fonctionnel, jamais de placeholders
2. Inclus TOUS les fichiers nécessaires pour un projet fonctionnel
3. Utilise des pratiques modernes et sécurisées
4. Ajoute les fichiers de configuration nécessaires (package.json, requirements.txt, etc.)
5. Génère un README.md avec les instructions d'installation et d'utilisation

FORMAT DE RÉPONSE:
Pour chaque fichier, utilise ce format exact:
```file:chemin/vers/fichier.ext
contenu du fichier ici
```

Par exemple:
```file:index.html
<!DOCTYPE html>
<html>...
```

```file:style.css
body { ... }
```

TYPES DE PROJETS SUPPORTÉS:
- Sites web statiques (HTML/CSS/JS)
- Applications React/Vue/Angular
- APIs Python (Flask/FastAPI)
- APIs Node.js (Express)
- Applications full-stack

Génère TOUJOURS un projet complet avec tous les fichiers nécessaires."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialise le générateur de code

        Args:
            api_key: Clé API Anthropic
            model: Modèle Claude à utiliser
        """
        logger.info(f"Initialisation CodeGenerator avec modèle: {model}")
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "./generated_projects"))

    def generate_project(self, prompt: str, project_name: str) -> Dict[str, str]:
        """
        Génère un projet complet à partir d'un prompt

        Args:
            prompt: Description du projet à générer
            project_name: Nom du projet

        Returns:
            Dictionnaire {chemin_fichier: contenu}
        """
        logger.info(f"Génération du projet: {project_name}")
        logger.info(f"Prompt: {prompt[:100]}...")

        # Appel à l'API Claude
        enhanced_prompt = f"""Génère un projet complet appelé "{project_name}" avec les spécifications suivantes:

{prompt}

IMPORTANT:
- Le projet doit être COMPLET et FONCTIONNEL
- Inclus TOUS les fichiers nécessaires
- Ajoute un fichier render.yaml pour le déploiement sur Render
- Ajoute un Dockerfile si nécessaire
- Le projet doit pouvoir se lancer immédiatement après installation"""

        logger.info("Appel API Claude en cours...")

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": enhanced_prompt}],
            )
            logger.info("Réponse API Claude reçue")
        except Exception as e:
            logger.error(f"Erreur API Claude: {e}")
            raise

        # Parser la réponse pour extraire les fichiers
        content = response.content[0].text
        logger.info(f"Taille de la réponse: {len(content)} caractères")

        files = self._parse_files(content)

        # Ajouter render.yaml si absent
        if "render.yaml" not in files:
            files["render.yaml"] = self._generate_render_yaml(files, project_name)

        logger.info(f"{len(files)} fichiers générés")
        return files

    def _parse_files(self, content: str) -> Dict[str, str]:
        """
        Parse la réponse de Claude pour extraire les fichiers

        Args:
            content: Réponse brute de Claude

        Returns:
            Dictionnaire {chemin: contenu}
        """
        files = {}

        # Pattern pour capturer les blocs de code avec chemin de fichier
        pattern = r"```file:([^\n]+)\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)

        for filepath, file_content in matches:
            filepath = filepath.strip()
            files[filepath] = file_content.strip()
            logger.debug(f"Fichier trouvé: {filepath}")

        # Fallback: chercher les blocs de code classiques avec noms de fichiers
        if not files:
            logger.info("Aucun fichier trouvé avec pattern principal, essai fallback...")
            # Pattern alternatif pour ```language filename
            alt_pattern = r"```(?:\w+)?\s*#?\s*([^\n]+\.[a-zA-Z]+)\n(.*?)```"
            matches = re.findall(alt_pattern, content, re.DOTALL)
            for filepath, file_content in matches:
                if "/" in filepath or "." in filepath:
                    files[filepath.strip()] = file_content.strip()
                    logger.debug(f"Fichier trouvé (fallback): {filepath}")

        logger.info(f"Total fichiers parsés: {len(files)}")
        return files

    def _generate_render_yaml(self, files: Dict[str, str], project_name: str) -> str:
        """
        Génère automatiquement un render.yaml basé sur le type de projet

        Args:
            files: Fichiers du projet
            project_name: Nom du projet

        Returns:
            Contenu du render.yaml
        """
        # Détecter le type de projet
        has_package_json = "package.json" in files
        has_requirements = "requirements.txt" in files
        has_dockerfile = "Dockerfile" in files or "dockerfile" in files
        has_index_html = "index.html" in files or "public/index.html" in files

        # Site statique
        if has_index_html and not has_package_json and not has_requirements:
            return f"""services:
  - type: web
    name: {project_name}
    runtime: static
    buildCommand: echo "Static site ready"
    staticPublishPath: ./
    pullRequestPreviewsEnabled: true
"""

        # Application Node.js
        if has_package_json:
            return f"""services:
  - type: web
    name: {project_name}
    runtime: node
    buildCommand: npm install && npm run build
    startCommand: npm start
    envVars:
      - key: NODE_ENV
        value: production
"""

        # Application Python
        if has_requirements:
            return f"""services:
  - type: web
    name: {project_name}
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
"""

        # Docker
        if has_dockerfile:
            return f"""services:
  - type: web
    name: {project_name}
    runtime: docker
    dockerfilePath: ./Dockerfile
"""

        # Par défaut: site statique
        return f"""services:
  - type: web
    name: {project_name}
    runtime: static
    staticPublishPath: ./
"""

    def save_project(self, files: Dict[str, str], project_name: str) -> Path:
        """
        Sauvegarde les fichiers du projet sur le disque

        Args:
            files: Dictionnaire {chemin: contenu}
            project_name: Nom du projet

        Returns:
            Chemin du dossier projet
        """
        project_path = self.output_dir / project_name
        project_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Sauvegarde dans: {project_path}")

        for filepath, content in files.items():
            file_path = project_path / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            logger.debug(f"Fichier sauvegardé: {filepath}")

        logger.info(f"Projet sauvegardé dans {project_path}")
        return project_path
