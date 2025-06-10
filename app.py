from flask import Flask, render_template, request, redirect
import sqlite3

# Cria o app Flask
app = Flask(__name__)

# Função para conectar ao banco
def get_db_connection():
    conn = sqlite3.connect('ferramentas.db')
    conn.row_factory = sqlite3.Row  # permite acessar as colunas como dicionários
    return conn

# Página principal
@app.route('/')
def index():
    conn = get_db_connection()

    # Ferramentas em estoque
    ferramentas_estoque = conn.execute('SELECT * FROM ferramentas WHERE status = "em estoque"').fetchall()

    # Ferramentas em uso
    ferramentas_uso = conn.execute('SELECT * FROM ferramentas WHERE status = "em uso"').fetchall()

    # Contagem total
    total = conn.execute('SELECT COUNT(*) FROM ferramentas').fetchone()[0]
    em_uso = len(ferramentas_uso)
    em_estoque = len(ferramentas_estoque)

    conn.close()

    return render_template('index.html',
                           ferramentas_estoque=ferramentas_estoque,
                           ferramentas_uso=ferramentas_uso,
                           total=total,
                           em_uso=em_uso,
                           em_estoque=em_estoque)

# Rota para adicionar uma nova ferramenta
@app.route('/adicionar', methods=['POST'])
def adicionar():
    nome = request.form['nome']
    status = request.form['status']
    local = request.form['local']
    tecnico = request.form['tecnico']
    quantidade = int(request.form['quantidade'])

    conn = get_db_connection()

    # Verifica se já existe ferramenta igual (mesmo nome, status, local e técnico)
    ferramenta_existente = conn.execute('''
        SELECT * FROM ferramentas
        WHERE nome = ? AND status = ? AND local = ? AND tecnico = ?
    ''', (nome, status, local, tecnico)).fetchone()

    if ferramenta_existente:
        # Se existe, soma a quantidade
        nova_quantidade = ferramenta_existente['quantidade'] + quantidade
        conn.execute('''
            UPDATE ferramentas
            SET quantidade = ?
            WHERE id = ?
        ''', (nova_quantidade, ferramenta_existente['id']))
    else:
        # Caso contrário, insere nova linha
        conn.execute('''
            INSERT INTO ferramentas (nome, status, local, tecnico, quantidade)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, status, local, tecnico, quantidade))

    conn.commit()
    conn.close()
    return redirect('/')


@app.route('/devolver/<int:id>')
def devolver(id):
    conn = get_db_connection()

    # Pega os dados da ferramenta original
    ferramenta = conn.execute('SELECT * FROM ferramentas WHERE id = ?', (id,)).fetchone()
    nome = ferramenta['nome']
    quantidade = ferramenta['quantidade']

    # Verifica se já existe essa ferramenta em estoque
    existente_estoque = conn.execute('''
        SELECT * FROM ferramentas
        WHERE nome = ? AND status = "em estoque"
    ''', (nome,)).fetchone()

    if existente_estoque:
        # Soma quantidade ao item em estoque existente
        nova_quantidade = existente_estoque['quantidade'] + quantidade
        conn.execute('''
            UPDATE ferramentas
            SET quantidade = ?
            WHERE id = ?
        ''', (nova_quantidade, existente_estoque['id']))

        # Deleta a ferramenta que foi devolvida
        conn.execute('DELETE FROM ferramentas WHERE id = ?', (id,))
    else:
        # Apenas atualiza a devolvida para virar estoque
        conn.execute('''
            UPDATE ferramentas
            SET status = ?, local = ?, tecnico = ?
            WHERE id = ?
        ''', ('em estoque', 'estoque', '', id))

    conn.commit()
    conn.close()
    return redirect('/')




# Inicia o servidor
if __name__ == '__main__':
    print("Iniciando o servidor Flask...")
    app.run(debug=True)
