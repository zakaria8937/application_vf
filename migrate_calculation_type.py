# migrate_calculation_type.py
import sqlite3
import os

DB_PATH = os.path.join("instance", "eos_compare.db")

def add_calculation_type_column():
    if not os.path.exists(DB_PATH):
        print(f"❌ Base introuvable : {DB_PATH}")
        print("   Lancez d'abord l'application pour créer la base.")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(calculations)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "calculation_type" in columns:
        print("✅ La colonne calculation_type existe déjà.")
        conn.close()
        return True
    
    # Ajouter la colonne
    cursor.execute("ALTER TABLE calculations ADD COLUMN calculation_type TEXT DEFAULT 'eos_explorer'")
    conn.commit()
    conn.close()
    
    print("✅ Colonne calculation_type ajoutée avec succès !")
    return True

if __name__ == "__main__":
    add_calculation_type_column()