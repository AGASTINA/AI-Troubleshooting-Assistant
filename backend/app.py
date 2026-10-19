from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from ai_assistant import diagnose, model_is_configured
from repairs import execute_repair, suggested_repairs

load_dotenv(Path(__file__).with_name(".env"))

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

MAX_MESSAGE_LENGTH = 1000
FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"


@app.get("/")
def frontend_index():
    if not (FRONTEND_DIST / "index.html").is_file():
        return jsonify({"error": "Frontend build is missing."}), 503
    return send_from_directory(FRONTEND_DIST, "index.html")


@app.get("/assets/<path:asset_name>")
def frontend_assets(asset_name):
    return send_from_directory(FRONTEND_DIST / "assets", asset_name)


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "AI Troubleshooting Assistant",
        "engine": "hosted_model" if model_is_configured() else "local_rules",
    }), 200


@app.post("/api/chat")
def chat():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json."}), 415

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    message = payload.get("message")
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Please enter a non-empty message."}), 400

    message = message.strip()
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({
            "error": f"Message must be {MAX_MESSAGE_LENGTH} characters or fewer."
        }), 400

    result = diagnose(message)
    result["repairs"] = suggested_repairs(result["category"], message)
    return jsonify(result), 200


@app.post("/api/repairs/<repair_id>")
def run_repair(repair_id):
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json."}), 415

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    result, status = execute_repair(repair_id, payload.get("confirmed") is True)
    return jsonify(result), status


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Endpoint not found."}), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
