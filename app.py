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

def ver_pontos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT f.nome, p.data, p.hora_entrada, p.hora_saida
    FROM ponto p
    JOIN funcionarios f ON f.id = p.funcionario_id
    ORDER BY p.data DESC
    ''')
    resultados = cursor.fetchall()
    conn.close()

    for r in resultados:
        print(f"Funcionário: {r[0]} | Data: {r[1]} | Entrada: {r[2]} | Saída: {r[3]}")

# ======================== TESTE ========================
if __name__ == '__main__':
    criar_banco()
    # cadastrar_funcionario('João Silva', 'Analista')
    # registrar_entrada(1)
    registrar_saida(1)
    ver_pontos()
