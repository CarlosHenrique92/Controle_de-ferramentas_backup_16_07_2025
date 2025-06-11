import sqlite3

conn = sqlite3.connect('ferramentas.db')
cursor = conn.cursor()

cursor.execute("SELECT nome, quantidade, status FROM ferramentas")
ferramentas = cursor.fetchall()

for ferramenta in ferramentas:
    print(ferramenta)

conn.close()
