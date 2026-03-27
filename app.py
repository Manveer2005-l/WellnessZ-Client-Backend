from flask import Flask, jsonify, request
import pandas as pd

app = Flask(__name__)

# -------------------------------
# Load dataset ONCE
# -------------------------------

df = pd.read_csv("manveer.csv")  # <-- put your CSV file name

# Ensure date format
df["date"] = pd.to_datetime(df["date"])

# -------------------------------
# Health check
# -------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# -------------------------------
# Get all client IDs
# -------------------------------
@app.route("/clients", methods=["GET"])
def get_all_clients():
    client_ids = df["client_id"].unique().tolist()
    return jsonify(client_ids)

# -------------------------------
# Get client by ID
# -------------------------------
@app.route("/clients/<client_id>", methods=["GET"])
def get_client(client_id):

    client_data = df[df["client_id"] == client_id]

    if client_data.empty:
        return jsonify({"error": "client not found"}), 404

    visits = client_data.sort_values("date").to_dict(orient="records")

    return jsonify({"visits": visits})

# -------------------------------
# Optional: add/update client
# -------------------------------
@app.route("/clients/<client_id>", methods=["POST"])
def upsert_client(client_id):

    payload = request.get_json(force=True)

    global df

    new_rows = pd.DataFrame(payload.get("visits", []))
    new_rows["client_id"] = client_id

    df = pd.concat([df, new_rows], ignore_index=True)

    return jsonify({"status": "saved", "client_id": client_id})

# -------------------------------
# Run
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
