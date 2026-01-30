#!/usr/bin/env python3
"""
Agent IA de Déploiement Automatique
===================================
Génère des applications complètes à partir de prompts et les déploie sur Render

Usage:
    python main.py create "Description de votre projet"
    python main.py interactive
    python main.py list-services
"""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
from dotenv import load_dotenv

from agent import CodeGenerator, RenderDeployer

# Charger les variables d'environnement
load_dotenv()

app = typer.Typer(
    name="ai-deployer",
    help="Agent IA pour générer et déployer des applications automatiquement",
    add_completion=False,
)
console = Console()


def get_api_keys() -> tuple[str, str]:
    """Récupère les clés API depuis l'environnement ou demande à l'utilisateur"""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    render_key = os.getenv("RENDER_API_KEY", "")

    if not anthropic_key:
        console.print("[yellow]⚠ Clé API Anthropic non trouvée dans .env[/yellow]")
        anthropic_key = Prompt.ask("Entrez votre clé API Anthropic")

    if not render_key:
        console.print("[yellow]⚠ Clé API Render non trouvée dans .env[/yellow]")
        render_key = Prompt.ask(
            "Entrez votre clé API Render (optionnel, appuyez Entrée pour ignorer)",
            default="",
        )

    return anthropic_key, render_key


def display_banner():
    """Affiche la bannière de l'application"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🤖 AGENT IA DE DÉPLOIEMENT AUTOMATIQUE                 ║
║                                                           ║
║   Propulsé par Claude (Anthropic)                        ║
║   Déploiement sur Render                                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold blue")


@app.command()
def create(
    prompt: str = typer.Argument(..., help="Description du projet à générer"),
    name: str = typer.Option(None, "--name", "-n", help="Nom du projet"),
    deploy: bool = typer.Option(True, "--deploy/--no-deploy", help="Déployer automatiquement"),
    model: str = typer.Option(
        "claude-opus-4-5-20250514",
        "--model",
        "-m",
        help="Modèle Claude à utiliser",
    ),
):
    """
    Génère un projet complet à partir d'un prompt et le déploie sur Render
    """
    display_banner()

    # Récupérer les clés API
    anthropic_key, render_key = get_api_keys()

    # Générer un nom si non fourni
    if not name:
        # Créer un nom à partir du prompt
        words = prompt.split()[:3]
        name = "-".join(words).lower().replace(",", "").replace(".", "")
        name = f"project-{name}"

    console.print(Panel(f"[bold]Projet:[/bold] {name}\n[bold]Prompt:[/bold] {prompt}"))

    # Générer le code
    generator = CodeGenerator(api_key=anthropic_key, model=model)
    files = generator.generate_project(prompt, name)

    if not files:
        console.print("[red]❌ Erreur: Aucun fichier généré[/red]")
        raise typer.Exit(1)

    # Sauvegarder le projet
    project_path = generator.save_project(files, name)

    # Afficher les fichiers générés
    table = Table(title="Fichiers générés")
    table.add_column("Fichier", style="cyan")
    table.add_column("Taille", justify="right", style="green")

    for filepath, content in files.items():
        size = len(content.encode("utf-8"))
        table.add_row(filepath, f"{size} bytes")

    console.print(table)

    # Déployer si demandé
    if deploy and render_key:
        deployer = RenderDeployer(api_key=render_key)
        result = deployer.deploy_via_blueprint(project_path, name)

        if result.get("url"):
            console.print(
                Panel(
                    f"[bold green]✓ Déployé avec succès![/bold green]\n\n"
                    f"[bold]URL:[/bold] {result['url']}\n"
                    f"[bold]Dashboard:[/bold] {result.get('dashboard', 'N/A')}",
                    title="Déploiement réussi",
                )
            )
        else:
            console.print(
                Panel(
                    f"[bold yellow]Projet prêt à déployer[/bold yellow]\n\n"
                    f"[bold]Chemin:[/bold] {project_path}\n\n"
                    f"{result.get('instructions', '')}",
                    title="Instructions de déploiement",
                )
            )
    elif deploy:
        console.print(
            "\n[yellow]⚠ Clé API Render non fournie. "
            "Déploiement manuel requis.[/yellow]"
        )
        console.print(f"\n[bold]Projet sauvegardé dans:[/bold] {project_path}")
        console.print("\nPour déployer manuellement:")
        console.print(f"  1. cd {project_path}")
        console.print("  2. git init && git add . && git commit -m 'Initial'")
        console.print("  3. Créez un repo GitHub et poussez le code")
        console.print("  4. Connectez le repo sur https://dashboard.render.com")

    console.print("\n[green]✓ Terminé![/green]")


@app.command()
def interactive():
    """
    Mode interactif - Créez des projets via une conversation
    """
    display_banner()

    anthropic_key, render_key = get_api_keys()
    generator = CodeGenerator(api_key=anthropic_key)
    deployer = RenderDeployer(api_key=render_key) if render_key else None

    console.print(
        Panel(
            "Bienvenue dans le mode interactif!\n\n"
            "Décrivez le projet que vous souhaitez créer et je le générerai pour vous.\n"
            "Tapez 'quit' ou 'exit' pour quitter.",
            title="Mode Interactif",
        )
    )

    while True:
        console.print()
        prompt = Prompt.ask("[bold cyan]Décrivez votre projet[/bold cyan]")

        if prompt.lower() in ("quit", "exit", "q"):
            console.print("[dim]Au revoir![/dim]")
            break

        if not prompt.strip():
            continue

        # Demander le nom du projet
        name = Prompt.ask(
            "[bold]Nom du projet[/bold]",
            default=f"project-{len(prompt.split()[0][:10])}",
        )

        try:
            # Générer
            files = generator.generate_project(prompt, name)
            if not files:
                console.print("[red]Erreur lors de la génération[/red]")
                continue

            # Sauvegarder
            project_path = generator.save_project(files, name)

            # Proposer le déploiement
            if deployer and Confirm.ask("Voulez-vous déployer sur Render?"):
                result = deployer.deploy_via_blueprint(project_path, name)
                if result.get("url"):
                    console.print(f"\n[bold green]URL:[/bold green] {result['url']}")

            console.print(f"\n[green]✓ Projet '{name}' créé dans {project_path}[/green]")

        except Exception as e:
            console.print(f"[red]Erreur:[/red] {e}")


@app.command("list-services")
def list_services():
    """
    Liste tous vos services Render
    """
    display_banner()

    render_key = os.getenv("RENDER_API_KEY", "")
    if not render_key:
        render_key = Prompt.ask("Entrez votre clé API Render")

    deployer = RenderDeployer(api_key=render_key)
    services = deployer.list_services()

    if not services:
        console.print("[yellow]Aucun service trouvé[/yellow]")
        return

    table = Table(title="Vos services Render")
    table.add_column("Nom", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("URL")

    for item in services:
        service = item.get("service", item)
        name = service.get("name", "N/A")
        stype = service.get("type", "N/A")
        status = service.get("suspended", "active")
        status = "suspended" if status == "suspended" else "active"
        url = service.get("serviceDetails", {}).get("url", "N/A")
        table.add_row(name, stype, status, url)

    console.print(table)


@app.command()
def examples():
    """
    Affiche des exemples de prompts
    """
    display_banner()

    examples_text = """
## Exemples de prompts

### Site web simple
```
Crée un portfolio personnel moderne avec une page d'accueil,
une section projets, et un formulaire de contact. Design minimaliste
avec des animations CSS.
```

### Application React
```
Crée une application React de liste de tâches (todo list) avec:
- Ajout/suppression de tâches
- Marquage comme complété
- Filtrage par statut
- Stockage local (localStorage)
- Design moderne avec Tailwind CSS
```

### API Python
```
Crée une API REST Flask pour gérer une bibliothèque:
- CRUD pour les livres (titre, auteur, ISBN, disponibilité)
- Authentification JWT
- Base de données SQLite
- Documentation Swagger
```

### Application Full-Stack
```
Crée un blog simple avec:
- Frontend React avec routing
- Backend Node.js/Express
- Base de données MongoDB
- Authentification utilisateur
- CRUD pour les articles
- Commentaires
```
"""

    console.print(Markdown(examples_text))


@app.command()
def version():
    """Affiche la version de l'agent"""
    from agent import __version__

    console.print(f"AI Deployer v{__version__}")


if __name__ == "__main__":
    app()
