"""
Script de migration : ajoute les nouvelles colonnes à la base SQLite existante.
Exécuter UNE SEULE FOIS : python migrate_db.py
"""
import sqlite3
import os

DB_PATH = os.path.join("instance", "eos_compare.db")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"[Migration] Base introuvable : {DB_PATH}")
        print("Lancez d'abord l'application pour créer la base (db.create_all).")
        return

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # Récupérer les colonnes existantes
    cur.execute("PRAGMA table_info(users)")
    existing = {row[1] for row in cur.fetchall()}

    added = []

    if "is_verified" not in existing:
        cur.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0")
        added.append("is_verified")

    if "verification_token" not in existing:
        cur.execute("ALTER TABLE users ADD COLUMN verification_token TEXT")
        added.append("verification_token")

    if "verification_expiry" not in existing:
        cur.execute("ALTER TABLE users ADD COLUMN verification_expiry TEXT")
        added.append("verification_expiry")

    if "reset_token" not in existing:
        cur.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
        added.append("reset_token")

    if "reset_expiry" not in existing:
        cur.execute("ALTER TABLE users ADD COLUMN reset_expiry TEXT")
        added.append("reset_expiry")

    conn.commit()
    conn.close()

    if added:
        print(f"[Migration] Colonnes ajoutées : {', '.join(added)}")
    else:
        print("[Migration] Aucune colonne à ajouter (déjà à jour).")

if __name__ == "__main__":
    migrate()
