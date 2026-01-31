"""
Serveur Web API pour l'Agent IA de Déploiement
Expose l'agent via une API REST pour utilisation sur Render
"""

import os
import sys
import traceback
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Gestionnaire d'erreurs global pour toujours renvoyer du JSON
@app.errorhandler(Exception)
def handle_exception(e):
    """Gestionnaire d'erreurs global"""
    logger.error(f"Erreur non gérée: {e}", exc_info=True)
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))

    return jsonify({
        "error": str(e),
        "error_type": type(e).__name__,
        "traceback": tb_str,
        "timestamp": datetime.now().isoformat()
    }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route non trouvée", "error_type": "NotFound"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erreur serveur interne", "error_type": "ServerError"}), 500

# Import de l'agent (après la config Flask)
try:
    from agent import CodeGenerator
    logger.info("Module CodeGenerator importé avec succès")
except Exception as e:
    logger.error(f"Erreur import CodeGenerator: {e}")
    CodeGenerator = None

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

        /* Styles pour les erreurs */
        .error-container {
            background: rgba(255,68,68,0.1);
            border: 2px solid #ff4444;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            display: none;
        }
        .error-container.show { display: block; }
        .error-container h3 {
            color: #ff4444;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .error-message {
            background: rgba(0,0,0,0.4);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            color: #ff6b6b;
            font-weight: 500;
        }
        .error-details {
            background: #1a1a2e;
            border-radius: 8px;
            padding: 15px;
            font-family: monospace;
            font-size: 12px;
            color: #ccc;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .error-details-label {
            color: #888;
            font-size: 12px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .error-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }
        .error-info-item {
            background: rgba(0,0,0,0.3);
            padding: 10px;
            border-radius: 6px;
        }
        .error-info-item label {
            color: #888;
            font-size: 11px;
            margin-bottom: 4px;
        }
        .error-info-item span {
            color: #ff6b6b;
            font-family: monospace;
            font-size: 13px;
        }
        .close-error {
            background: transparent;
            border: 1px solid #ff4444;
            color: #ff4444;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 15px;
            width: auto;
        }
        .close-error:hover {
            background: rgba(255,68,68,0.2);
            transform: none;
            box-shadow: none;
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

        .status-bar {
            background: rgba(0,0,0,0.3);
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .status-bar .api-status {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #00ff88;
        }
        .status-dot.error { background: #ff4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Agent IA de Déploiement</h1>
        <p class="subtitle">Générez des applications complètes avec Claude</p>

        <div class="status-bar">
            <div class="api-status">
                <div class="status-dot" id="statusDot"></div>
                <span id="statusText">Vérification API...</span>
            </div>
            <span id="modelName" style="color: #888;"></span>
        </div>

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

        <!-- Zone d'erreur détaillée -->
        <div class="error-container" id="errorContainer">
            <h3>❌ Erreur</h3>
            <div class="error-message" id="errorMessage"></div>
            <div class="error-info" id="errorInfo"></div>
            <div class="error-details-label">Détails techniques (traceback)</div>
            <div class="error-details" id="errorDetails"></div>
            <button class="close-error" onclick="closeError()">Fermer</button>
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

        // Vérifier le statut de l'API au chargement
        async function checkApiStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                const dot = document.getElementById('statusDot');
                const text = document.getElementById('statusText');
                const model = document.getElementById('modelName');

                if (data.api_configured) {
                    dot.classList.remove('error');
                    text.textContent = 'API Anthropic configurée';
                    text.style.color = '#00ff88';
                    model.textContent = 'Modèle: ' + data.model;
                } else {
                    dot.classList.add('error');
                    text.textContent = 'API non configurée';
                    text.style.color = '#ff4444';
                }
            } catch (e) {
                document.getElementById('statusDot').classList.add('error');
                document.getElementById('statusText').textContent = 'Erreur de connexion';
            }
        }

        checkApiStatus();

        function useExample(type) {
            document.getElementById('prompt').value = examples[type];
            document.getElementById('projectName').value = type + '-project';
        }

        function showError(error) {
            const container = document.getElementById('errorContainer');
            const message = document.getElementById('errorMessage');
            const details = document.getElementById('errorDetails');
            const info = document.getElementById('errorInfo');

            message.textContent = error.error || 'Une erreur inconnue est survenue';

            // Afficher les infos supplémentaires
            let infoHtml = '';
            if (error.error_type) {
                infoHtml += `<div class="error-info-item"><label>Type</label><span>${error.error_type}</span></div>`;
            }
            if (error.status_code) {
                infoHtml += `<div class="error-info-item"><label>Code HTTP</label><span>${error.status_code}</span></div>`;
            }
            if (error.model) {
                infoHtml += `<div class="error-info-item"><label>Modèle</label><span>${error.model}</span></div>`;
            }
            if (error.timestamp) {
                infoHtml += `<div class="error-info-item"><label>Timestamp</label><span>${error.timestamp}</span></div>`;
            }
            info.innerHTML = infoHtml;

            // Afficher le traceback
            if (error.traceback) {
                details.textContent = error.traceback;
                details.style.display = 'block';
            } else if (error.details) {
                details.textContent = JSON.stringify(error.details, null, 2);
                details.style.display = 'block';
            } else {
                details.style.display = 'none';
            }

            container.classList.add('show');
            document.getElementById('result').classList.remove('show');
        }

        function closeError() {
            document.getElementById('errorContainer').classList.remove('show');
        }

        async function generateProject() {
            const prompt = document.getElementById('prompt').value;
            const name = document.getElementById('projectName').value || 'my-project';

            if (!prompt.trim()) {
                showError({ error: 'Veuillez décrire votre projet' });
                return;
            }

            const btn = document.getElementById('generateBtn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const errorContainer = document.getElementById('errorContainer');

            btn.disabled = true;
            loading.classList.add('show');
            result.classList.remove('show');
            errorContainer.classList.remove('show');

            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 180000); // 3 min timeout

                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, name }),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                // Lire d'abord comme texte pour gérer les erreurs HTML
                const responseText = await response.text();
                let data;

                try {
                    data = JSON.parse(responseText);
                } catch (parseError) {
                    // La réponse n'est pas du JSON (probablement une erreur HTML de Render)
                    showError({
                        error: 'Le serveur a renvoyé une réponse invalide (pas du JSON)',
                        error_type: 'ServerError',
                        status_code: response.status,
                        details: {
                            status: response.status,
                            statusText: response.statusText,
                            responsePreview: responseText.substring(0, 500)
                        },
                        traceback: 'Réponse brute du serveur:\\n\\n' + responseText.substring(0, 2000)
                    });
                    return;
                }

                if (data.error || !response.ok) {
                    showError(data);
                    return;
                }

                displayFiles(data.files);
                result.classList.add('show');

            } catch (error) {
                if (error.name === 'AbortError') {
                    showError({
                        error: 'Timeout: La génération a pris trop de temps (> 3 minutes)',
                        error_type: 'TimeoutError',
                        details: { suggestion: 'Essayez avec un prompt plus simple ou réessayez plus tard' }
                    });
                } else {
                    showError({
                        error: 'Erreur réseau: ' + error.message,
                        error_type: 'NetworkError',
                        traceback: error.stack || 'Pas de stack trace disponible'
                    });
                }
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


@app.route("/api/status")
def api_status():
    """Vérifie le statut de l'API"""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    return jsonify({
        "api_configured": bool(api_key and len(api_key) > 10),
        "api_key_preview": api_key[:20] + "..." if api_key else None,
        "model": "claude-sonnet-4-20250514",
        "generator_loaded": CodeGenerator is not None,
        "python_version": sys.version
    })


@app.route("/api/generate", methods=["POST"])
def generate():
    """
    Génère un projet à partir d'un prompt

    Body JSON:
        - prompt: Description du projet
        - name: Nom du projet (optionnel)
    """
    logger.info("=== Nouvelle requête de génération ===")

    try:
        data = request.get_json()
        if not data:
            logger.error("Pas de données JSON reçues")
            return jsonify({
                "error": "Données JSON invalides ou manquantes",
                "error_type": "ValidationError",
                "timestamp": datetime.now().isoformat()
            }), 400

        prompt = data.get("prompt", "")
        name = data.get("name", "generated-project")

        logger.info(f"Projet: {name}, Prompt: {prompt[:100]}...")

        if not prompt:
            return jsonify({
                "error": "Le prompt est requis",
                "error_type": "ValidationError",
                "timestamp": datetime.now().isoformat()
            }), 400

        # Vérifier si CodeGenerator a été importé
        if CodeGenerator is None:
            logger.error("CodeGenerator n'a pas pu être importé")
            return jsonify({
                "error": "Module CodeGenerator non disponible - erreur d'import",
                "error_type": "ImportError",
                "timestamp": datetime.now().isoformat()
            }), 500

        # Vérifier la clé API
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("Clé API non configurée")
            return jsonify({
                "error": "Clé API Anthropic non configurée",
                "error_type": "ConfigurationError",
                "details": "Ajoutez ANTHROPIC_API_KEY dans les variables d'environnement Render",
                "timestamp": datetime.now().isoformat()
            }), 500

        logger.info(f"Clé API présente: {api_key[:20]}...")
        logger.info("Initialisation du générateur...")

        # Générer le projet
        generator = CodeGenerator(api_key=api_key)
        logger.info("Appel à l'API Claude...")
        files = generator.generate_project(prompt, name)
        logger.info(f"Génération terminée: {len(files) if files else 0} fichiers")

        if not files:
            return jsonify({
                "error": "Aucun fichier généré",
                "error_type": "GenerationError",
                "timestamp": datetime.now().isoformat()
            }), 500

        return jsonify({
            "success": True,
            "name": name,
            "files": files,
            "file_count": len(files)
        })

    except Exception as e:
        # Capturer le traceback complet
        exc_type, exc_value, exc_tb = sys.exc_info()
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))

        # Extraire les détails de l'erreur API Anthropic si disponible
        error_details = {}
        status_code = None

        if hasattr(e, 'response'):
            try:
                error_details = e.response.json() if hasattr(e.response, 'json') else {}
                status_code = e.response.status_code if hasattr(e.response, 'status_code') else None
            except:
                pass

        if hasattr(e, 'status_code'):
            status_code = e.status_code

        if hasattr(e, 'body'):
            error_details = e.body if isinstance(e.body, dict) else {"raw": str(e.body)}

        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__,
            "status_code": status_code,
            "model": "claude-sonnet-4-20250514",
            "details": error_details,
            "traceback": tb_str,
            "timestamp": datetime.now().isoformat()
        }), 500


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
