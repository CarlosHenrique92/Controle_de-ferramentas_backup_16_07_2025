import sqlite3

# Conectando ao banco de dados
conn = sqlite3.connect('ferramentas.db')
cursor = conn.cursor()

# Verifica se a coluna já existe para evitar erro
cursor.execute("PRAGMA table_info(ferramentas)")
colunas = [coluna[1] for coluna in cursor.fetchall()]

if 'perfuratriz' not in colunas:
    cursor.execute('ALTER TABLE ferramentas ADD COLUMN perfuratriz TEXT')
    print("✅ Coluna 'perfuratriz' adicionada com sucesso!")
else:
    print("ℹ️ A coluna 'perfuratriz' já existe. Nenhuma alteração feita.")

# Finaliza
conn.commit()
conn.close()
