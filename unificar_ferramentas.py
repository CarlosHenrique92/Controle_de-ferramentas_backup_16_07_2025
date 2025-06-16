import sqlite3

def unificar_ferramentas():
    conn = sqlite3.connect('ferramentas.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Pega todos os nomes + status únicos
    cursor.execute('SELECT nome, status FROM ferramentas GROUP BY nome, status')
    combinacoes = cursor.fetchall()

    for c in combinacoes:
        nome = c['nome']
        status = c['status']

        # Busca todas as ferramentas com esse nome e status
        cursor.execute('SELECT * FROM ferramentas WHERE nome = ? AND status = ?', (nome, status))
        duplicatas = cursor.fetchall()

        if len(duplicatas) > 1:
            quantidade_total = sum(f['quantidade'] for f in duplicatas)

            # Apaga todas as duplicatas
            cursor.execute('DELETE FROM ferramentas WHERE nome = ? AND status = ?', (nome, status))

            # Insere uma única linha com a soma
            cursor.execute('INSERT INTO ferramentas (nome, status, local, tecnico, quantidade, idgeo) VALUES (?, ?, ?, ?, ?, ?)',
                (nome, status, '', '', quantidade_total, '')
            )

    conn.commit()
    conn.close()
    print("Ferramentas unificadas com sucesso.")

if __name__ == '__main__':
    unificar_ferramentas()
