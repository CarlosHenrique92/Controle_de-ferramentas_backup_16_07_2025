from flask import Flask, render_template, request, redirect
import sqlite3

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
    
    # Verifica se já existe ferramenta com os mesmos dados
    existente = conn.execute('''
        SELECT * FROM ferramentas
        WHERE nome = ? AND status = ? AND local = ? AND tecnico = ? AND idgeo = ?
    ''', (nome, status, local, tecnico, idgeo)).fetchone()

    if existente:
        # Atualiza a quantidade somando
        nova_qtd = existente['quantidade'] + quantidade
        conn.execute('''
            UPDATE ferramentas
            SET quantidade = ?
            WHERE id = ?
        ''', (nova_qtd, existente['id']))
    else:
        # Insere novo registro
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

    # Busca a ferramenta que está em uso
    cursor.execute("SELECT nome, quantidade FROM ferramentas WHERE id = ? AND status = 'uso'", (id,))
    ferramenta_em_uso = cursor.fetchone()

    if ferramenta_em_uso:
        nome, quantidade = ferramenta_em_uso

        # Verifica se já existe ferramenta com mesmo nome no estoque
        cursor.execute("SELECT id, quantidade FROM ferramentas WHERE nome = ? AND status = 'estoque'", (nome,))
        ferramenta_estoque = cursor.fetchone()

        if ferramenta_estoque:
            estoque_id, estoque_quantidade = ferramenta_estoque
            nova_quantidade = estoque_quantidade + quantidade

            # Atualiza a quantidade no estoque existente
            cursor.execute("UPDATE ferramentas SET quantidade = ? WHERE id = ?", (nova_quantidade, estoque_id))
        else:
            # Não existe no estoque ainda — cria um novo registro com campos vazios
            cursor.execute("""
                INSERT INTO ferramentas (nome, quantidade, status, local, tecnico, idgeo)
                VALUES (?, ?, 'estoque', '', '', '')
            """, (nome, quantidade))

        # Remove a ferramenta em uso
        cursor.execute("DELETE FROM ferramentas WHERE id = ?", (id,))

    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/relatorios', methods=['GET', 'POST'])
def relatorios():
    conn = sqlite3.connect('ferramentas.db')
    cursor = conn.cursor()

    # Coleta dados únicos para preencher os filtros
    cursor.execute("SELECT DISTINCT nome FROM ferramentas")
    nomes_ferramentas = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT tecnico FROM ferramentas WHERE tecnico != ''")
    tecnicos = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT local FROM ferramentas WHERE local != ''")
    locais = [row[0] for row in cursor.fetchall()]

    ferramentas_filtradas = []

    if request.method == 'POST':
        nome = request.form.get('nome')
        tecnico = request.form.get('tecnico')
        local = request.form.get('local')

        query = "SELECT nome, quantidade, status, local, tecnico, idgeo FROM ferramentas WHERE 1=1"
        params = []

        if nome:
            query += " AND nome = ?"
            params.append(nome)

        if tecnico:
            query += " AND tecnico = ?"
            params.append(tecnico)

        if local:
            query += " AND local = ?"
            params.append(local)

        cursor.execute(query, params)
        ferramentas_filtradas = cursor.fetchall()

    conn.close()
    return render_template('relatorios.html',
                           nomes_ferramentas=nomes_ferramentas,
                           tecnicos=tecnicos,
                           locais=locais,
                           ferramentas=ferramentas_filtradas)


@app.route('/relatorio_estoque')
def relatorio_estoque():
    conn = sqlite3.connect('ferramentas.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nome, quantidade, local, tecnico, idgeo
        FROM ferramentas
        WHERE status = 'estoque'
        ORDER BY nome
    """)
    ferramentas_estoque = cursor.fetchall()
    conn.close()
    return render_template('relatorio_estoque.html', ferramentas=ferramentas_estoque)



@app.route('/exportar_excel_projetos')
def exportar_excel_projetos():
    import pandas as pd

    conn = sqlite3.connect('ferramentas.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nome, quantidade, local, tecnico, idgeo
        FROM ferramentas
        WHERE status = 'uso'
    """)
    dados = cursor.fetchall()
    conn.close()

    # Criar DataFrame
    df = pd.DataFrame(dados, columns=['Nome da Ferramenta', 'Quantidade', 'Projeto', 'Técnico', 'IDGEO'])

    # Salvar como Excel
    caminho = 'relatorio_projetos.xlsx'
    df.to_excel(caminho, index=False)

    from flask import send_file
    return send_file(caminho, as_attachment=True)




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

from openpyxl import Workbook
from flask import send_file
import io


@app.route('/exportar_excel')
def exportar_excel():
    conn = sqlite3.connect('ferramentas.db')
    cursor = conn.cursor()

    cursor.execute("SELECT nome, quantidade FROM ferramentas WHERE LOWER(status) = 'em estoque'")
    ferramentas_estoque = cursor.fetchall()
    conn.close()

    if not ferramentas_estoque:
        return "Nenhum dado encontrado para exportar."

    wb = Workbook()
    ws = wb.active
    ws.title = "Estoque"

    ws.append(["Nome da Ferramenta", "Quantidade"])
    for nome, quantidade in ferramentas_estoque:
        ws.append([nome, quantidade])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(output, as_attachment=True, download_name="relatorio_estoque.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')



if __name__ == '__main__':
    print("Iniciando o servidor Flask...")
    app.run(debug=True)


