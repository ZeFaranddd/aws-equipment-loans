"""Equipment Loans API (Track A: EC2 + RDS MySQL).

Flask + PyMySQL. Konfigurasi koneksi dibaca dari environment variable
(lihat .env.example); tidak ada kredensial di kode.
"""
import os
import uuid

import pymysql
from flask import Flask, jsonify, request

app = Flask(__name__)

FIELDS = ("name", "category", "status", "borrower")
VALID_STATUS = ("available", "borrowed")

SCHEMA = """
CREATE TABLE IF NOT EXISTS equipment (
    id         CHAR(36)     NOT NULL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    category   VARCHAR(50)  NOT NULL DEFAULT '',
    status     VARCHAR(20)  NOT NULL DEFAULT 'available',
    borrower   VARCHAR(100) NOT NULL DEFAULT '',
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


# ---------- akses database ----------
def get_conn():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "equipmentdb"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=5,
    )


def init_db():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
    finally:
        conn.close()


def _clean(row):
    if row and row.get("created_at") is not None:
        row["created_at"] = row["created_at"].isoformat() + "+00:00"  # RDS memakai UTC
    return row


def db_list():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM equipment ORDER BY created_at DESC")
            return [_clean(r) for r in cur.fetchall()]
    finally:
        conn.close()


def db_get(item_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM equipment WHERE id = %s", (item_id,))
            return _clean(cur.fetchone())
    finally:
        conn.close()


def db_create(item):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO equipment (id, name, category, status, borrower) "
                "VALUES (%s, %s, %s, %s, %s)",
                (item["id"], item["name"], item["category"], item["status"], item["borrower"]),
            )
    finally:
        conn.close()
    return db_get(item["id"])


def db_update(item_id, changes):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            sets = ", ".join(f"{col} = %s" for col in changes)  # kolom dari whitelist FIELDS
            cur.execute(f"UPDATE equipment SET {sets} WHERE id = %s", (*changes.values(), item_id))
    finally:
        conn.close()
    return db_get(item_id)


def db_delete(item_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM equipment WHERE id = %s", (item_id,))
            return cur.rowcount > 0
    finally:
        conn.close()


# ---------- validasi ----------
def validate(data, partial):
    """Return (changes, error)."""
    changes = {}
    for field in FIELDS:
        if field in data:
            value = data[field]
            if not isinstance(value, str):
                return None, f"{field} must be a string"
            changes[field] = value.strip()
    if not partial and not changes.get("name"):
        return None, "name is required"
    if "name" in changes and not changes["name"]:
        return None, "name cannot be empty"
    if "status" in changes and changes["status"] not in VALID_STATUS:
        return None, "status must be 'available' or 'borrowed'"
    return changes, None


# ---------- endpoint ----------
@app.get("/health")
def health():
    try:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                cur.fetchone()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        return jsonify(status="error", db="unreachable", detail=type(exc).__name__), 503
    return jsonify(status="ok", service="equipment-api", db="connected")


# CREATE
@app.post("/equipment")
def create_equipment():
    data = request.get_json(silent=True) or {}
    changes, error = validate(data, partial=False)
    if error:
        return jsonify(error=error), 400
    item = {"id": str(uuid.uuid4()), "category": "", "status": "available", "borrower": ""}
    item.update(changes)
    return jsonify(db_create(item)), 201


# LIST (tambahan)
@app.get("/equipment")
def list_equipment():
    return jsonify(db_list())


# READ
@app.get("/equipment/<item_id>")
def get_equipment(item_id):
    item = db_get(item_id)
    if not item:
        return jsonify(error="not found"), 404
    return jsonify(item)


# UPDATE
@app.put("/equipment/<item_id>")
def update_equipment(item_id):
    if not db_get(item_id):
        return jsonify(error="not found"), 404
    data = request.get_json(silent=True) or {}
    changes, error = validate(data, partial=True)
    if error:
        return jsonify(error=error), 400
    if not changes:
        return jsonify(error="no valid fields to update"), 400
    return jsonify(db_update(item_id, changes))


# DELETE
@app.delete("/equipment/<item_id>")
def delete_equipment(item_id):
    if not db_delete(item_id):
        return jsonify(error="not found"), 404
    return jsonify(deleted=item_id)


# Buat tabel saat start. Jika DB belum siap, app tetap hidup dan /health menunjukkan error.
try:
    init_db()
except Exception as exc:  # noqa: BLE001
    app.logger.error("init_db gagal: %s", exc)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
