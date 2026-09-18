import sqlite3
import pandas as pd
from datetime import date

DB_NAME = "habits.db"

def ottieni_connessione():
    """Crea e restituisce una connessione attiva al database delle abitudini."""
    conn = sqlite3.connect(DB_NAME)
    # Abilita le foreign key (fondamentale per SQLite)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS abitudini (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descrizione TEXT,
            importanza INTEGER DEFAULT 3,
            data_creazione TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_giornaliero (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            abitudine_id INTEGER,
            data TEXT,
            completato INTEGER,
            FOREIGN KEY (abitudine_id) REFERENCES abitudini (id) ON DELETE CASCADE,
            UNIQUE(abitudine_id, data)
        )
    """)
    conn.commit()
    
    return conn

def aggiungi_abitudine(nome, descrizione="",importanza=3):
    """Inserisce una nuova abitudine nel database."""
    conn = ottieni_connessione()
    cursor = conn.cursor()
    oggi = date.today().strftime("%Y-%m-%d")
    
    cursor.execute("""
        INSERT INTO abitudini (nome, descrizione, importanza,data_creazione)
        VALUES (?, ?, ?,?)
    """, (nome, descrizione,importanza, oggi))
    
    conn.commit()
    conn.close()

def get_tutte_abitudini():
    """Restituisce un DataFrame Pandas con l'elenco di tutte le abitudini."""
    conn = ottieni_connessione()
    df = pd.read_sql_query("SELECT * FROM abitudini", conn)
    conn.close()
    return df

def registra_log(abitudine_id, data_str, completato):
    """Inserisce o aggiorna lo stato di completamento di un'abitudine per una data specifica."""
    conn = ottieni_connessione()
    cursor = conn.cursor()
    
    # INSERT OR REPLACE sfrutta il vincolo UNIQUE per aggiornare lo stato se il log esiste già
    cursor.execute("""
        INSERT OR REPLACE INTO log_giornaliero (abitudine_id, data, completato)
        VALUES (?, ?, ?)
    """, (abitudine_id, data_str, completato))
    
    conn.commit()
    conn.close()

def get_log_abitudini():
    """Restituisce lo storico unito alle abitudini, includendo il grado di importanza."""
    conn = ottieni_connessione()
    query = """
        SELECT l.id, l.abitudine_id, a.nome as nome_abitudine, a.importanza, l.data, l.completato
        FROM log_giornaliero l
        JOIN abitudini a ON l.abitudine_id = a.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
