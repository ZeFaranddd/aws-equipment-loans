"""Equipment Loans API (starter code, Week 12).

Penyimpanan sementara di memori proses. Service `db` (MySQL) direncanakan
pada tahap berikutnya (lihat docker-compose.yml).
"""
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

EQUIPMENT = {}  # id -> dict


@app.get("/health")
def health():
    return jsonify(status="ok", service="equipment-api")


# CREATE
@app.post("/equipment")
def create_equipment():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return jsonify(error="name is required"), 400
    item = {
        "id": str(uuid.uuid4()),
        "name": data["name"],
        "category": data.get("category", ""),
        "status": data.get("status", "available"),
        "borrower": data.get("borrower", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    EQUIPMENT[item["id"]] = item
    return jsonify(item), 201


# LIST (tambahan)
@app.get("/equipment")
def list_equipment():
    return jsonify(list(EQUIPMENT.values()))


# READ
@app.get("/equipment/<item_id>")
def get_equipment(item_id):
    item = EQUIPMENT.get(item_id)
    if not item:
        return jsonify(error="not found"), 404
    return jsonify(item)


# UPDATE
@app.put("/equipment/<item_id>")
def update_equipment(item_id):
    item = EQUIPMENT.get(item_id)
    if not item:
        return jsonify(error="not found"), 404
    data = request.get_json(silent=True) or {}
    for field in ("name", "category", "status", "borrower"):
        if field in data:
            item[field] = data[field]
    return jsonify(item)


# DELETE
@app.delete("/equipment/<item_id>")
def delete_equipment(item_id):
    if EQUIPMENT.pop(item_id, None) is None:
        return jsonify(error="not found"), 404
    return jsonify(deleted=item_id)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
