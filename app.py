from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import openpyxl

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('ferramentas.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        ferramentas_estoque = conn.execute('SELECT * FROM ferramentas WHERE status = "estoque"').fetchall()
        ferramentas_uso = conn.execute('SELECT * FROM ferramentas WHERE status = "uso"').fetchall()
        conn.close()
        return render_template('index.html', ferramentas_estoque=ferramentas_estoque, ferramentas_uso=ferramentas_uso)
    except sqlite3.OperationalError as e:
        erro = str(e)
        return render_template('index.html', ferramentas_estoque=[], ferramentas_uso=[], erro=erro)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    nome = request.form['nome']
    status = request.form['status']
    local = request.form['local']
    tecnico = request.form['tecnico']
    quantidade = int(request.form['quantidade'])
    idgeo = request.form['idgeo']

    conn = get_db_connection()

    existente = conn.execute('SELECT * FROM ferramentas WHERE nome = ? AND status = ?', (nome, status)).fetchone()

    if existente:
        nova_qtd = existente['quantidade'] + quantidade
        conn.execute('UPDATE ferramentas SET quantidade = ? WHERE id = ?', (nova_qtd, existente['id']))
    else:
        conn.execute(
            'INSERT INTO ferramentas (nome, status, local, tecnico, quantidade, idgeo) VALUES (?, ?, ?, ?, ?, ?)',
            (nome, status, local, tecnico, quantidade, idgeo)
        )

    if status == 'uso':
        ferramenta_estoque = conn.execute('SELECT * FROM ferramentas WHERE nome = ? AND status = "estoque"', (nome,)).fetchone()
        if ferramenta_estoque:
            nova_qtd_estoque = ferramenta_estoque['quantidade'] - quantidade
            if nova_qtd_estoque <= 0:
                conn.execute('DELETE FROM ferramentas WHERE id = ?', (ferramenta_estoque['id'],))
            else:
                conn.execute('UPDATE ferramentas SET quantidade = ? WHERE id = ?', (nova_qtd_estoque, ferramenta_estoque['id']))

    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    ferramenta = conn.execute('SELECT * FROM ferramentas WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        nome = request.form['nome']
        status = request.form['status']
        local = request.form['local']
        tecnico = request.form['tecnico']
        quantidade = int(request.form['quantidade'])
        idgeo = request.form['idgeo']

        conn.execute(
            'UPDATE ferramentas SET nome = ?, status = ?, local = ?, tecnico = ?, quantidade = ?, idgeo = ? WHERE id = ?',
            (nome, status, local, tecnico, quantidade, idgeo, id)
        )
        conn.commit()
        conn.close()
        return redirect('/')

    conn.close()
    return render_template('editar.html', ferramenta=ferramenta)

@app.route('/deletar/<int:id>')
def deletar(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM ferramentas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/devolver/<int:id>')
def devolver(id):
    conn = get_db_connection()
    ferramenta = conn.execute('SELECT * FROM ferramentas WHERE id = ?', (id,)).fetchone()

    if ferramenta:
        existente = conn.execute('SELECT * FROM ferramentas WHERE nome = ? AND status = "estoque"', (ferramenta['nome'],)).fetchone()
        if existente:
            nova_qtd = existente['quantidade'] + ferramenta['quantidade']
            conn.execute('UPDATE ferramentas SET quantidade = ? WHERE id = ?', (nova_qtd, existente['id']))
            conn.execute('DELETE FROM ferramentas WHERE id = ?', (ferramenta['id'],))
        else:
            conn.execute('UPDATE ferramentas SET status = "estoque", local = "", tecnico = "", idgeo = "" WHERE id = ?', (ferramenta['id'],))

    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/relatorios', methods=['GET'])
def relatorios():
    conn = get_db_connection()

    ferramenta = request.args.get('ferramenta', '').lower()
    tecnico = request.args.get('tecnico', '').lower()
    projeto = request.args.get('projeto', '').lower()

    query = """
        SELECT nome, quantidade, status, local, tecnico, idgeo
        FROM ferramentas
        WHERE status = 'uso'
    """
    params = []

    if ferramenta:
        query += " AND LOWER(nome) LIKE ?"
        params.append(f"%{ferramenta}%")
    if tecnico:
        query += " AND LOWER(tecnico) LIKE ?"
        params.append(f"%{tecnico}%")
    if projeto:
        query += " AND LOWER(local) LIKE ?"
        params.append(f"%{projeto}%")

    ferramentas = conn.execute(query, params).fetchall()

    nomes_ferramentas = [row['nome'] for row in conn.execute("SELECT DISTINCT nome FROM ferramentas WHERE status = 'uso'")]
    tecnicos = [row['tecnico'] for row in conn.execute("SELECT DISTINCT tecnico FROM ferramentas WHERE status = 'uso' AND tecnico != ''")]
    locais = [row['local'] for row in conn.execute("SELECT DISTINCT local FROM ferramentas WHERE status = 'uso' AND local != ''")]

    conn.close()

    return render_template(
        'relatorios.html',
        ferramentas=ferramentas,
        nomes_ferramentas=nomes_ferramentas,
        tecnicos=tecnicos,
        locais=locais
    )

@app.route('/relatorio_estoque', methods=['GET', 'POST'])
def relatorio_estoque():
    conn = get_db_connection()

    nome_filtro = ''
    if request.method == 'POST':
        nome_filtro = request.form.get('nome', '').lower()
        query = "SELECT nome, quantidade FROM ferramentas WHERE status = 'estoque'"
        params = []

        if nome_filtro:
            query += " AND LOWER(nome) LIKE ?"
            params.append(f"%{nome_filtro}%")

        ferramentas_estoque = conn.execute(query, params).fetchall()
    else:
        ferramentas_estoque = conn.execute("SELECT nome, quantidade FROM ferramentas WHERE status = 'estoque'").fetchall()

    nomes = [row['nome'] for row in conn.execute("SELECT DISTINCT nome FROM ferramentas WHERE status = 'estoque'")]
    conn.close()

    return render_template('relatorio_estoque.html', ferramentas_estoque=ferramentas_estoque, nomes=nomes)

@app.route('/exportar_estoque_excel')
def exportar_estoque_excel():
    conn = sqlite3.connect('ferramentas.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nome, quantidade FROM ferramentas WHERE status = 'estoque'")
    dados = cursor.fetchall()
    conn.close()

    if not dados:
        return "Nenhum dado encontrado para exportar."

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Nome da Ferramenta", "Quantidade"])
    for linha in dados:
        ws.append(linha)

    nome_arquivo = "relatorio_estoque.xlsx"
    wb.save(nome_arquivo)

    return send_file(nome_arquivo, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

# git add .
# git commit -m "Atualizamos aceitar zero unidades e deixar em vermelho"
# git push
