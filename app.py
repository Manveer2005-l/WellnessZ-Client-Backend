from flask import Flask, jsonify, request

app = Flask(__name__)

# -------------------------------
# Mock in-memory client database
# -------------------------------
CLIENTS = {
    "TEST_001": {
        "bmi": 28.2,
        "hm_visceral_fat": 13,
        "hm_muscle": 30,
        "hm_rm": 44,
        "age": 27,
        "sex": 1
    },
    "660ee13cda3531415fa05bae": {
        "bmi": 31.5,
        "hm_visceral_fat": 16,
        "hm_muscle": 28,
        "hm_rm": 41,
        "age": 35,
        "sex": 1
    }
}

# -------------------------------
# Health check
# -------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# -------------------------------
# Get client by ID
# -------------------------------
@app.route("/clients/<client_id>", methods=["GET"])
def get_client(client_id):
    client = CLIENTS.get(client_id)

    if not client:
        return jsonify({"error": "client not found"}), 404

    return jsonify(client)

# -------------------------------
# Optional: add / update client
# -------------------------------
@app.route("/clients/<client_id>", methods=["POST"])
def upsert_client(client_id):
    payload = request.get_json(force=True)

    CLIENTS[client_id] = payload
    return jsonify({"status": "saved", "client_id": client_id})

# -------------------------------
# Run locally
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
