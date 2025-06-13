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
    conn = get_db_connection()
    ferramentas_estoque = conn.execute('SELECT * FROM ferramentas WHERE status = "estoque"').fetchall()
    ferramentas_uso = conn.execute('SELECT * FROM ferramentas WHERE status = "uso"').fetchall()
    conn.close()
    return render_template('index.html', ferramentas_estoque=ferramentas_estoque, ferramentas_uso=ferramentas_uso)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    nome = request.form['nome']
    status = request.form['status']
    local = request.form['local']
    tecnico = request.form['tecnico']
    quantidade = int(request.form['quantidade'])
    idgeo = request.form['idgeo']

    conn = get_db_connection()
    existente = conn.execute('''
        SELECT * FROM ferramentas
        WHERE nome = ? AND status = ? AND local = ? AND tecnico = ? AND idgeo = ?
    ''', (nome, status, local, tecnico, idgeo)).fetchone()

    if existente:
        nova_qtd = existente['quantidade'] + quantidade
        conn.execute('''
            UPDATE ferramentas SET quantidade = ? WHERE id = ?
        ''', (nova_qtd, existente['id']))
    else:
        conn.execute('''
            INSERT INTO ferramentas (nome, status, local, tecnico, quantidade, idgeo)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome, status, local, tecnico, quantidade, idgeo))

    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/deletar/<int:id>')
def deletar(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM ferramentas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/devolver/<int:id>')
def devolver(id):
    conn = sqlite3.connect('ferramentas.db')
    cursor = conn.cursor()

    cursor.execute("SELECT nome, quantidade FROM ferramentas WHERE id = ? AND status = 'uso'", (id,))
    ferramenta_em_uso = cursor.fetchone()

    if ferramenta_em_uso:
        nome, quantidade = ferramenta_em_uso
        cursor.execute("SELECT id, quantidade FROM ferramentas WHERE nome = ? AND status = 'estoque'", (nome,))
        ferramenta_estoque = cursor.fetchone()

        if ferramenta_estoque:
            estoque_id, estoque_quantidade = ferramenta_estoque
            nova_quantidade = estoque_quantidade + quantidade
            cursor.execute("UPDATE ferramentas SET quantidade = ? WHERE id = ?", (nova_quantidade, estoque_id))
        else:
            cursor.execute("""
                INSERT INTO ferramentas (nome, quantidade, status, local, tecnico, idgeo)
                VALUES (?, ?, 'estoque', '', '', '')
            """, (nome, quantidade))

        cursor.execute("DELETE FROM ferramentas WHERE id = ?", (id,))

    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    if request.method == 'POST':
        nova_quantidade = int(request.form['quantidade'])
        novo_local = request.form['local']
        novo_tecnico = request.form['tecnico']
        novo_idgeo = request.form['idgeo']

        conn.execute('''
            UPDATE ferramentas
            SET quantidade = ?, local = ?, tecnico = ?, idgeo = ?
            WHERE id = ?
        ''', (nova_quantidade, novo_local, novo_tecnico, novo_idgeo, id))
        conn.commit()
        conn.close()
        return redirect('/')

    ferramenta = conn.execute('SELECT * FROM ferramentas WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('editar.html', ferramenta=ferramenta)

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


@app.route('/relatorio_estoque')
def relatorio_estoque():
    conn = get_db_connection()
    ferramentas_estoque = conn.execute("SELECT nome, quantidade FROM ferramentas WHERE status = 'estoque'").fetchall()
    conn.close()
    return render_template('relatorio_estoque.html', ferramentas=ferramentas_estoque)

@app.route('/exportar_excel')
def exportar_excel():
    ferramenta = request.args.get('ferramenta', '')
    tecnico = request.args.get('tecnico', '')
    projeto = request.args.get('projeto', '')

    query = "SELECT nome, quantidade, local, tecnico, idgeo FROM ferramentas WHERE status = 'uso'"
    params = []

    if ferramenta:
        query += " AND LOWER(nome) LIKE ?"
        params.append(f"%{ferramenta.lower()}%")
    if tecnico:
        query += " AND LOWER(tecnico) LIKE ?"
        params.append(f"%{tecnico.lower()}%")
    if projeto:
        query += " AND LOWER(local) LIKE ?"
        params.append(f"%{projeto.lower()}%")

    conn = sqlite3.connect('ferramentas.db')
    cursor = conn.cursor()
    cursor.execute(query, params)
    dados = cursor.fetchall()
    conn.close()

    if not dados:
        return "Nenhum dado encontrado para exportar."

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Nome", "Quantidade", "Projeto", "Técnico", "IDGEO"])
    for linha in dados:
        ws.append(linha)

    arquivo = "relatorio_projetos.xlsx"
    wb.save(arquivo)
    return send_file(arquivo, as_attachment=True)

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
    ws.append(["Nome", "Quantidade"])
    for linha in dados:
        ws.append(linha)

    arquivo = "relatorio_estoque.xlsx"
    wb.save(arquivo)
    return send_file(arquivo, as_attachment=True)

if __name__ == '__main__':
    print("Iniciando o servidor Flask...")
    app.run(debug=True)

 git add .
 git commit -m "Planilha de estoque salvo"
 git push



