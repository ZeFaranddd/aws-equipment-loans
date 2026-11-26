# Deployment Plan: Equipment Loans API (Track A)

Lingkungan: AWS Academy Cloud Foundations Sandbox, region **us-east-1**.
Batasan Sandbox yang dipatuhi: EC2 t3.micro, EBS gp2 (maks 35 GB), RDS MySQL tanpa Multi-AZ dan tanpa Enhanced Monitoring, RDS db.t3.micro gp2.
Semua resource dihapus otomatis saat sesi berakhir, jadi seluruh langkah di bawah harus dikerjakan ulang tiap sesi baru.

## Status deployment

| Resource | Nama | Status |
| -------- | ---- | ------ |
| Security Group web | `web-sg` | [x] |
| Security Group database | `db-sg` | [x] |
| RDS MySQL | `equipment-db` | [x] |
| EC2 | `equipment-api-vm` | [x] |
| Service API | `equipment-api` (systemd) | [x] |
| Uji CRUD | `scripts/test-crud.sh` | [x] |

Sesi 26 Nov 2026 (resource sudah dihapus): Endpoint RDS `equipment-db.cj1hpuxmmna0.us-east-1.rds.amazonaws.com`  |  Public IP EC2 `100.58.104.92`
Versi terpasang: MySQL 8.4.13 (RDS), Amazon Linux 2023 dengan `python3` bawaan (cek: `python3 --version`).

## Langkah

1. **Start Lab** sampai status ready, buka Console, pastikan region **us-east-1**.
2. **Security Group `web-sg`** (default VPC): inbound SSH 22 dari My IP, Custom TCP 8000 dari 0.0.0.0/0.
3. **Security Group `db-sg`** (default VPC): inbound MySQL/Aurora 3306 dengan source = `web-sg`.
4. **RDS**: Standard create, MySQL 8.4.x (default), template Dev/Test, Single-AZ, identifier `equipment-db`, user `admin`, db.t3.micro, storage gp2 20 GB (autoscaling off), Public access **No**, security group `db-sg`, Enhanced monitoring off, initial database `equipmentdb`.
5. **EC2**: nama `equipment-api-vm`, Amazon Linux 2023, t3.micro, key pair `vockey`, security group `web-sg`, auto-assign public IP, root volume gp2 8 GB, IAM instance profile `LabInstanceProfile`.
6. Tunggu RDS **Available**, salin endpoint. Masuk ke EC2 (SSH `ec2-user` atau Session Manager lalu `sudo su - ec2-user`).
7. Di EC2 (repo harus public agar bisa di-clone):
   ```bash
   sudo dnf install -y git
   sudo mkdir -p /opt/equipment-api && sudo chown ec2-user:ec2-user /opt/equipment-api
   git clone https://github.com/ZeFaranddd/aws-equipment-loans.git /opt/equipment-api
   cd /opt/equipment-api
   DB_HOST=<endpoint-rds> DB_PASSWORD='<password>' bash deploy/ec2-setup.sh
   ```
8. Uji: `bash scripts/test-crud.sh | tee crud-test.txt`, dan dari laptop `http://<public-ip>:8000/health`.

## Uji konektivitas (bukti)

```bash
# port 3306 terbuka dari EC2 ke RDS
timeout 5 bash -c "</dev/tcp/<endpoint-rds>/3306" && echo "PORT 3306 OPEN"
# login dan query
mysql -h <endpoint-rds> -u admin -p -e "SELECT VERSION(); SHOW DATABASES;"
```

## Bukti AWS (`docs/evidence/`)

| File | Isi |
| ---- | --- |
| `01-sandbox-ready.png` | Lab status ready + Console us-east-1 |
| `02-security-groups.png`, `02b-security-group-web.png` | Inbound rules `db-sg` dan `web-sg` |
| `03-rds-available.png` | RDS Available, endpoint, Public access No |
| `04-ec2-running.png` | EC2 running, t3.micro, public IP, IAM role |
| `05b-db-connectivity.png` + `.txt` | Port check dan query `mysql` dari EC2 |
| `06-service-status.png` | `systemctl status equipment-api` active (running) |
| `07-crud-test.txt` | Output `scripts/test-crud.sh` |
| `08-health-browser.png` | `/health` dari browser laptop (`db: connected`) |
| `09-cli-proof.png` | (opsional) AWS CLI describe-instances dan describe-db-instances |

## Cleanup

Terminate EC2, delete RDS (tanpa final snapshot), lalu End Lab. Sandbox juga menghapus sisa resource saat timer 0:00.

## Troubleshooting

| Gejala | Penyebab umum | Solusi |
| ------ | ------------- | ------ |
| Nama Security Group ditolak | AWS menyimpan awalan `sg-` untuk ID, nama tidak boleh diawali `sg-` | Pakai `web-sg` dan `db-sg` (akhiran, bukan awalan) |
| EC2 langsung terminated | volume bukan gp2 / tipe instance tidak diizinkan | Luncurkan ulang dengan gp2 dan t3.micro |
| `ec2-setup.sh` gagal konek RDS | `db-sg` salah source, RDS belum Available, password salah | Cek rule 3306 dengan source `web-sg` |
| `/bin/bash^M: bad interpreter` | line ending CRLF | `sed -i 's/\r$//' deploy/*.sh scripts/*.sh` |
| `/health` 503 | DB tidak terjangkau | `sudo journalctl -u equipment-api -n 50` |
| Timeout dari laptop ke :8000 | rule 8000 di `web-sg` belum ada | Tambahkan inbound TCP 8000 |
