# Deployment Plan: Equipment Loans API (Track B, EC2 + Docker + ECR)

Dokumen ini menjelaskan cara membangun ulang seluruh infrastruktur proyek di AWS Learner Lab.

## 1. Ringkasan

| Item     | Nilai                                                                            |
| -------- | -------------------------------------------------------------------------------- |
| Use case | Equipment Loans (peminjaman peralatan)                                           |
| Track    | B: EC2 + Docker + ECR                                                            |
| Region   | us-east-1 (N. Virginia)                                                          |
| Akun     | AWS Learner Lab                                                                  |
| IAM      | `LabInstanceProfile` (berisi `LabRole`) dipasang di EC2, tidak membuat role baru |
| Diagram  | `docs/architecture.drawio`                                                       |

## 2. Daftar Resource

| Resource        | Nama                         | Konfigurasi                                                                         |
| --------------- | ---------------------------- | ----------------------------------------------------------------------------------- |
| ECR repository  | `equipment-api`              | Private                                                                             |
| Security Group  | `sg-docker`                  | Inbound: SSH 22 dari My IP, TCP 8000 dari Anywhere (3306 tidak dibuka)              |
| EC2 instance    | `equipment-docker`           | t3.micro, Amazon Linux 2023, 8 GB, public IP, instance profile `LabInstanceProfile` |
| Key pair        | `lab-key`                    | RSA, `.pem` (jangan di-commit)                                                      |
| Container `api` | image `equipment-api:latest` | Flask + gunicorn, port 8000 (dibuild dan dijalankan)                                |
| Container `db`  | image `mysql:8`              | Direncanakan di `docker-compose.yml`                                                |

## 3. Langkah Deployment

### 3.1 Mulai Learner Lab

1. Buka Learner Lab, klik **Start Lab**, tunggu indikator hijau.
2. Klik **AWS** untuk membuka Console, pastikan region **us-east-1**.
3. Catat sisa budget awal.

### 3.2 Buat repository ECR

1. Console, ECR, **Create repository**.
2. Visibility **Private**, name `equipment-api`, **Create**.

### 3.3 Buat Security Group

1. EC2, Security Groups, **Create security group**, name `sg-docker`, VPC default.
2. Inbound rules: SSH (22) source **My IP**; Custom TCP 8000 source **Anywhere-IPv4**.

### 3.4 Luncurkan EC2

1. EC2, **Launch instance**, name `equipment-docker`.
2. AMI **Amazon Linux 2023**, instance type **t3.micro**.
3. Key pair: buat `lab-key` (RSA, `.pem`).
4. Network settings: VPC default, Auto-assign public IP **Enable**, security group `sg-docker`.
5. Advanced details, **IAM instance profile: `LabInstanceProfile`**.
6. Launch, tunggu status checks 2/2 passed.

### 3.5 SSH dan install Docker

```bash
chmod 400 lab-key.pem
ssh -i lab-key.pem ec2-user@<PUBLIC_IP_EC2>
```

Di dalam EC2:

```bash
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
exit
```

SSH lagi (agar grup berlaku), lalu uji:

```bash
docker --version
docker run hello-world
```

### 3.6 Ambil kode

Pilih salah satu:

```bash
# repo public
git clone https://github.com/ZeFaranddd/aws-equipment-loans.git
cd aws-equipment-loans/src
```

```bash
# atau salin dari laptop (jalankan di laptop, dari folder repo)
scp -i lab-key.pem -r src ec2-user@<PUBLIC_IP_EC2>:~/src
# lalu di EC2: cd ~/src
```

### 3.6b Build image

```bash
docker build -t equipment-api .
docker images
```

### 3.7 Push image ke ECR

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
REPO=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/equipment-api

aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
docker tag equipment-api:latest $REPO:latest
docker push $REPO:latest
```

Verifikasi: ECR, repository `equipment-api`, image tag `latest` muncul.

### 3.8 Jalankan dari image dan uji

```bash
docker run -d -p 8000:8000 --name api $REPO:latest
curl http://localhost:8000/health
```

Dari laptop (ganti `IP`):

```bash
IP=<PUBLIC_IP_EC2>
curl http://$IP:8000/health

curl -X POST http://$IP:8000/equipment -H "Content-Type: application/json" \
  -d '{"name":"Kamera Sony","category":"Elektronik"}'
curl http://$IP:8000/equipment
curl http://$IP:8000/equipment/<id>
curl -X PUT http://$IP:8000/equipment/<id> -H "Content-Type: application/json" \
  -d '{"status":"borrowed","borrower":"Budi"}'
curl -X DELETE http://$IP:8000/equipment/<id>
```

Simpan output ke `docs/evidence/api-test-output.txt`.

## 4. Bukti yang Dikumpulkan

Disimpan di `docs/evidence/`:

| File                        | Isi                                                |
| --------------------------- | -------------------------------------------------- |
| `01-learner-lab-green.png`  | Lab berjalan, budget, region                       |
| `02-ecr-repository.png`     | Repository `equipment-api` dan image tag `latest`  |
| `03-ec2-running.png`        | Instance Running, security group, instance profile |
| `04-docker-hello-world.png` | Output `docker run hello-world`                    |
| `05-docker-push.png`        | Output `docker push` sukses                        |
| `06-api-test.png`           | Output `/health` dan CRUD                          |
| `api-test-output.txt`       | Teks output uji                                    |

## 5. Status Deployment

Perbarui setelah tiap langkah selesai.

| Langkah                         | Status | Tanggal |
| ------------------------------- | ------ | ------- |
| Learner Lab dimulai             | [ ]    |         |
| Repository ECR dibuat           | [ ]    |         |
| Security Group dibuat           | [ ]    |         |
| EC2 berjalan                    | [ ]    |         |
| Docker terpasang dan diuji      | [ ]    |         |
| Image dibuild                   | [ ]    |         |
| Image di-push ke ECR            | [ ]    |         |
| Container diuji (health + CRUD) | [ ]    |         |
| Screenshot bukti disimpan       | [ ]    |         |
| Cleanup selesai                 | [ ]    |         |

IP publik EC2 (isi saat deploy): `-`

## 6. Pengelolaan Budget

- Satu-satunya resource berbiaya per jam adalah EC2 t3.micro. Tidak memakai RDS, NAT Gateway, atau Load Balancer.
- Cek budget di awal dan akhir sesi. Klik **End Lab** setelah selesai.
- Kerjakan seluruh langkah 3.2 sampai 3.8 dan semua screenshot dalam satu sesi.

## 7. Cleanup

1. Terminate EC2 `equipment-docker`.
2. (Opsional) hapus repository ECR `equipment-api`.
3. (Opsional) hapus Security Group `sg-docker` dan key pair `lab-key`.
4. Catat budget akhir, klik **End Lab**.

## 8. Troubleshooting

| Masalah                          | Penanganan                                                                     |
| -------------------------------- | ------------------------------------------------------------------------------ |
| SSH timeout                      | Cek SG port 22 dari My IP (IP berubah bila ganti jaringan) dan public IP aktif |
| `Permission denied (publickey)`  | Pakai user `ec2-user`, key yang benar, `chmod 400`                             |
| `docker: permission denied`      | Logout lalu SSH ulang setelah `usermod -aG docker`                             |
| ECR login gagal / `AccessDenied` | Pastikan EC2 memakai `LabInstanceProfile` (Actions, Security, Modify IAM role) |
| `curl` ke IP:8000 timeout        | Cek SG inbound 8000 dan container jalan (`docker ps`)                          |
