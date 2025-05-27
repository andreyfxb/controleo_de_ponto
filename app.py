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
            funcionario_id = int(input("ID do funcionário: "))
            registrar_entrada(funcionario_id)

        elif opcao == '3':
            funcionario_id = int(input("ID do funcionário: "))
            registrar_saida(funcionario_id)

        elif opcao == '4':
            ver_pontos()

        elif opcao == '0':
            print("Saindo do sistema.")
            break

        else:
            print("Opção inválida. Tente novamente.")

