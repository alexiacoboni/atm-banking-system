-- Creare baza de date și utilizare
CREATE DATABASE IF NOT EXISTS banca;
USE banca;

-- Ștergere dacă există
DROP TABLE IF EXISTS tranzactii;
DROP TABLE IF EXISTS conturi;

-- Creare tabel conturi
CREATE TABLE conturi (
    id_cont INT AUTO_INCREMENT PRIMARY KEY,
    nume VARCHAR(255) NOT NULL UNIQUE,  -- devenim capabili să îl referim în FK
    parola VARCHAR(255) NOT NULL,
    tip ENUM('curent', 'deposit') NOT NULL,
    sold DECIMAL(10, 2) DEFAULT 0,
    rol ENUM('client', 'admin') NOT NULL DEFAULT 'client',
    perioada VARCHAR(20),
    data_start DATE
);

-- Inserare date de test
INSERT INTO conturi (nume, parola, tip, sold, rol)
VALUES
('ana', '1234', 'curent', 500.00, 'admin'),
('ionel', '12942', 'deposit', 2000.00, 'client');

-- Creare tabel tranzactii (legat prin 'nume')
CREATE TABLE tranzactii (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    tip ENUM('depunere', 'retragere', 'transfer') NOT NULL,
    suma DECIMAL(10,2) NOT NULL CHECK (suma >= 0),
    data DATETIME DEFAULT CURRENT_TIMESTAMP,
    cont_destinatar VARCHAR(255),
    FOREIGN KEY (username) REFERENCES conturi(nume)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Inserare tranzacții de test
INSERT INTO tranzactii (username, tip, suma, cont_destinatar)
VALUES
  ('ana', 'depunere', 500.00, NULL),
  ('ana', 'retragere', 100.00, NULL),
  ('ana', 'transfer', 200.00, 'ionel'),
  ('ionel', 'depunere', 300.00, NULL),
  ('ionel', 'transfer', 150.00, 'ana'),
  ('ionel', 'retragere', 50.00, NULL);

-- Interogări utile
SELECT * FROM conturi;
SELECT * FROM tranzactii;
SELECT * FROM conturi WHERE nume = 'ionel' AND parola = '12942';
ALTER TABLE tranzactii
MODIFY COLUMN data DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP;
SELECT * FROM tranzactii ORDER BY id DESC LIMIT 5;
SHOW COLUMNS FROM tranzactii;
SET time_zone = '+03:00'; -- pentru România (vară)

ALTER TABLE conturi
MODIFY tip ENUM('curent', 'depozit') NOT NULL;

USE banca;
SELECT DISTINCT tip FROM conturi;

UPDATE conturi
SET tip = 'depozit'
WHERE tip = 'deposit';

SET SQL_SAFE_UPDATES = 0;

UPDATE conturi SET tip = 'depozit' WHERE tip = 'deposit';

SELECT * FROM conturi;