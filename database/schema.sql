-- ================================================
-- EOS Compare — Schéma de base de données MySQL
-- ================================================

CREATE DATABASE IF NOT EXISTS eos_compare CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE eos_compare;

-- ── Table des utilisateurs ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    username            VARCHAR(80)  NOT NULL UNIQUE,
    email               VARCHAR(120) NOT NULL UNIQUE,
    password            VARCHAR(200) NOT NULL,
    role                ENUM('student', 'teacher', 'admin') DEFAULT 'student',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Vérification email
    is_verified         TINYINT(1) NOT NULL DEFAULT 0,
    verification_token  VARCHAR(100) NULL,
    verification_expiry DATETIME NULL,

    -- Réinitialisation mot de passe
    reset_token         VARCHAR(100) NULL,
    reset_expiry        DATETIME NULL
);

-- ── Script de migration (si la table users existe déjà) ─────────────────────
-- ALTER TABLE users ADD COLUMN is_verified TINYINT(1) NOT NULL DEFAULT 0;
-- ALTER TABLE users ADD COLUMN verification_token VARCHAR(100) NULL;
-- ALTER TABLE users ADD COLUMN verification_expiry DATETIME NULL;
-- ALTER TABLE users ADD COLUMN reset_token VARCHAR(100) NULL;
-- ALTER TABLE users ADD COLUMN reset_expiry DATETIME NULL;

-- ── Table des molécules (gaz personnalisés) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS molecules (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    formula  VARCHAR(50),
    tc       FLOAT COMMENT 'Température critique (K)',
    pc       FLOAT COMMENT 'Pression critique (bar)',
    omega    FLOAT COMMENT 'Facteur acentrique',
    a_vdw    FLOAT COMMENT 'Constante a Van der Waals (Pa.m6/mol2)',
    b_vdw    FLOAT COMMENT 'Constante b Van der Waals (m3/mol)',
    user_id  INT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ── Table de l'historique des calculs ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS calculations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT,
    gas_name        VARCHAR(50),
    temperature     FLOAT COMMENT 'Température en K',
    pressure        FLOAT COMMENT 'Pression en Pa',
    equations_used  VARCHAR(200),
    result_json     TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ── Index pour performance ──────────────────────────────────────────────────
CREATE INDEX idx_calc_user    ON calculations(user_id);
CREATE INDEX idx_calc_date    ON calculations(created_at);
CREATE INDEX idx_mol_formula  ON molecules(formula);
