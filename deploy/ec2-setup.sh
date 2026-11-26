#!/usr/bin/env bash
# Setup aplikasi di EC2 (Amazon Linux 2023). Jalankan sebagai ec2-user:
#   DB_HOST=<endpoint-rds> DB_PASSWORD='<password>' bash deploy/ec2-setup.sh
# Aman dijalankan ulang (idempotent).
set -euo pipefail

: "${DB_HOST:?isi DB_HOST dengan endpoint RDS}"
: "${DB_PASSWORD:?isi DB_PASSWORD}"
DB_USER="${DB_USER:-admin}"
DB_NAME="${DB_NAME:-equipmentdb}"
REPO_URL="${REPO_URL:-https://github.com/ZeFaranddd/aws-equipment-loans.git}"
APP_DIR=/opt/equipment-api

echo "[1/6] Install paket (git, python3-pip, klien MySQL)"
sudo dnf install -y git python3-pip mariadb105

echo "[2/6] Ambil kode dari GitHub"
sudo mkdir -p "$APP_DIR"
sudo chown ec2-user:ec2-user "$APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$APP_DIR"
fi

echo "[3/6] Virtualenv dan dependency"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --quiet -r "$APP_DIR/src/requirements.txt"

echo "[4/6] Uji koneksi ke RDS, buat database dan tabel"
export MYSQL_PWD="$DB_PASSWORD"
if ! mysql -h "$DB_HOST" -u "$DB_USER" -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`; SELECT VERSION() AS mysql_version;"; then
  echo "GAGAL konek ke RDS. Cek: status RDS Available, db-sg mengizinkan 3306 dari web-sg, password benar." >&2
  exit 1
fi
mysql -h "$DB_HOST" -u "$DB_USER" "$DB_NAME" < "$APP_DIR/src/schema.sql"
mysql -h "$DB_HOST" -u "$DB_USER" "$DB_NAME" -e "SHOW TABLES;"
unset MYSQL_PWD

echo "[5/6] Tulis konfigurasi ke /etc/equipment-api.env (chmod 600)"
sudo tee /etc/equipment-api.env >/dev/null <<ENVFILE
DB_HOST=$DB_HOST
DB_PORT=3306
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME
ENVFILE
sudo chmod 600 /etc/equipment-api.env

echo "[6/6] Pasang dan jalankan service systemd"
sudo cp "$APP_DIR/deploy/equipment-api.service" /etc/systemd/system/equipment-api.service
sudo systemctl daemon-reload
sudo systemctl enable equipment-api
sudo systemctl restart equipment-api
sleep 3
sudo systemctl --no-pager status equipment-api | head -n 12 || true
echo "--- /health ---"
curl -s http://localhost:8000/health || true
echo
