import sqlite3

conn = sqlite3.connect('ferramentas.db')

conn.execute('''
    CREATE TABLE IF NOT EXISTS ferramentas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        status TEXT NOT NULL,
        local TEXT NOT NULL,
        tecnico TEXT,
        quantidade INTEGER NOT NULL
    )
''')

conn.commit()
conn.close()
