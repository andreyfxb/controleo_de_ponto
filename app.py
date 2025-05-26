import sqlite3

def criar_banco():
    conn = sqlite3.connect('ponto.db')
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
    print("Banco e tabelas criados com sucesso!")

if __name__ == '__main__':
    criar_banco()
