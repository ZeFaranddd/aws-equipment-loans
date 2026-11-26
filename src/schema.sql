-- Skema database equipmentdb (dibuat otomatis oleh app.py; file ini sebagai dokumentasi
-- dan dijalankan oleh deploy/ec2-setup.sh).
CREATE TABLE IF NOT EXISTS equipment (
    id         CHAR(36)     NOT NULL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    category   VARCHAR(50)  NOT NULL DEFAULT '',
    status     VARCHAR(20)  NOT NULL DEFAULT 'available',
    borrower   VARCHAR(100) NOT NULL DEFAULT '',
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
