# Deployment Plan: Equipment Loans API (Track A)

Lingkungan: AWS Academy Cloud Foundations Sandbox, region **us-east-1**.
Batasan Sandbox yang dipatuhi: EC2 t3.micro, EBS gp2 (maks 35 GB), RDS MySQL tanpa Multi-AZ dan tanpa Enhanced Monitoring, RDS db.t3.micro gp2.
Semua resource dihapus otomatis saat sesi berakhir, jadi seluruh langkah di bawah harus dikerjakan ulang tiap sesi baru.

## Status deployment

| Resource | Nama | Status |
| -------- | ---- | ------ |
| Security Group web | `sg-web` | [ ] |
| Security Group database | `sg-db` | [ ] |
| RDS MySQL | `equipment-db` | [ ] |
| EC2 | `equipment-api-vm` | [ ] |
| Service API | `equipment-api` (systemd) | [ ] |
| Uji CRUD | `scripts/test-crud.sh` | [ ] |

Endpoint RDS: `__________`  |  Public IP EC2: `__________`  (isi per sesi)

## Langkah

1. **Start Lab** sampai status ready, buka Console, pastikan region **us-east-1**.
2. **Security Group `sg-web`** (default VPC): inbound SSH 22 dari My IP, Custom TCP 8000 dari 0.0.0.0/0.
3. **Security Group `sg-db`** (default VPC): inbound MySQL/Aurora 3306 dengan source = `sg-web`.
4. **RDS**: Standard create, MySQL 8.0.x, template Dev/Test, Single-AZ, identifier `equipment-db`, user `admin`, db.t3.micro, storage gp2 20 GB (autoscaling off), Public access **No**, security group `sg-db`, Enhanced monitoring off, initial database `equipmentdb`.
5. **EC2**: nama `equipment-api-vm`, Amazon Linux 2023, t3.micro, key pair `vockey`, security group `sg-web`, auto-assign public IP, root volume gp2 8 GB, IAM instance profile `LabInstanceProfile`.
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
| `02-security-groups.png` | Inbound rules `sg-web` dan `sg-db` |
| `03-rds-available.png` | RDS Available, endpoint, Public access No |
| `04-ec2-running.png` | EC2 running, t3.micro, public IP, IAM role |
| `05-db-connectivity.txt` | Output port check dan `mysql` dari EC2 |
| `06-service-status.png` | `systemctl status equipment-api` active (running) |
| `07-crud-test.txt` | Output `scripts/test-crud.sh` |
| `08-health-browser.png` | `/health` dari browser laptop (`db: connected`) |

## Cleanup

Terminate EC2, delete RDS (tanpa final snapshot), lalu End Lab. Sandbox juga menghapus sisa resource saat timer 0:00.

## Troubleshooting

| Gejala | Penyebab umum | Solusi |
| ------ | ------------- | ------ |
| EC2 langsung terminated | volume bukan gp2 / tipe instance tidak diizinkan | Luncurkan ulang dengan gp2 dan t3.micro |
| `ec2-setup.sh` gagal konek RDS | `sg-db` salah source, RDS belum Available, password salah | Cek rule 3306 dengan source `sg-web` |
| `/bin/bash^M: bad interpreter` | line ending CRLF | `sed -i 's/\r$//' deploy/*.sh scripts/*.sh` |
| `/health` 503 | DB tidak terjangkau | `sudo journalctl -u equipment-api -n 50` |
| Timeout dari laptop ke :8000 | rule 8000 di `sg-web` belum ada | Tambahkan inbound TCP 8000 |
