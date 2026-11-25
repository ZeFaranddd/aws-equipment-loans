# Deployment Plan — Equipment Loans (Track C: Serverless)

## 1. Prasyarat & Konfigurasi Dasar

- **Platform:** AWS Academy Learner Lab
- **Region:** `us-east-1` (N. Virginia)
- **IAM Execution Role:** `LabRole` (wajib menggunakan role bawaan lab, tidak membuat role baru)

## 2. Langkah Provisioning Infrastruktur

### A. DynamoDB Table

1. Buka layanan **DynamoDB** > **Create table**.
2. **Table name:** `equipment`
3. **Partition key:** `id` (String)
4. **Table settings:** Customize settings > Capacity mode **On-demand**.
5. Klik **Create table** dan tunggu hingga status berubah menjadi **Active**.

### B. AWS Lambda Function

1. Buka layanan **Lambda** > **Create function** (**Author from scratch**).
2. **Function name:** `equipment-crud`
3. **Runtime:** Python 3.12
4. **Execution role:** Use an existing role > pilih `LabRole`.
5. Salin kode dari `src/lambda_function.py` ke editor `lambda_function.py`, lalu klik **Deploy**.
6. Uji fungsi menggunakan _Test Event_ (`POST`) untuk memastikan kode `201` dan item masuk ke DynamoDB.

### C. API Gateway (HTTP API)

1. Buka layanan **API Gateway** > **Create API** > **HTTP API** (**Build**).
2. **Integrations:** Tambahkan integrasi Lambda mengarah ke `equipment-crud`.
3. **API name:** `equipment-api`
4. **Routes:** Daftarkan 5 route berikut ke integrasi `equipment-crud`:
   - `POST /equipment`
   - `GET /equipment`
   - `GET /equipment/{id}`
   - `PUT /equipment/{id}`
   - `DELETE /equipment/{id}`
5. **Stage:** Gunakan `$default` dengan _Auto-deploy_ aktif, lalu klik **Create**.
6. Salin **Invoke URL** untuk pengujian endpoint.

## 3. Verifikasi & Pengujian Endpoint

Jalankan perintah berikut di terminal (ganti `<INVOKE_URL>` dan `<ITEM_ID>`):

```bash
URL=<INVOKE_URL>

# 1. Create
curl -X POST $URL/equipment -H "Content-Type: application/json" \
  -d '{"name":"Kamera Sony","category":"Elektronik"}'

# 2. List All
curl $URL/equipment

# 3. Read by ID
curl $URL/equipment/<ITEM_ID>

# 4. Update
curl -X PUT $URL/equipment/<ITEM_ID> -H "Content-Type: application/json" \
  -d '{"name":"Kamera Sony","category":"Elektronik","status":"borrowed","borrower":"Budi"}'

# 5. Delete
curl -X DELETE $URL/equipment/<ITEM_ID>
```
