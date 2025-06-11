import sqlite3

conn = sqlite3.connect('ferramentas.db')
cursor = conn.cursor()

# Corrige os status inconsistentes
cursor.execute("UPDATE ferramentas SET status = 'em uso' WHERE LOWER(status) = 'uso'")
cursor.execute("UPDATE ferramentas SET status = 'em estoque' WHERE LOWER(status) = 'estoque'")

conn.commit()
conn.close()

print("Status corrigidos com sucesso!")
