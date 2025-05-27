import sqlite3
from datetime import datetime

def conectar():
    return sqlite3.connect('ponto.db')

def criar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cargo TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ponto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funcionario_id INTEGER NOT NULL,
        data TEXT NOT NULL,
        hora_entrada TEXT,
        hora_saida TEXT,
        FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id)
    )
    ''')

    conn.commit()
    conn.close()

def cadastrar_funcionario(nome, cargo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO funcionarios (nome, cargo) VALUES (?, ?)", (nome.strip(), cargo.strip()))
    conn.commit()
    conn.close()
    print(f"Funcionário '{nome.strip()}' cadastrado com sucesso!")

def registrar_entrada(funcionario_id):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().date().isoformat()
    hora = datetime.now().time().strftime('%H:%M:%S')

    cursor.execute('''
    INSERT INTO ponto (funcionario_id, data, hora_entrada)
    VALUES (?, ?, ?)
    ''', (funcionario_id, data, hora))

    conn.commit()
    conn.close()
    print("Entrada registrada!")

def registrar_saida(funcionario_id):
    conn = conectar()
    cursor = conn.cursor()
    data = datetime.now().date().isoformat()
    hora = datetime.now().time().strftime('%H:%M:%S')

    cursor.execute('''
    UPDATE ponto
    SET hora_saida = ?
    WHERE funcionario_id = ? AND data = ? AND hora_saida IS NULL
    ''', (hora, funcionario_id, data))

    if cursor.rowcount == 0:
        print("Nenhum registro de entrada encontrado para hoje sem saída registrada.")
    else:
        print("Saída registrada!")

    conn.commit()
    conn.close()

def ver_pontos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT p.id, f.nome, f.cargo, p.data, p.hora_entrada, p.hora_saida
    FROM ponto p
    JOIN funcionarios f ON p.funcionario_id = f.id
    ORDER BY p.data DESC, p.hora_entrada DESC
    ''')

    registros = cursor.fetchall()
    if registros:
        print("\n--- Registros de ponto ---")
        for r in registros:
            print(f"ID: {r[0]} | Funcionário: {r[1]} ({r[2]}) | Data: {r[3]} | Entrada: {r[4]} | Saída: {r[5]}")
    else:
        print("Nenhum registro de ponto encontrado.")
    conn.close()

def listar_funcionarios():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, cargo FROM funcionarios ORDER BY id")
    funcionarios = cursor.fetchall()
    if funcionarios:
        print("\n--- Lista de Funcionários ---")
        for f in funcionarios:
            print(f"ID: {f[0]} | Nome: {f[1]} | Cargo: {f[2]}")
    else:
        print("Nenhum funcionário cadastrado.")
    conn.close()

def input_id():
    while True:
        id_str = input("ID do funcionário: ").strip()
        if id_str.isdigit():
            return int(id_str)
        else:
            print("Por favor, digite um número válido para o ID.")

if __name__ == '__main__':
    criar_banco()

    while True:
        print("\n--- MENU CONTROLE DE PONTO ---")
        print("[1] Cadastrar funcionário")
        print("[2] Registrar entrada")
        print("[3] Registrar saída")
        print("[4] Ver pontos")
        print("[5] Listar funcionários")
        print("[0] Sair")

        opcao = input("Escolha uma opção: ").strip()

        if opcao == '1':
            nome = input("Nome do funcionário: ")
            cargo = input("Cargo: ")
            cadastrar_funcionario(nome, cargo)

        elif opcao == '2':
            listar_funcionarios()
            funcionario_id = input_id()
            registrar_entrada(funcionario_id)

        elif opcao == '3':
            listar_funcionarios()
            funcionario_id = input_id()
            registrar_saida(funcionario_id)

        elif opcao == '4':
            ver_pontos()

        elif opcao == '5':
            listar_funcionarios()

        elif opcao == '0':
            print("Saindo do sistema.")
            break

        else:
            print("Opção inválida. Tente novamente.")
