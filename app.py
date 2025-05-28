import sqlite3
import os, sys, subprocess, datetime, logging
from datetime import datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import xlsxwriter
from xlsxwriter.exceptions import FileCreateError

# =========================================================
# ► S E T U P   L O G G I N G ◄
# =========================================================
logging.basicConfig(filename='ponto.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# =========================================================
# ► B A N C O   D E   D A D O S ◄
# =========================================================
DB = "ponto.db"

def conectar():
    try:
        return sqlite3.connect(DB)
    except sqlite3.Error as e:
        logging.error(f"Erro ao conectar ao banco: {e}")
        messagebox.showerror("Erro", "Falha ao conectar ao banco de dados.")
        sys.exit(1)

def criar_banco():
    try:
        conn = conectar(); c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS funcionarios(
                    id INTEGER PRIMARY KEY,
                    nome TEXT NOT NULL,
                    cargo TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS ponto(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    funcionario_id INTEGER NOT NULL,
                    data TEXT NOT NULL,
                    hora_entrada TEXT,
                    hora_saida TEXT,
                    FOREIGN KEY(funcionario_id) REFERENCES funcionarios(id))""")
        c.execute("""CREATE TABLE IF NOT EXISTS usuarios(
                    username TEXT PRIMARY KEY,
                    senha TEXT NOT NULL)""")
        c.execute("SELECT COUNT(*) FROM usuarios")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO usuarios (username, senha) VALUES ('admin', '1234')")
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Erro ao criar banco: {e}")
        messagebox.showerror("Erro", "Falha ao criar banco de dados.")
    finally:
        conn.close()

# =========================================================
# ► F U N Ç Õ E S   D O   S I S T E M A ◄
# =========================================================
def validar_id(fid):
    try:
        return int(fid) > 0
    except ValueError:
        return False

def validar_nome_cargo(texto):
    return bool(texto.strip()) and len(texto.strip()) <= 100

def cadastrar_funcionario(fid: str, nome: str, cargo: str):
    if not validar_id(fid):
        messagebox.showerror("Erro", "ID deve ser um número positivo.")
        return
    if not validar_nome_cargo(nome) or not validar_nome_cargo(cargo):
        messagebox.showerror("Erro", "Nome e cargo devem ser não vazios e ter até 100 caracteres.")
        return
    conn = conectar(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO funcionarios (id, nome, cargo) VALUES (?, ?, ?)",
                    (int(fid), nome.strip(), cargo.strip()))
        conn.commit()
        messagebox.showinfo("Sucesso", f"Funcionário '{nome}' cadastrado!")
        logging.info(f"Funcionário cadastrado: ID={fid}, Nome={nome}, Cargo={cargo}")
    except sqlite3.IntegrityError:
        messagebox.showerror("Erro", f"ID {fid} já existe.")
    except sqlite3.Error as e:
        logging.error(f"Erro ao cadastrar funcionário: {e}")
        messagebox.showerror("Erro", "Falha ao cadastrar funcionário.")
    finally:
        conn.close()
        atualizar_func_combo()

def buscar_funcionario(termo: str):
    if not termo.strip():
        messagebox.showerror("Erro", "Digite um termo para busca.")
        return []
    conn = conectar(); cur = conn.cursor()
    try:
        cur.execute("SELECT id, nome, cargo FROM funcionarios WHERE id=? OR nome LIKE ?",
                    (termo, f"%{termo}%"))
        res = cur.fetchall()
        return res
    except sqlite3.Error as e:
        logging.error(f"Erro ao buscar funcionário: {e}")
        messagebox.showerror("Erro", "Falha ao buscar funcionário.")
        return []
    finally:
        conn.close()

def registrar_entrada(fid: int):
    conn = conectar(); cur = conn.cursor()
    try:
        data = dt.now().strftime("%Y-%m-%d")
        hora = dt.now().strftime("%H:%M:%S")
        cur.execute("INSERT INTO ponto (funcionario_id, data, hora_entrada) VALUES (?, ?, ?)",
                    (fid, data, hora))
        conn.commit()
        atualizar_log(f"Entrada registrada: {hora}")
        logging.info(f"Entrada registrada: Funcionário ID={fid}, Data={data}, Hora={hora}")
    except sqlite3.Error as e:
        logging.error(f"Erro ao registrar entrada: {e}")
        messagebox.showerror("Erro", "Falha ao registrar entrada.")
    finally:
        conn.close()

def registrar_saida(fid: int):
    conn = conectar(); cur = conn.cursor()
    try:
        data = dt.now().strftime("%Y-%m-%d")
        hora = dt.now().strftime("%H:%M:%S")
        cur.execute("""UPDATE ponto SET hora_saida=?
                       WHERE funcionario_id=? AND data=? AND hora_saida IS NULL""",
                    (hora, fid, data))
        conn.commit()
        if cur.rowcount:
            atualizar_log(f"Saída registrada: {hora}")
            logging.info(f"Saída registrada: Funcionário ID={fid}, Data={data}, Hora={hora}")
        else:
            atualizar_log("Nenhuma entrada pendente.")
            messagebox.showwarning("Aviso", "Nenhuma entrada pendente para este funcionário.")
    except sqlite3.Error as e:
        logging.error(f"Erro ao registrar saída: {e}")
        messagebox.showerror("Erro", "Falha ao registrar saída.")
    finally:
        conn.close()

def exportar_para_excel(data_inicio=None, data_fim=None):
    if messagebox.askyesno("Confirmação", "Deseja exportar os registros para Excel?"):
        conn = conectar(); cur = conn.cursor()
        try:
            query = '''SELECT p.id, f.id, f.nome, f.cargo, p.data, p.hora_entrada, p.hora_saida
                      FROM ponto p JOIN funcionarios f ON f.id = p.funcionario_id'''
            params = []
            if data_inicio and data_fim:
                query += " WHERE p.data BETWEEN ? AND ?"
                params = [data_inicio, data_fim]
            query += " ORDER BY p.data, p.hora_entrada"
            cur.execute(query, params)
            rows = cur.fetchall()
            if not rows:
                messagebox.showinfo("Aviso", "Sem registros para exportar.")
                return
            arq = f"registros_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            wb = xlsxwriter.Workbook(arq)
            ws = wb.add_worksheet("Pontos")
            fmt_cab = wb.add_format({'bold': True, 'bg_color': '#0288D1', 'font_color': 'white'})
            fmt_date = wb.add_format({'num_format': 'dd/mm/yyyy'})
            fmt_dia = wb.add_format({'num_format': '[$-0416]ddd'})
            fmt_hora = wb.add_format({'num_format': 'hh:mm:ss'})
            fmt_total = wb.add_format({'num_format': '[hh]:mm:ss'})
            headers = ["ID Reg.", "ID Func.", "Nome", "Cargo", "Data", "Dia", "Entrada", "Saída", "Horas"]
            for c, h in enumerate(headers):
                ws.write(0, c, h, fmt_cab)
            for ln, (idr, idf, nome, cargo, data_s, ent_s, sai_s) in enumerate(rows, 1):
                d = dt.strptime(data_s, '%Y-%m-%d')
                ws.write(ln, 0, idr); ws.write(ln, 1, idf); ws.write(ln, 2, nome); ws.write(ln, 3, cargo)
                ws.write_datetime(ln, 4, d, fmt_date); ws.write_datetime(ln, 5, d, fmt_dia)
                e_dt = dt.strptime(ent_s, '%H:%M:%S'); ws.write_datetime(ln, 6, e_dt, fmt_hora)
                if sai_s:
                    s_dt = dt.strptime(sai_s, '%H:%M:%S'); ws.write_datetime(ln, 7, s_dt, fmt_hora)
                    ws.write_formula(ln, 8, f"=H{ln+1}-G{ln+1}", fmt_total)
            ws.autofilter(0, 0, ln, len(headers)-1); ws.set_column(0, 3, 14); ws.set_column(4, 8, 12)
            wb.close()
            messagebox.showinfo("Sucesso", f"Planilha '{arq}' criada.")
            try:
                if os.name == 'nt': os.startfile(arq)
                elif sys.platform == 'darwin': subprocess.call(['open', arq])
                else: subprocess.call(['xdg-open', arq])
            except Exception as e:
                logging.error(f"Erro ao abrir planilha: {e}")
        except FileCreateError as e:
            logging.error(f"Erro ao criar planilha: {e}")
            messagebox.showerror("Erro", "Falha ao criar planilha. Verifique se o arquivo está aberto.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao exportar: {e}")
            messagebox.showerror("Erro", "Falha ao exportar registros.")
        finally:
            conn.close()

def mudar_senha(username):
    nova_senha = simpledialog.askstring("Mudar Senha", "Digite a nova senha:", show="*")
    if nova_senha and len(nova_senha) >= 4:
        conn = conectar(); cur = conn.cursor()
        try:
            cur.execute("UPDATE usuarios SET senha=? WHERE username=?", (nova_senha, username))
            conn.commit()
            if cur.rowcount:
                messagebox.showinfo("Sucesso", "Senha alterada com sucesso!")
                logging.info(f"Senha alterada para usuário: {username}")
            else:
                messagebox.showerror("Erro", "Usuário não encontrado.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao mudar senha: {e}")
            messagebox.showerror("Erro", "Falha ao alterar senha.")
        finally:
            conn.close()
    else:
        messagebox.showerror("Erro", "A senha deve ter pelo menos 4 caracteres.")

# =========================================================
# ► I N T E R F A C E   T K I N T E R ◄
# =========================================================
class SistemaPonto:
    def __init__(self):
        self.current_user = None
        self.root = None
        self.combo = None
        self.txt_reg = None
        self.log_var = None
        self.icons = {}

    def load_icons(self):
        try:
            icon_paths = {
                'login': 'icons/login.png',
                'save': 'icons/save.png',
                'entry': 'icons/entry.png',
                'exit': 'icons/exit.png',
                'search': 'icons/search.png',
                'excel': 'icons/excel.png',
                'password': 'icons/password.png'
            }
            for key, path in icon_paths.items():
                if os.path.exists(path):
                    img = Image.open(path).resize((20, 20), Image.LANCZOS)
                    self.icons[key] = ImageTk.PhotoImage(img)
        except Exception as e:
            logging.warning(f"Erro ao carregar ícones: {e}")

    def atualizar_log(self, msg: str):
        self.log_var.set(msg)
        self.atualizar_registros()

    def atualizar_registros(self):
        try:
            conn = conectar(); cur = conn.cursor()
            cur.execute("""SELECT f.nome, p.data, p.hora_entrada, p.hora_saida
                          FROM ponto p JOIN funcionarios f ON f.id = p.funcionario_id
                          ORDER BY p.data DESC, p.hora_entrada DESC LIMIT 10""")
            regs = cur.fetchall()
            self.txt_reg.configure(state='normal')
            self.txt_reg.delete(1.0, tk.END)
            for n, d, e, s in regs:
                self.txt_reg.insert(tk.END, f"{n} | {d} | {e} → {s if s else 'Pendente'}\n")
            self.txt_reg.configure(state='disabled')
        except sqlite3.Error as e:
            logging.error(f"Erro ao atualizar registros: {e}")
            messagebox.showerror("Erro", "Falha ao atualizar registros.")
        finally:
            conn.close()

    def atualizar_func_combo(self):
        try:
            conn = conectar(); cur = conn.cursor()
            cur.execute("SELECT id, nome FROM funcionarios ORDER BY nome")
            funcs = cur.fetchall()
            self.combo['values'] = [f"{fid} - {nome}" for fid, nome in funcs]
            if self.combo['values']:
                self.combo.current(0)
        except sqlite3.Error as e:
            logging.error(f"Erro ao atualizar combo: {e}")
            messagebox.showerror("Erro", "Falha ao atualizar lista de funcionários.")
        finally:
            conn.close()

    def dashboard(self, frm):
        dash = ttk.LabelFrame(frm, text="Dashboard", padding=10)
        dash.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        try:
            conn = conectar(); cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM funcionarios")
            total_func = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM ponto WHERE data=?", (dt.now().strftime("%Y-%m-%d"),))
            entradas_hoje = cur.fetchone()[0]
            ttk.Label(dash, text=f"Funcionários: {total_func}", font=('Arial', 12)).pack(pady=2)
            ttk.Label(dash, text=f"Entradas Hoje: {entradas_hoje}", font=('Arial', 12)).pack(pady=2)
        except sqlite3.Error as e:
            logging.error(f"Erro ao carregar dashboard: {e}")
            ttk.Label(dash, text="Erro ao carregar dashboard", font=('Arial', 12)).pack(pady=2)
        finally:
            conn.close()

    def login_window(self):
        lg = tk.Tk()
        lg.title("Login - Sistema de Ponto")
        lg.geometry("350x250")
        lg.configure(bg="#263238")
        lg.resizable(False, False)
        self.load_icons()

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#263238', foreground='white', font=('Arial', 12))
        style.configure('TButton', background='#0288D1', foreground='white', font=('Arial', 10, 'bold'))
        style.map('TButton', background=[('active', '#01579B')])

        ttk.Label(lg, text="Sistema de Ponto", font=('Arial', 16, 'bold')).pack(pady=10)
        ttk.Label(lg, text="Usuário:").pack(pady=5)
        u_ent = ttk.Entry(lg, font=('Arial', 12))
        u_ent.pack(padx=20, fill='x')
        ttk.Label(lg, text="Senha:").pack(pady=5)
        p_ent = ttk.Entry(lg, show="*", font=('Arial', 12))
        p_ent.pack(padx=20, fill='x')

        def autenticar():
            user, pwd = u_ent.get().strip(), p_ent.get().strip()
            if not user or not pwd:
                messagebox.showerror("Erro", "Preencha usuário e senha.")
                return
            conn = conectar(); cur = conn.cursor()
            try:
                cur.execute("SELECT 1 FROM usuarios WHERE username=? AND senha=?", (user, pwd))
                if cur.fetchone():
                    self.current_user = user
                    lg.destroy()
                    self.iniciar_interface()
                else:
                    messagebox.showerror("Erro", "Credenciais inválidas.")
                    logging.warning(f"Tentativa de login falha: {user}")
            except sqlite3.Error as e:
                logging.error(f"Erro ao autenticar: {e}")
                messagebox.showerror("Erro", "Falha na autenticação.")
            finally:
                conn.close()

        btn = ttk.Button(lg, text="Entrar", command=autenticar, image=self.icons.get('login'), compound='left')
        btn.pack(pady=15, padx=20, fill='x')
        lg.bind('<Return>', lambda e: autenticar())
        lg.mainloop()

    def iniciar_interface(self):
        self.root = tk.Toplevel()
        self.root.title("Sistema de Ponto")
        self.root.geometry("800x600")
        self.root.configure(bg="#ECEFF1")
        self.root.resizable(True, True)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', background='#0288D1', foreground='white', font=('Arial', 10, 'bold'))
        style.map('TButton', background=[('active', '#01579B')])
        style.configure('TLabelFrame', background='#ECEFF1', foreground='#263238', font=('Arial', 12, 'bold'))
        style.configure('TLabel', background='#ECEFF1', foreground='#263238', font=('Arial', 10))

        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill='both', expand=True)

        # Cadastro
        cad = ttk.LabelFrame(frm, text="Cadastrar Funcionário", padding=10)
        cad.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        id_e = ttk.Entry(cad, width=10, font=('Arial', 10))
        nome_e = ttk.Entry(cad, width=25, font=('Arial', 10))
        cargo_e = ttk.Entry(cad, width=25, font=('Arial', 10))
        ttk.Label(cad, text="ID").grid(row=0, column=0, padx=5, pady=2)
        id_e.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(cad, text="Nome").grid(row=1, column=0, padx=5, pady=2)
        nome_e.grid(row=1, column=1, padx=5, pady=2)
        ttk.Label(cad, text="Cargo").grid(row=2, column=0, padx=5, pady=2)
        cargo_e.grid(row=2, column=1, padx=5, pady=2)
        ttk.Button(cad, text="Salvar", image=self.icons.get('save'), compound='left',
                   command=lambda: cadastrar_funcionario(id_e.get(), nome_e.get(), cargo_e.get())).grid(row=3, column=0, columnspan=2, pady=10)

        # Ponto
        pnt = ttk.LabelFrame(frm, text="Registrar Ponto", padding=10)
        pnt.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        ttk.Label(pnt, text="Funcionário").grid(row=0, column=0, padx=5, pady=2)
        self.combo = ttk.Combobox(pnt, state='readonly', width=30, font=('Arial', 10))
        self.combo.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(pnt, text="Entrada", image=self.icons.get('entry'), compound='left',
                   command=lambda: registrar_entrada(int(self.combo.get().split(' - ')[0]))).grid(row=1, column=0, pady=5, padx=5)
        ttk.Button(pnt, text="Saída", image=self.icons.get('exit'), compound='left',
                   command=lambda: registrar_saida(int(self.combo.get().split(' - ')[0]))).grid(row=1, column=1, pady=5, padx=5)

        # Dashboard
        self.dashboard(frm)

        # Busca
        ttk.Button(frm, text="Buscar Funcionário", image=self.icons.get('search'), compound='left',
                   command=self.buscar_popup).grid(row=2, column=0, pady=5, sticky='ew')

        # Registros
        self.txt_reg = tk.Text(frm, width=60, height=12, state='disabled', font=('Arial', 10), bg="#FAFAFA")
        self.txt_reg.grid(row=3, column=0, columnspan=2, pady=5, sticky='ew')

        # Export
        ttk.Button(frm, text="Exportar Excel", image=self.icons.get('excel'), compound='left',
                   command=lambda: exportar_para_excel()).grid(row=4, column=0, pady=5, sticky='ew')

        # Mudar Senha
        ttk.Button(frm, text="Mudar Senha", image=self.icons.get('password'), compound='left',
                   command=lambda: mudar_senha(self.current_user)).grid(row=4, column=1, pady=5, sticky='ew')

        # Log
        self.log_var = tk.StringVar(value="Bem-vindo!")
        ttk.Label(self.root, textvariable=self.log_var, font=('Arial', 10, 'italic')).pack(pady=5)

        self.atualizar_func_combo()
        self.atualizar_registros()

        self.root.mainloop()

    def buscar_popup(self):
        termo = simpledialog.askstring("Buscar", "ID ou parte do nome:")
        if termo:
            res = buscar_funcionario(termo)
            if res:
                txt = "\n".join([f"ID: {r[0]} | {r[1]} ({r[2]})" for r in res])
                messagebox.showinfo("Encontrados", txt)
            else:
                messagebox.showinfo("Nada", "Nenhum funcionário encontrado.")

if __name__ == '__main__':
    try:
        criar_banco()
        app = SistemaPonto()
        app.login_window()
    except Exception as e:
        logging.critical(f"Erro fatal na inicialização: {e}")
        messagebox.showerror("Erro Fatal", "O sistema encontrou um erro e será encerrado.")
        sys.exit(1)