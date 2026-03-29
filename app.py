from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import json
import os

app = Flask(__name__)
CORS(app)

DATA_FILE = "manveer.json"


def parse_float(value, default=0.0):
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()

    if value == "" or value.upper() == "NA":
        return default

    # remove units like "73 KG"
    cleaned = ""
    dot_used = False
    for ch in value:
        if ch.isdigit():
            cleaned += ch
        elif ch == "." and not dot_used:
            cleaned += ch
            dot_used = True

    if cleaned in ("", "."):
        return default

    try:
        return float(cleaned)
    except ValueError:
        return default


def parse_date(value):
    if value is None:
        return pd.NaT

    value = str(value).strip()
    if not value:
        return pd.NaT

    formats = [
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%a %b %d %Y %H:%M:%S GMT%z (%Z)",
    ]

    for fmt in formats:
        try:
            return pd.to_datetime(value, format=fmt)
        except Exception:
            pass

    return pd.to_datetime(value, errors="coerce")


def load_dataset():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"{DATA_FILE} not found in project root")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    rows = []

    for record in raw_data:
        client_obj = record.get("client", {})
        client_id = client_obj.get("$oid") if isinstance(client_obj, dict) else str(client_obj)

        health_matrix = record.get("healthMatrix", [])
        if not isinstance(health_matrix, list):
            continue

        for visit in health_matrix:
            row = {
                "client_id": str(client_id),
                "date": visit.get("createdDate"),
                "bmi": parse_float(visit.get("bmi")),
                "hm_visceral_fat": parse_float(visit.get("visceral_fat")),
                "hm_muscle": parse_float(visit.get("muscle")),
                "hm_rm": parse_float(visit.get("rm")),
                # fallback defaults for now because age/sex are not present in this JSON
                "age": 30,
                "sex": 1,
            }
            rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        raise ValueError("No usable rows were extracted from the JSON dataset")

    df["client_id"] = df["client_id"].astype(str)
    df["date"] = df["date"].apply(parse_date)

    # keep rows even if date parsing fails, but sort valid dates first
    return df


df = load_dataset()

print("Dataset loaded successfully")
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print(df.head())


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "rows": int(len(df)),
        "clients": int(df["client_id"].nunique())
    })


@app.route("/clients", methods=["GET"])
def get_all_clients():
    client_ids = sorted(df["client_id"].dropna().unique().tolist())
    return jsonify(client_ids)


@app.route("/clients/<client_id>", methods=["GET"])
def get_client(client_id):
    client_rows = df[df["client_id"] == str(client_id)].copy()

    if client_rows.empty:
        return jsonify({"error": "client not found"}), 404

    client_rows = client_rows.sort_values("date", na_position="last")

    visits = []
    for _, row in client_rows.iterrows():
        visits.append({
            "date": row["date"].strftime("%Y-%m-%d") if pd.notna(row["date"]) else None,
            "bmi": float(row["bmi"]),
            "hm_visceral_fat": float(row["hm_visceral_fat"]),
            "hm_muscle": float(row["hm_muscle"]),
            "hm_rm": float(row["hm_rm"]),
            "age": int(row["age"]),
            "sex": int(row["sex"]),
        })

    return jsonify({"visits": visits})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
