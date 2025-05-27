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
    cursor.execute("INSERT INTO funcionarios (nome, cargo) VALUES (?, ?)", (nome, cargo))
    conn.commit()
    conn.close()
    print(f"Funcionário '{nome}' cadastrado com sucesso!")

def funcionario_existe(funcionario_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM funcionarios WHERE id = ?', (funcionario_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None

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

    conn.commit()
    conn.close()
    print("Saída registrada!")

def ver_pontos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT p.id, f.nome, f.cargo, p.data, p.hora_entrada, p.hora_saida
    FROM ponto p
    JOIN funcionarios f ON p.funcionario_id = f.id
    ORDER BY p.data DESC, f.nome
    ''')
    registros = cursor.fetchall()
    conn.close()

    if registros:
        print("\n--- Registros de ponto ---")
        for reg in registros:
            id_ponto, nome, cargo, data, entrada, saida = reg
            print(f"ID: {id_ponto} | Funcionário: {nome} ({cargo}) | Data: {data} | Entrada: {entrada} | Saída: {saida}")
    else:
        print("Nenhum registro encontrado.")

if __name__ == '__main__':
    criar_banco()
    
    while True:
        print("\n--- MENU CONTROLE DE PONTO ---")
        print("[1] Cadastrar funcionário")
        print("[2] Registrar entrada")
        print("[3] Registrar saída")
        print("[4] Ver pontos")
        print("[0] Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == '1':
            nome = input("Nome do funcionário: ")
            cargo = input("Cargo: ")
            cadastrar_funcionario(nome, cargo)

        elif opcao == '2':
            try:
                funcionario_id = int(input("ID do funcionário: "))
                if funcionario_existe(funcionario_id):
                    registrar_entrada(funcionario_id)
                else:
                    print("ID do funcionário não encontrado. Tente novamente.")
            except ValueError:
                print("Por favor, digite um número válido para o ID.")

        elif opcao == '3':
            try:
                funcionario_id = int(input("ID do funcionário: "))
                if funcionario_existe(funcionario_id):
                    registrar_saida(funcionario_id)
                else:
                    print("ID do funcionário não encontrado. Tente novamente.")
            except ValueError:
                print("Por favor, digite um número válido para o ID.")

        elif opcao == '4':
            ver_pontos()

        elif opcao == '0':
            print("Saindo do sistema.")
            break

        else:
            print("Opção inválida. Tente novamente.")
