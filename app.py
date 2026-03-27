from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# -------------------------------
# Load CSV
# -------------------------------
import json
import pandas as pd

with open("manveer.json") as f:
    data = json.load(f)

rows = []

for client_id, client_data in data.items():
    for visit in client_data["visits"]:
        visit["client_id"] = client_id
        rows.append(visit)

df = pd.DataFrame(rows)

df["date"] = pd.to_datetime(df["date"])

print("DATA LOADED:", df.shape)
print(df.head())

# Normalize
df["client_id"] = df["client_id"].astype(str)


# -------------------------------
# Health check
# -------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# -------------------------------
# GET ALL CLIENT IDS
# -------------------------------
@app.route("/clients", methods=["GET"])
def get_all_clients():
    client_ids = sorted(df["client_id"].unique().tolist())
    return jsonify(client_ids)

# -------------------------------
# GET CLIENT DATA
# -------------------------------
@app.route("/clients/<client_id>", methods=["GET"])
def get_client(client_id):

    client_data = df[df["client_id"] == client_id]

    if client_data.empty:
        return jsonify({"error": "client not found"}), 404

    visits = client_data.sort_values("date").to_dict(orient="records")

    return jsonify({"visits": visits})

# -------------------------------
# RUN
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
