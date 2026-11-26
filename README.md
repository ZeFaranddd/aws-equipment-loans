# Equipment Loans on AWS

Project individu Cloud Computing (AWS), Week 12: Design & AWS Setup.

## Use case

Sistem peminjaman peralatan (Equipment Loans): mencatat peralatan dan status peminjamannya.

## Track

**Track B: Containers (EC2 + Docker + ECR)**

Catatan: rencana awal Track C (Serverless), dialihkan ke Track B karena pembuatan tabel DynamoDB (`dynamodb:CreateTable`) ditolak oleh kebijakan IAM akun AWS Learner Lab.

## Arsitektur

![Architecture](docs/architecture.png)

File sumber diagram: `docs/architecture.drawio`. Design brief: `docs/design-brief.pdf`.

| Service | Image | Port | Status Week 12 |
| ------- | ----- | ---- | -------------- |
| api | `equipment-api` (dibuild dari `src/Dockerfile`) | 8000 | Dibuild, di-push ke ECR, diuji |
| db | `mysql:8` | 3306 (internal) | Direncanakan di `docker-compose.yml` |

## Entitas

`Equipment`: `id`, `name`, `category`, `status` (available/borrowed), `borrower`, `created_at`.

## Endpoint

| Method | Path            | Deskripsi            |
| ------ | --------------- | -------------------- |
| POST   | /equipment      | Create               |
| GET    | /equipment/{id} | Read                 |
| PUT    | /equipment/{id} | Update               |
| DELETE | /equipment/{id} | Delete               |
| GET    | /equipment      | List (tambahan)      |
| GET    | /health         | Cek status (tambahan)|

## Menjalankan secara lokal (opsional)

```bash
cd src
docker build -t equipment-api .
docker run -d -p 8000:8000 --name api equipment-api
curl http://localhost:8000/health
```

## Cara deploy ke AWS

Lihat [deploy/DEPLOYMENT.md](deploy/DEPLOYMENT.md).

## Struktur repo

```
README.md
docker-compose.yml        # rencana dua service (api + db)
src/                      # app.py, requirements.txt, Dockerfile
deploy/DEPLOYMENT.md      # rencana dan langkah deployment
docs/                     # diagram, design brief, bukti AWS
docs/evidence/            # screenshot dan output uji
```

## Bukti AWS

Lihat folder `docs/evidence/`.
