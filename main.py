import sqlite3
from datetime import datetime

# === Criar banco de dados e tabelas ===
def criar_banco():
    con = sqlite3.con
    nect("ferramentas.db")
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ferramentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            quantidade_total INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_ferramenta INTEGER,
            projeto TEXT,
            quantidade INTEGER,
            data_saida TEXT,
            FOREIGN KEY (id_ferramenta) REFERENCES ferramentas(id)
        )
    """)

    con.commit()
    con.close()

# === Adicionar ferramenta sem duplicar ===
def adicionar_ferramenta(nome, quantidade):
    con = sqlite3.connect("ferramentas.db")
    cur = con.cursor()

    cur.execute("SELECT id, quantidade_total FROM ferramentas WHERE nome = ?", (nome,))
    resultado = cur.fetchone()

    if resultado:
        id_ferramenta, qtd_atual = resultado
        nova_qtd = qtd_atual + quantidade
        cur.execute("UPDATE ferramentas SET quantidade_total = ? WHERE id = ?", (nova_qtd, id_ferramenta))
        print(f"🔁 Ferramenta '{nome}' já existe. Quantidade atualizada para {nova_qtd}.")
    else:
        cur.execute("INSERT INTO ferramentas (nome, quantidade_total) VALUES (?, ?)", (nome, quantidade))
        print(f"✅ Ferramenta '{nome}' adicionada com {quantidade} unidades.")

    con.commit()
    con.close()

# === Registrar saída de ferramenta ===
def registrar_saida(nome, quantidade, projeto):
    con = sqlite3.connect("ferramentas.db")
    cur = con.cursor()

    cur.execute("SELECT id, quantidade_total FROM ferramentas WHERE nome = ?", (nome,))
    resultado = cur.fetchone()

    if not resultado:
        print(f"❌ Ferramenta '{nome}' não encontrada.")
        con.close()
        return

    id_ferramenta, total = resultado

    cur.execute("SELECT SUM(quantidade) FROM movimentacoes WHERE id_ferramenta = ?", (id_ferramenta,))
    emprestadas = cur.fetchone()[0] or 0

    disponiveis = total - emprestadas

    if quantidade > disponiveis:
        print(f"❌ Não há unidades suficientes. Disponíveis: {disponiveis}")
    else:
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO movimentacoes (id_ferramenta, projeto, quantidade, data_saida) VALUES (?, ?, ?, ?)",
                    (id_ferramenta, projeto, quantidade, data))
        print(f"📦 Saída registrada: {quantidade}x '{nome}' para projeto '{projeto}'.")

    con.commit()
    con.close()

# === Relatório de ferramentas ===
def relatorio_ferramentas():
    con = sqlite3.connect("ferramentas.db")
    cur = con.cursor()

    cur.execute("SELECT id, nome, quantidade_total FROM ferramentas")
    ferramentas = cur.fetchall()

    print("\n📋 RELATÓRIO DE FERRAMENTAS")
    for id_ferramenta, nome, total in ferramentas:
        cur.execute("SELECT SUM(quantidade) FROM movimentacoes WHERE id_ferramenta = ?", (id_ferramenta,))
        emprestadas = cur.fetchone()[0] or 0
        disponiveis = total - emprestadas

        print(f"- {nome}: Total = {total}, Emprestadas = {emprestadas}, Disponíveis = {disponiveis}")

    con.close()

# === Menu interativo ===
def menu():
    criar_banco()

    while True:
        print("\n=== MENU ===")
        print("1. Adicionar ferramenta")
        print("2. Registrar saída")
        print("3. Ver relatório")
        print("4. Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            nome = input("Nome da ferramenta: ")
            quantidade = int(input("Quantidade: "))
            adicionar_ferramenta(nome.strip().title(), quantidade)

        elif opcao == "2":
            nome = input("Nome da ferramenta: ")
            quantidade = int(input("Quantidade: "))
            projeto = input("Projeto: ")
            registrar_saida(nome.strip().title(), quantidade, projeto.strip().title())

        elif opcao == "3":
            relatorio_ferramentas()

        elif opcao == "4":
            print("👋 Saindo...")
            break

        else:
            print("⚠️ Opção inválida!")

# === Executar programa ===
if __name__ == "__main__":
    menu()

       #testar o git hub