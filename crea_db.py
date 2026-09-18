import sqlite3

DB_NAME = "habits.db"

def inizializza_db():
    """Crea il database SQLite e le tabelle necessarie per l'Habit Tracker."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Tabella delle Abitudini
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS abitudini (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descrizione TEXT,
            importanza INTEGER DEFAULT 3,
            data_creazione TEXT NOT NULL
        )
    """)
    
    # 2. Tabella dei Log Giornalieri (traccia il completamento giorno per giorno)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_giornaliero (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            abitudine_id INTEGER,
            data TEXT NOT NULL,
            completato INTEGER DEFAULT 0,
            FOREIGN KEY (abitudine_id) REFERENCES abitudini (id) ON DELETE CASCADE,
            UNIQUE(abitudine_id, data)
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database 'habits.db' e tabelle create con successo!")

if __name__ == "__main__":
    inizializza_db()