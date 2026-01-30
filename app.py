"""
Serveur Web API pour l'Agent IA de Déploiement
Expose l'agent via une API REST pour utilisation sur Render
"""

import os
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Import de l'agent
from agent import CodeGenerator

# Template HTML pour l'interface web
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent IA de Déploiement</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 40px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #00d9ff;
            font-weight: 500;
        }
        input, textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            background: rgba(0,0,0,0.3);
            color: #fff;
            font-size: 16px;
            margin-bottom: 20px;
            transition: border-color 0.3s;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #00d9ff;
        }
        textarea {
            min-height: 150px;
            resize: vertical;
        }
        button {
            width: 100%;
            padding: 18px;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            border: none;
            border-radius: 10px;
            color: #1a1a2e;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0,217,255,0.3);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .result {
            background: rgba(0,255,136,0.1);
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            display: none;
        }
        .result.show { display: block; }
        .result h3 { color: #00ff88; margin-bottom: 15px; }
        .file-list {
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
        }
        .file-item {
            padding: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-family: monospace;
        }
        .file-item:last-child { border-bottom: none; }
        .file-name { color: #00d9ff; }
        .file-content {
            margin-top: 10px;
            background: #0d1117;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 13px;
            white-space: pre-wrap;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        .loading.show { display: block; }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255,255,255,0.1);
            border-top-color: #00d9ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .error {
            background: rgba(255,0,0,0.1);
            border: 1px solid #ff4444;
            color: #ff4444;
        }
        .examples {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .example {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 10px;
            cursor: pointer;
            transition: background 0.3s;
            border: 1px solid transparent;
        }
        .example:hover {
            background: rgba(255,255,255,0.1);
            border-color: #00d9ff;
        }
        .example h4 { color: #00d9ff; margin-bottom: 8px; }
        .example p { font-size: 14px; color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Agent IA de Déploiement</h1>
        <p class="subtitle">Générez des applications complètes avec Claude</p>

        <div class="card">
            <label for="projectName">Nom du projet</label>
            <input type="text" id="projectName" placeholder="mon-super-projet">

            <label for="prompt">Décrivez votre projet</label>
            <textarea id="prompt" placeholder="Ex: Crée un portfolio moderne avec une section projets, un formulaire de contact, et un design minimaliste..."></textarea>

            <button onclick="generateProject()" id="generateBtn">
                ✨ Générer le projet
            </button>
        </div>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Claude génère votre projet...</p>
            <p style="color: #888; font-size: 14px;">Cela peut prendre 30-60 secondes</p>
        </div>

        <div class="result" id="result">
            <h3>✅ Projet généré avec succès!</h3>
            <div class="file-list" id="fileList"></div>
        </div>

        <div class="card">
            <h3 style="margin-bottom: 15px;">💡 Exemples de prompts</h3>
            <div class="examples">
                <div class="example" onclick="useExample('portfolio')">
                    <h4>Portfolio</h4>
                    <p>Site portfolio moderne avec projets et contact</p>
                </div>
                <div class="example" onclick="useExample('todo')">
                    <h4>Todo App</h4>
                    <p>Application de gestion de tâches React</p>
                </div>
                <div class="example" onclick="useExample('api')">
                    <h4>API REST</h4>
                    <p>API Python Flask avec CRUD</p>
                </div>
                <div class="example" onclick="useExample('landing')">
                    <h4>Landing Page</h4>
                    <p>Page d'atterrissage pour startup</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        const examples = {
            portfolio: "Crée un portfolio personnel moderne avec:\\n- Page d'accueil avec présentation animée\\n- Section projets avec grille de cartes\\n- Formulaire de contact fonctionnel\\n- Design minimaliste et responsive\\n- Animations CSS fluides",
            todo: "Crée une application Todo List en HTML/CSS/JS avec:\\n- Ajout et suppression de tâches\\n- Marquage comme complété\\n- Filtrage (toutes, actives, complétées)\\n- Sauvegarde localStorage\\n- Design moderne et épuré",
            api: "Crée une API REST simple en Python Flask avec:\\n- Endpoints CRUD pour des articles de blog\\n- Stockage en mémoire (liste)\\n- Documentation des endpoints\\n- Gestion des erreurs",
            landing: "Crée une landing page moderne pour une startup tech avec:\\n- Hero section avec CTA\\n- Section fonctionnalités\\n- Témoignages clients\\n- Section pricing\\n- Footer avec liens"
        };

        function useExample(type) {
            document.getElementById('prompt').value = examples[type];
            document.getElementById('projectName').value = type + '-project';
        }

        async function generateProject() {
            const prompt = document.getElementById('prompt').value;
            const name = document.getElementById('projectName').value || 'my-project';

            if (!prompt.trim()) {
                alert('Veuillez décrire votre projet');
                return;
            }

            const btn = document.getElementById('generateBtn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');

            btn.disabled = true;
            loading.classList.add('show');
            result.classList.remove('show');

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, name })
                });

                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                displayFiles(data.files);
                result.classList.add('show');

            } catch (error) {
                alert('Erreur: ' + error.message);
            } finally {
                btn.disabled = false;
                loading.classList.remove('show');
            }
        }

        function displayFiles(files) {
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = '';

            for (const [path, content] of Object.entries(files)) {
                const div = document.createElement('div');
                div.className = 'file-item';
                div.innerHTML = `
                    <span class="file-name">📄 ${path}</span>
                    <pre class="file-content">${escapeHtml(content)}</pre>
                `;
                fileList.appendChild(div);
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """Page d'accueil avec interface web"""
    return render_template_string(HTML_TEMPLATE)


@app.route("/health")
def health():
    """Endpoint de santé pour Render"""
    return jsonify({"status": "healthy", "service": "ai-deployer"})


@app.route("/api/generate", methods=["POST"])
def generate():
    """
    Génère un projet à partir d'un prompt

    Body JSON:
        - prompt: Description du projet
        - name: Nom du projet (optionnel)
    """
    try:
        data = request.get_json()
        prompt = data.get("prompt", "")
        name = data.get("name", "generated-project")

        if not prompt:
            return jsonify({"error": "Le prompt est requis"}), 400

        # Vérifier la clé API
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return jsonify({"error": "Clé API Anthropic non configurée"}), 500

        # Générer le projet
        generator = CodeGenerator(api_key=api_key)
        files = generator.generate_project(prompt, name)

        if not files:
            return jsonify({"error": "Aucun fichier généré"}), 500

        return jsonify({
            "success": True,
            "name": name,
            "files": files,
            "file_count": len(files)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/examples")
def examples():
    """Retourne des exemples de prompts"""
    return jsonify({
        "examples": [
            {
                "name": "Portfolio",
                "prompt": "Crée un portfolio personnel moderne avec page d'accueil, section projets, et formulaire de contact"
            },
            {
                "name": "Todo App",
                "prompt": "Crée une application de liste de tâches avec ajout, suppression, et filtrage"
            },
            {
                "name": "API REST",
                "prompt": "Crée une API REST Flask pour gérer des articles de blog avec CRUD"
            },
            {
                "name": "Landing Page",
                "prompt": "Crée une landing page moderne pour une startup avec hero, features, et pricing"
            }
        ]
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
