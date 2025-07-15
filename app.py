from flask import Flask, render_template, request, redirect, send_file, session, url_for, session
from datetime import datetime
import sqlite3
import openpyxl
import os
import smtplib
from email.message import EmailMessage
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from fpdf import FPDF
import unicodedata

app = Flask(__name__)
app.secret_key = 'chave_secreta_segura' #Nescesário para uso da sessão

#---------------GERAR PDF DE SOLICITAÇÃO DE FERRAMENTA----------------
def get_db_connection():
    conn = sqlite3.connect('ferramentas.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Função para gerar PDF (deixe essa definida em outro lugar no projeto real) ---
def gerar_pdf_solicitacao(dados, ferramentas, caminho_pdf):
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Requisição de Ferramentas", ln=True, align='C')
    pdf.ln()

    # Cabeçalho com dados principais
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Nome da Requisição: {dados['nome_requisicao']}", ln=True)
    pdf.cell(0, 10, f"Responsável: {dados['responsavel']}", ln=True)
    pdf.cell(0, 10, f"Projeto/Local: {dados['local']}", ln=True)
    pdf.cell(0, 10, f"Técnico: {dados['tecnico']}", ln=True)
    pdf.cell(0, 10, f"IDGEO: {dados['idgeo']}", ln=True)
    pdf.cell(0, 10, f"Data de Envio: {dados['data_envio']}", ln=True)
    pdf.cell(0, 10, f"Modalidade de Envio: {dados.get('modalidade_envio', 'Não especificada')}", ln=True)
    pdf.cell(0, 10, f"Data da Solicitação: {dados['data_solicitacao']}", ln=True)


    pdf.ln()
    pdf.cell(200, 10, txt="Ferramentas:", ln=True)
    for f in ferramentas:
        pdf.cell(200, 10, txt=f"- {f['nome']}: {f['quantidade']}", ln=True)

    pdf.output(caminho_pdf)

# -------------------- CONEXÃO --------------------
def get_db_connection():
    conn = sqlite3.connect('ferramentas.db')
    conn.row_factory = sqlite3.Row
    return conn

def enviar_email_com_anexo(dados, caminho_pdf):
    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg['Subject'] = f"Nova Requisição: {dados['nome_requisicao']}"
    msg['From'] = 'almoxarifado@geoambiente.eng.br'
    msg['To'] = 'almoxarifado@geoambiente.eng.br'

    corpo = f"""
Nova solicitação de ferramentas!

📄 Requisição: {dados['nome_requisicao']}
📦 Data de envio: {dados['data_envio']}
👤 Responsável: {dados['responsavel']}
🏗️ Local/Projeto: {dados['local']}
🔧 Técnico: {dados['tecnico']}
🆔 IDGEO: {dados['idgeo']}
🚚 Modalidade de envio: {dados.get('modalidade_envio', 'não especificada')}
📅 Solicitado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

🔩 Ferramentas:
"""
    for f in dados['ferramentas']:
        corpo += f"- {f['nome']}: {f['quantidade']}\n"

    msg.set_content(corpo)

    with open(caminho_pdf, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(caminho_pdf))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()
            smtp.login('almoxarifado@geoambiente.eng.br', 'swkb kwmk tjjm ozio')  # senha de app
            smtp.send_message(msg)
            print("📨 E-mail enviado com sucesso!")
    except Exception as e:
        print("❌ Erro ao enviar e-mail:", e)


# Cria a tabela 'requisicoes' caso ainda não exista
def criar_tabela_requisicoes():
    conn = sqlite3.connect('ferramentas.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requisicoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_requisicao TEXT,
            data_solicitacao TEXT,
            data_envio TEXT,
            responsavel TEXT,
            local TEXT,
            tecnico TEXT,
            idgeo TEXT,
            ferramentas TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Chama a função para garantir que a tabela existe
criar_tabela_requisicoes()




# -------------------- LOGIN --------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form['senha']
        if senha == 'Geo@#07981':
            session['logado'] = True
            return redirect('/')
        else:
            return render_template('login.html', erro='Senha incorreta.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -------------------- PÁGINA INICIAL --------------------
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

# -------------------- ADICIONAR --------------------
@app.route('/adicionar', methods=['POST'])
def adicionar():
    if not session.get('logado'):
        return redirect('/login')

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
        conn.execute('''INSERT INTO ferramentas (nome, status, local, tecnico, quantidade, idgeo)
                        VALUES (?, ?, ?, ?, ?, ?)''', (nome, status, local, tecnico, quantidade, idgeo))

    if status == 'uso':
        ferramenta_estoque = conn.execute('SELECT * FROM ferramentas WHERE nome = ? AND status = "estoque"', (nome,)).fetchone()
        if ferramenta_estoque:
            nova_qtd_estoque = ferramenta_estoque['quantidade'] - quantidade
            conn.execute('UPDATE ferramentas SET quantidade = ? WHERE id = ?', (nova_qtd_estoque, ferramenta_estoque['id']))

    conn.commit()
    conn.close()
    return redirect('/')

# -------------------- EDITAR --------------------
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if not session.get('logado'):
        return redirect('/login')

    conn = get_db_connection()
    ferramenta = conn.execute('SELECT * FROM ferramentas WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        nome = ferramenta['nome']
        status_anterior = ferramenta['status']
        quantidade_antiga = ferramenta['quantidade']
        novo_status = request.form['status']
        quantidade_nova = int(request.form['quantidade'])
        local = request.form['local']
        tecnico = request.form['tecnico']
        idgeo = request.form['idgeo']

        # Lógica de atualização
        if status_anterior == 'estoque' and novo_status == 'uso':
            existente_uso = conn.execute('''SELECT * FROM ferramentas 
                                             WHERE nome = ? AND status = 'uso' AND local = ? AND tecnico = ? AND idgeo = ?''',
                                             (nome, local, tecnico, idgeo)).fetchone()
            if existente_uso:
                nova_qtd = existente_uso['quantidade'] + quantidade_nova
                conn.execute('UPDATE ferramentas SET quantidade = ? WHERE id = ?', (nova_qtd, existente_uso['id']))
            else:
                conn.execute('''INSERT INTO ferramentas (nome, status, local, tecnico, quantidade, idgeo)
                                VALUES (?, 'uso', ?, ?, ?, ?)''', (nome, local, tecnico, quantidade_nova, idgeo))
            restante = quantidade_antiga - quantidade_nova
            conn.execute('UPDATE ferramentas SET quantidade = ? WHERE id = ?', (restante, id))

        elif status_anterior == 'uso' and novo_status == 'estoque':
            existente_estoque = conn.execute('SELECT * FROM ferramentas WHERE nome = ? AND status = "estoque"', (nome,)).fetchone()
            if existente_estoque:
                nova_qtd = existente_estoque['quantidade'] + quantidade_nova
                conn.execute('UPDATE ferramentas SET quantidade = ? WHERE id = ?', (nova_qtd, existente_estoque['id']))
                conn.execute('DELETE FROM ferramentas WHERE id = ?', (id,))
            else:
                conn.execute('''UPDATE ferramentas SET status = 'estoque', local = '', tecnico = '', idgeo = '' WHERE id = ?''', (id,))

        elif status_anterior == 'uso' and novo_status == 'uso':
            existente_uso = conn.execute('''SELECT * FROM ferramentas WHERE nome = ? AND status = 'uso' AND local = ? AND tecnico = ? AND idgeo = ?''',
                                         (nome, local, tecnico, idgeo)).fetchone()
            if existente_uso:
                nova_qtd = existente_uso['quantidade'] + quantidade_nova
                conn.execute('UPDATE ferramentas SET quantidade = ? WHERE id = ?', (nova_qtd, existente_uso['id']))
                conn.execute('DELETE FROM ferramentas WHERE id = ?', (id,))
            else:
                conn.execute('''UPDATE ferramentas SET local = ?, tecnico = ?, idgeo = ?, quantidade = ? WHERE id = ?''',
                             (local, tecnico, idgeo, quantidade_nova, id))

        else:
            conn.execute('''UPDATE ferramentas SET quantidade = ?, local = ?, tecnico = ?, idgeo = ? WHERE id = ?''',
                         (quantidade_nova, local, tecnico, idgeo, id))

        conn.commit()
        conn.close()
        return redirect('/')

    conn.close()
    return render_template('editar.html', ferramenta=ferramenta)

# -------------------- DELETAR --------------------
@app.route('/deletar/<int:id>')
def deletar(id):
    if not session.get('logado'):
        return redirect('/login')

    conn = get_db_connection()
    conn.execute('DELETE FROM ferramentas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

# -------------------- DEVOLVER --------------------
@app.route('/devolver/<int:id>')
def devolver(id):
    if not session.get('logado'):
        return redirect('/login')

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

# -------------------- RELATÓRIOS --------------------
@app.route('/relatorios', methods=['GET'])
def relatorios():
    conn = get_db_connection()
    ferramenta = request.args.get('ferramenta', '').lower()
    tecnico = request.args.get('tecnico', '').lower()
    projeto = request.args.get('projeto', '').lower()
    idgeo = request.args.get('idgeo', '').lower()

    query = '''SELECT nome, quantidade, status, local, tecnico, idgeo FROM ferramentas WHERE status = 'uso' '''
    params = []
    if ferramenta:
        query += ' AND LOWER(nome) LIKE ?'
        params.append(f'%{ferramenta}%')
    if tecnico:
        query += ' AND LOWER(tecnico) LIKE ?'
        params.append(f'%{tecnico}%')
    if projeto:
        query += ' AND LOWER(local) LIKE ?'
        params.append(f'%{projeto}%')
    if idgeo:
        query += ' AND LOWER(idgeo) LIKE ?'
        params.append(f'%{idgeo}%')

    ferramentas = conn.execute(query, params).fetchall()
    nomes_ferramentas = [row['nome'] for row in conn.execute("SELECT DISTINCT nome FROM ferramentas WHERE status = 'uso'")]
    tecnicos = [row['tecnico'] for row in conn.execute("SELECT DISTINCT tecnico FROM ferramentas WHERE status = 'uso' AND tecnico != ''")]
    locais = [row['local'] for row in conn.execute("SELECT DISTINCT local FROM ferramentas WHERE status = 'uso' AND local != ''")]
    idgeos = [row['idgeo'] for row in conn.execute("SELECT DISTINCT idgeo FROM ferramentas WHERE status = 'uso' AND idgeo != ''")]

    conn.close()
    return render_template('relatorios.html', ferramentas=ferramentas, nomes_ferramentas=nomes_ferramentas, tecnicos=tecnicos, locais=locais, idgeos=idgeos)

# -------------------- RELATÓRIO ESTOQUE --------------------
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

# -------------------- EXPORTAÇÃO --------------------
@app.route('/exportar_excel')
def exportar_excel():
    ferramenta = request.args.get('ferramenta', '').lower()
    tecnico = request.args.get('tecnico', '').lower()
    projeto = request.args.get('projeto', '').lower()
    idgeo = request.args.get('idgeo', '').lower()

    query = '''SELECT nome, quantidade, status, local, tecnico, idgeo FROM ferramentas WHERE status = 'uso' '''
    params = []
    if ferramenta:
        query += ' AND LOWER(nome) LIKE ?'
        params.append(f'%{ferramenta}%')
    if tecnico:
        query += ' AND LOWER(tecnico) LIKE ?'
        params.append(f'%{tecnico}%')
    if projeto:
        query += ' AND LOWER(local) LIKE ?'
        params.append(f'%{projeto}%')
    if idgeo:
        query += ' AND LOWER(idgeo) LIKE ?'
        params.append(f'%{idgeo}%')

    conn = sqlite3.connect('ferramentas.db')
    cursor = conn.cursor()
    dados = cursor.execute(query, params).fetchall()
    conn.close()

    if not dados:
        return "Nenhum dado encontrado para exportar."

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Nome", "Quantidade", "Status", "Projeto", "Técnico", "IDGEO"])
    for linha in dados:
        ws.append(linha)

    nome_arquivo = "relatorio_projetos.xlsx"
    wb.save(nome_arquivo)
    return send_file(nome_arquivo, as_attachment=True)

@app.route('/exportar_estoque')
def exportar_estoque():
    conn = get_db_connection()
    ferramentas = conn.execute('SELECT * FROM ferramentas WHERE status = "estoque"').fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Estoque'
    ws.append(['ID', 'Nome', 'Quantidade', 'Local', 'Técnico', 'IDGEO'])
    for f in ferramentas:
        ws.append([f['id'], f['nome'], f['quantidade'], f['local'], f['tecnico'], f['idgeo']])

    caminho_arquivo = os.path.join(os.path.expanduser("~"), "relatorio_estoque.xlsx")
    wb.save(caminho_arquivo)
    return send_file(caminho_arquivo, as_attachment=True)

#--------------CONFIRMAR RELATORIO------------------------------------
@app.route('/confirmar_solicitacao', methods=['POST'])
def confirmar_solicitacao():
    ferramentas_selecionadas = request.form.getlist('ferramentas[]')
    dados = {
        'nome_requisicao': request.form.get('nome_requisicao'),
        'responsavel': request.form.get('responsavel'),
        'local': request.form.get('local'),
        'tecnico': request.form.get('tecnico'),
        'idgeo': request.form.get('idgeo'),
        'data_envio': request.form.get('data_envio'),
        'modalidade_envio': request.form.get('modalidade_envio'),
        'ferramentas': []
    }

    for nome in ferramentas_selecionadas:
        qtd = request.form.get(f'quantidade_{nome}', '')
        dados['ferramentas'].append({
            'nome': nome,
            'quantidade': qtd
        })

    session['dados_requisicao'] = dados
    return render_template('confirmar_solicitacao.html', dados=dados)

# --- Rota final para processar a requisição ---
@app.route('/solicitar', methods=['GET', 'POST'])
def solicitar_ferramentas():
    conn = get_db_connection()

    if request.method == 'POST':
        # Se for retorno da tela de confirmação (botão Voltar)
        if request.form.get('confirmacao_final') == 'true':
            ferramentas_form = []
            ferramentas_disponiveis = conn.execute(
                'SELECT nome, quantidade FROM ferramentas WHERE status = "estoque" AND quantidade > 0'
            ).fetchall()

            ferramentas_selecionadas = request.form.getlist('ferramentas[]')

            for f in ferramentas_disponiveis:
                nome = f['nome']
                ferramentas_form.append({
                    'nome': nome,
                    'quantidade': f['quantidade'],
                    'selecionada': nome in ferramentas_selecionadas,
                    'qtd_solicitada': request.form.get(f'quantidade_' + nome, '')
                })

            conn.close()
            return render_template('solicitar.html', ferramentas=ferramentas_form,
                                   nome_requisicao=request.form.get('nome_requisicao'),
                                   responsavel=request.form.get('responsavel'),
                                   local=request.form.get('local'),
                                   tecnico=request.form.get('tecnico'),
                                   idgeo=request.form.get('idgeo'),
                                   data_envio=request.form.get('data_envio'),
                                   modalidade_envio=request.form.get('modalidade_envio'))

        # Processa a confirmação final e envia o e-mail
        if request.form.get('confirmado') == 'true':
            data_envio_raw = request.form.get('data_envio')  # exemplo: '2025-07-31'
            data_envio_formatada = datetime.strptime(data_envio_raw, '%Y-%m-%d').strftime('%d/%m/%Y')
            ferramentas_selecionadas = request.form.getlist('ferramentas[]')
            dados = {
                'nome_requisicao': request.form.get('nome_requisicao'),
                'responsavel': request.form.get('responsavel'),
                'local': request.form.get('local'),
                'tecnico': request.form.get('tecnico'),
                'idgeo': request.form.get('idgeo'),
                'data_envio':data_envio_formatada,
                'modalidade_envio': request.form.get('modalidade_envio'),
                'ferramentas': []
            }

            for nome in ferramentas_selecionadas:
                qtd = request.form.get(f'quantidade_{nome}', '1')
                dados['ferramentas'].append({'nome': nome, 'quantidade': qtd})

            data_solicitacao = datetime.now().strftime('%d/%m/%Y às %H:%M')
            dados['data_solicitacao'] = data_solicitacao
            ferramentas_str = ", ".join([f"{f['nome']} ({f['quantidade']})" for f in dados['ferramentas']])
            conn.execute('''
                INSERT INTO requisicoes (nome_requisicao, data_solicitacao, data_envio, responsavel, local, tecnico, idgeo, ferramentas, modalidade_envio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (dados['nome_requisicao'], data_solicitacao, dados['data_envio'], dados['responsavel'],
                  dados['local'], dados['tecnico'], dados['idgeo'], ferramentas_str, dados['modalidade_envio']))

            # Atualizar estoque
            for f in dados['ferramentas']:
                nome = f['nome']
                quantidade = int(f['quantidade'])

                ferramenta_estoque = conn.execute(
                    'SELECT * FROM ferramentas WHERE nome = ? AND status = "estoque"', (nome,)
                ).fetchone()

                if ferramenta_estoque and ferramenta_estoque['quantidade'] >= quantidade:
                    nova_qtd = ferramenta_estoque['quantidade'] - quantidade
                    conn.execute('UPDATE ferramentas SET quantidade = ? WHERE id = ?', (nova_qtd, ferramenta_estoque['id']))

                    ferramenta_uso = conn.execute('''
                        SELECT * FROM ferramentas WHERE nome = ? AND status = "uso" AND local = ? AND tecnico = ? AND idgeo = ?
                    ''', (nome, dados['local'], dados['tecnico'], dados['idgeo'])).fetchone()

                    if ferramenta_uso:
                        nova_qtd_uso = ferramenta_uso['quantidade'] + quantidade
                        conn.execute('UPDATE ferramentas SET quantidade = ? WHERE id = ?', (nova_qtd_uso, ferramenta_uso['id']))
                    else:
                        conn.execute('''
                            INSERT INTO ferramentas (nome, status, local, tecnico, quantidade, idgeo)
                            VALUES (?, 'uso', ?, ?, ?, ?)
                        ''', (nome, dados['local'], dados['tecnico'], quantidade, dados['idgeo']))

            # Geração e envio do PDF
            nome_limpo = unicodedata.normalize('NFKD', dados['nome_requisicao']).encode('ASCII', 'ignore').decode('ASCII')
            nome_arquivo_pdf = f"requisicao_{nome_limpo.replace(' ', '_')}.pdf"
            pdf_path = os.path.join('static', nome_arquivo_pdf)
            gerar_pdf_solicitacao(dados, dados['ferramentas'], pdf_path)
            enviar_email_com_anexo(dados, pdf_path)

            conn.commit()
            conn.close()

            return render_template('sucesso.html', nome_pdf=nome_arquivo_pdf)

    # GET padrão: exibe o formulário
    ferramentas = conn.execute(
        'SELECT nome, quantidade FROM ferramentas WHERE status = "estoque" AND quantidade > 0'
    ).fetchall()
    conn.close()
    return render_template('solicitar.html', ferramentas=ferramentas)


@app.route('/sucesso')
def sucesso():
    nome_pdf = request.args.get('pdf')
    return render_template('sucesso.html', nome_pdf=nome_pdf)




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

#  git add .
#  git commit -m "Adicionamos  a função de solicitar ferramentas"
#  git push

