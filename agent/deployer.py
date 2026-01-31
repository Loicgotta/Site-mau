"""
Module de déploiement automatique sur Render
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests

# Configuration du logging
logger = logging.getLogger(__name__)


class RenderDeployer:
    """Déploie des projets sur Render automatiquement"""

    RENDER_API_BASE = "https://api.render.com/v1"

    def __init__(self, api_key: str):
        """
        Initialise le déployeur Render

        Args:
            api_key: Clé API Render
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _api_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Effectue une requête à l'API Render
        """
        url = f"{self.RENDER_API_BASE}{endpoint}"
        response = requests.request(
            method, url, headers=self.headers, json=data, timeout=60
        )

        if response.status_code >= 400:
            logger.error(f"Erreur API Render: {response.status_code}")
            logger.error(response.text)
            raise Exception(f"Erreur API Render: {response.status_code}")

        return response.json() if response.text else {}

    def deploy_static_site(
        self, project_path: Path, project_name: str
    ) -> Dict[str, str]:
        """Déploie un site statique sur Render"""
        logger.info(f"Déploiement sur Render: {project_name}")

        service_config = {
            "type": "static_site",
            "name": project_name.lower().replace(" ", "-").replace("_", "-"),
            "ownerId": self._get_owner_id(),
            "repo": self._create_github_repo(project_path, project_name),
            "autoDeploy": "yes",
            "branch": "main",
            "buildCommand": "echo 'Build complete'",
            "publishPath": "./",
        }

        try:
            response = self._api_request("POST", "/services", service_config)
            service_id = response.get("service", {}).get("id")
            service_url = response.get("service", {}).get("serviceDetails", {}).get("url")

            logger.info("Service créé!")
            return {
                "service_id": service_id,
                "url": service_url,
                "status": "deployed",
                "dashboard": f"https://dashboard.render.com/web/{service_id}",
            }

        except Exception as e:
            logger.warning("Utilisation du déploiement alternatif...")
            return self._manual_deploy_instructions(project_path, project_name)

    def deploy_via_blueprint(
        self, project_path: Path, project_name: str
    ) -> Dict[str, str]:
        """Déploie via Render Blueprint (render.yaml)"""
        logger.info(f"Déploiement Blueprint: {project_name}")

        render_yaml = project_path / "render.yaml"
        if not render_yaml.exists():
            logger.warning("Pas de render.yaml trouvé, création automatique...")
            self._create_default_render_yaml(project_path, project_name)

        return self._deploy_with_github(project_path, project_name)

    def _get_owner_id(self) -> str:
        """Récupère l'ID du propriétaire du compte Render"""
        try:
            response = self._api_request("GET", "/owners")
            owners = response.get("owners", response) if isinstance(response, dict) else response
            if owners and len(owners) > 0:
                owner = owners[0].get("owner", owners[0])
                return owner.get("id", "")
        except Exception:
            pass
        return ""

    def _create_github_repo(self, project_path: Path, project_name: str) -> str:
        """Crée un repo GitHub pour le projet (si possible)"""
        return ""

    def _deploy_with_github(
        self, project_path: Path, project_name: str
    ) -> Dict[str, str]:
        """Déploie le projet via GitHub + Render"""
        git_dir = project_path / ".git"
        if not git_dir.exists():
            subprocess.run(["git", "init"], cwd=project_path, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=project_path, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit from AI Deployer"],
                cwd=project_path,
                capture_output=True,
            )

        return self._manual_deploy_instructions(project_path, project_name)

    def _manual_deploy_instructions(
        self, project_path: Path, project_name: str
    ) -> Dict[str, str]:
        """Génère des instructions de déploiement manuel"""
        safe_name = project_name.lower().replace(" ", "-").replace("_", "-")

        instructions = f"""
Pour déployer sur Render:

1. Créez un repo GitHub:
   cd {project_path}
   gh repo create {safe_name} --public --source=. --push

2. Allez sur https://dashboard.render.com/new

3. Sélectionnez "New Static Site" ou "New Web Service"

4. Connectez votre repo GitHub: {safe_name}

5. Render détectera automatiquement le render.yaml

Ou utilisez le lien direct:
https://render.com/deploy?repo=https://github.com/VOTRE_USERNAME/{safe_name}
"""

        logger.info(instructions)

        return {
            "status": "ready_to_deploy",
            "project_path": str(project_path),
            "instructions": instructions,
            "render_deploy_url": f"https://render.com/deploy",
        }

    def _create_default_render_yaml(self, project_path: Path, project_name: str):
        """Crée un render.yaml par défaut"""
        safe_name = project_name.lower().replace(" ", "-").replace("_", "-")

        content = f"""services:
  - type: web
    name: {safe_name}
    runtime: static
    buildCommand: echo "Ready"
    staticPublishPath: ./
    pullRequestPreviewsEnabled: true
"""
        (project_path / "render.yaml").write_text(content)

    def check_deployment_status(self, service_id: str) -> Dict[str, Any]:
        """Vérifie le statut d'un déploiement"""
        try:
            response = self._api_request("GET", f"/services/{service_id}")
            return response
        except Exception as e:
            return {"error": str(e)}

    def list_services(self) -> list:
        """Liste tous les services Render"""
        try:
            response = self._api_request("GET", "/services")
            return response.get("services", response) if isinstance(response, dict) else response
        except Exception as e:
            logger.error(f"Erreur: {e}")
            return []

    def get_service_url(self, service_id: str) -> Optional[str]:
        """Récupère l'URL d'un service déployé"""
        try:
            response = self._api_request("GET", f"/services/{service_id}")
            service = response.get("service", response)
            details = service.get("serviceDetails", {})
            return details.get("url")
        except Exception:
            return None
