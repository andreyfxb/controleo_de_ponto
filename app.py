import sqlite3
import os, sys, subprocess
from datetime import datetime

try:
    import xlsxwriter          # cria planilhas Excel
except ImportError:
    print("Falta o pacote xlsxwriter → instale com: pip install xlsxwriter")
    sys.exit(1)

# ---------- conexão ----------
def conectar():
    return sqlite3.connect('ponto.db')

def criar_banco():
    conn = conectar()
    c = conn.cursor()
    c.execute('''
      CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY,
        nome TEXT NOT NULL,
        cargo TEXT
      )
    ''')
    c.execute('''
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

# ---------- CRUD funcionário ----------
def cadastrar_funcionario(idf, nome, cargo):
    conn = conectar(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO funcionarios (id,nome,cargo) VALUES (?,?,?)",
                    (idf, nome.strip(), cargo.strip()))
        conn.commit()
        print(f"Funcionário '{nome.strip()}' cadastrado com ID {idf}.")
    except sqlite3.IntegrityError:
        print(f"ID {idf} já existe.")
    finally:
        conn.close()

def listar_funcionarios():
    conn = conectar(); cur = conn.cursor()
    cur.execute("SELECT id,nome,cargo FROM funcionarios ORDER BY id")
    rows = cur.fetchall(); conn.close()
    if rows:
        print("\n--- Funcionários ---")
        for r in rows:
            print(f"ID: {r[0]} | Nome: {r[1]} | Cargo: {r[2]}")
    else:
        print("Nenhum funcionário cadastrado.")

# ---------- ponto ----------
def registrar_entrada(fid):
    conn = conectar(); cur = conn.cursor()
    data = datetime.now().date().isoformat()
    hora = datetime.now().time().strftime('%H:%M:%S')
    cur.execute("INSERT INTO ponto (funcionario_id,data,hora_entrada) VALUES (?,?,?)",
                (fid, data, hora))
    conn.commit(); conn.close()
    print("Entrada registrada!")

def registrar_saida(fid):
    conn = conectar(); cur = conn.cursor()
    data = datetime.now().date().isoformat()
    hora = datetime.now().time().strftime('%H:%M:%S')
    cur.execute("""UPDATE ponto
                   SET hora_saida = ?
                   WHERE funcionario_id=? AND data=? AND hora_saida IS NULL""",
                (hora, fid, data))
    if cur.rowcount:
        print("Saída registrada!")
    else:
        print("Nenhuma entrada de hoje pendente para esse funcionário.")
    conn.commit(); conn.close()

def ver_pontos():
    conn = conectar(); cur = conn.cursor()
    cur.execute('''SELECT p.id,f.nome,f.cargo,p.data,p.hora_entrada,p.hora_saida
                   FROM ponto p JOIN funcionarios f ON f.id=p.funcionario_id
                   ORDER BY p.data DESC,p.hora_entrada DESC''')
    rows = cur.fetchall(); conn.close()
    if rows:
        print("\n--- Registros ---")
        for r in rows:
            print(f"Reg {r[0]} | {r[1]} ({r[2]}) | {r[3]} | Ent: {r[4]} | Sai: {r[5]}")
    else:
        print("Nenhum registro encontrado.")

# ---------- exportar para Excel ----------
def exportar_para_excel():
    conn = conectar(); cur = conn.cursor()
    cur.execute('''SELECT p.id,f.id,f.nome,f.cargo,p.data,
                          p.hora_entrada,p.hora_saida
                   FROM ponto p JOIN funcionarios f ON f.id=p.funcionario_id
                   ORDER BY p.data,p.hora_entrada''')
    dados = cur.fetchall(); conn.close()

    if not dados:
        print("Não há registros para exportar.")
        return

    arquivo = 'registros.xlsx'
    wb = xlsxwriter.Workbook(arquivo)
    ws = wb.add_worksheet('Pontos')

    cabe = ["ID Registro", "ID Func", "Nome", "Cargo",
            "Data", "Hora Entrada", "Hora Saída"]
    for col, val in enumerate(cabe):
        ws.write(0, col, val)

    for lin, row in enumerate(dados, start=1):
        for col, val in enumerate(row):
            ws.write(lin, col, val)

    wb.close()
    print(f"Planilha '{arquivo}' criada.")

    # abrir automaticamente
    caminho = os.path.abspath(arquivo)
    if os.name == 'nt':                     # Windows
        os.startfile(caminho)
    elif sys.platform == 'darwin':          # macOS
        subprocess.call(['open', caminho])
    else:                                   # Linux
        subprocess.call(['xdg-open', caminho])

# ---------- util ----------
def input_id(txt="ID: "):
    while True:
        v = input(txt).strip()
        if v.isdigit():
            return int(v)
        print("Digite número válido.")

def apagar_tudo():
    conn = conectar(); cur = conn.cursor()
    cur.execute("DELETE FROM ponto"); cur.execute("DELETE FROM funcionarios")
    conn.commit(); conn.close()
    print("Dados apagados!")

# ---------- main ----------
if __name__ == '__main__':
    criar_banco()
    while True:
        print("\n--- MENU ---")
        print("[1] Cadastrar funcionário")
        print("[2] Registrar entrada")
        print("[3] Registrar saída")
        print("[4] Ver pontos")
        print("[5] Listar funcionários")
        print("[6] Apagar TODOS os dados")
        print("[7] Exportar & abrir Excel")
        print("[0] Sair")

        op = input("Opção: ").strip()
        if op == '1':
            fid = input_id("ID novo: ")
            nome = input("Nome: ")
            cargo = input("Cargo: ")
            cadastrar_funcionario(fid, nome, cargo)
        elif op == '2':
            listar_funcionarios()
            registrar_entrada(input_id())
        elif op == '3':
            listar_funcionarios()
            registrar_saida(input_id())
        elif op == '4':
            ver_pontos()
        elif op == '5':
            listar_funcionarios()
        elif op == '6':
            if input("Confirma apagar tudo? (s/n): ").lower() == 's':
                apagar_tudo()
        elif op == '7':
            exportar_para_excel()
        elif op == '0':
            break
        else:
            print("Inválido.")
