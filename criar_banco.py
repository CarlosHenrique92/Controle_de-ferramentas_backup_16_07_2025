import sqlite3

conn = sqlite3.connect('ferramentas.db')
conn.execute('''
CREATE TABLE IF NOT EXISTS ferramentas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    status TEXT NOT NULL,
    local TEXT NOT NULL,
    tecnico TEXT,
    quantidade INTEGER NOT NULL,
    idgeo TEXT
)
''')
conn.commit()
conn.close()
print("Banco de dados e tabela criados com sucesso.")

