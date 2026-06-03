# migrate_last_login.py
import sqlite3
import os

DB_PATH = os.path.join("instance", "eos_compare.db")

def add_last_login_column():
    if not os.path.exists(DB_PATH):
        print(f"❌ Base introuvable : {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "last_login" in columns:
        print("✅ La colonne last_login existe déjà.")
        conn.close()
        return True
    
    cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
    conn.commit()
    conn.close()
    
    print("✅ Colonne last_login ajoutée avec succès !")
    return True

if __name__ == "__main__":
    add_last_login_column()