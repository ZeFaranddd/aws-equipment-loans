FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000

# 1 worker: data sementara disimpan di memori proses
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "app:app"]
