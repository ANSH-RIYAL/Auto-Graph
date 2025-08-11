from flask import Flask, jsonify, request
from services.core_service import CoreService
from integrations.auth_provider import verify_token

app = Flask(__name__)
svc = CoreService()


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/items", methods=["GET"])
def list_items():
    return jsonify([i for i in svc.list_items()])


@app.route("/api/items", methods=["POST"])
def create_item():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not verify_token(token):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(force=True)
    name = data.get("name", "")
    return jsonify(svc.create_item(name)), 201


@app.route("/api/search")
def search():
    q = request.args.get("q", "")
    return jsonify(svc.search(q))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)