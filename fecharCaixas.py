from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import json
from datetime import datetime, timedelta, timezone
import hashlib
import os
from cryptography.fernet import Fernet
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import ntplib


# Função para obter o diretório de dados da aplicação
def get_app_data_dir():
    home_dir = os.path.expanduser("~")
    app_dir = os.path.join(home_dir, ".sqgcx")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

class Criptografia:
    @staticmethod
    def carregar_chave():
        app_dir = get_app_data_dir()
        chave_path = os.path.join(app_dir, "chave.key")
        if not os.path.exists(chave_path):
            chave = Fernet.generate_key()
            with open(chave_path, "wb") as arquivo_chave:
                arquivo_chave.write(chave)
        else:
            with open(chave_path, "rb") as arquivo_chave:
                chave = arquivo_chave.read()
        return chave

    def __init__(self):
        self.chave = self.carregar_chave()
        self.cipher_suite = Fernet(self.chave)

    def criptografar(self, dados):
        return self.cipher_suite.encrypt(json.dumps(dados).encode()).decode()

    def descriptografar(self, dados_criptografados):
        return json.loads(self.cipher_suite.decrypt(dados_criptografados.encode()).decode())

class LicencaManager:
    def __init__(self, criptografia):
        self.criptografia = criptografia

    def get_ntp_time(self):
        try:
            client = ntplib.NTPClient()
            response = client.request('pool.ntp.org')
            return datetime.fromtimestamp(response.tx_time, timezone.utc)
        except Exception as e:
            raise Exception("Erro ao obter horário da internet: " + str(e))
        
    # TESTE DE EXPIRAÇÃO
    
    # def get_ntp_time(self):
    #     # Simula uma data futura (descomente uma das linhas)
    #     return datetime(2025, 2, 8)  # Data futura válida
    #     # return datetime(2025, 1, 1)   # Data expirada

    def carregar_licencas(self):
        app_dir = get_app_data_dir()
        licencas_path = os.path.join(app_dir, "licencas.json")
        if not os.path.exists(licencas_path):
            with open(licencas_path, "w") as arquivo:
                dados_iniciais = self.criptografia.criptografar({"licenca": None, "expiracao": None})
                arquivo.write(dados_iniciais)
        with open(licencas_path, "r") as arquivo:
            licencas = self.criptografia.descriptografar(arquivo.read())
            if "licenca" not in licencas or "expiracao" not in licencas:
                licencas = {"licenca": None, "expiracao": None}
                self.salvar_licencas(licencas)
            return licencas

    def salvar_licencas(self, licencas):
        app_dir = get_app_data_dir()
        licencas_path = os.path.join(app_dir, "licencas.json")
        with open(licencas_path, "w") as arquivo:
            dados_criptografados = self.criptografia.criptografar(licencas)
            arquivo.write(dados_criptografados)

    def verificar_licenca(self, licencas):
        if licencas["licenca"] and licencas["expiracao"]:
            try:
                data_expiracao = datetime.strptime(licencas["expiracao"], "%Y-%m-%d").date()
                current_time = self.get_ntp_time().date()
                
                return current_time <= data_expiracao
            except Exception as e:
                print(f"Falha na verificação NTP: {e}")
                return False
        return False

class Automacao:
    def __init__(self):
        self.driver = None
        self.running = False
        self.automation_thread = None

    def login(self, url, username, password, log_message):
        try:
            if self.driver:
                self.driver.quit()
            self.driver = webdriver.Chrome()

            self.driver.get(url)
            time.sleep(2)

            self.driver.find_element(By.ID, "username").send_keys(username)
            self.driver.find_element(By.ID, "password").send_keys(password)

            self.driver.find_element(By.CLASS_NAME, "btn-primary").click()

            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[text()='Clique para realizar o fechamento dos caixas!']"))
            ).click()
            log_message("Login realizado com sucesso.")
        except Exception as e:
            log_message(f"Erro ao fazer login: {e}")

    def fechar_caixa(self, log_message):
        try:
            log_message("Tentando fechar o caixa...")
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'TabelaConteudo')]//tr[contains(@bgcolor, '#F0F0F0')]//a"))
            )

            primeiro_item = self.driver.find_element(By.XPATH, "//table[contains(@class, 'TabelaConteudo')]//tr[contains(@bgcolor, '#F0F0F0')]//a")
            primeiro_item.click()

            time.sleep(3)

            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)

            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'btnSalvar'))
            )
            salvar_button = self.driver.find_element(By.ID, 'btnSalvar')
            salvar_button.click()

            WebDriverWait(self.driver, 10).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert.accept()

            time.sleep(3)
            log_message("Fechamento de caixa realizado com sucesso.")
        except Exception as e:
            log_message(f"Ocorreu um erro: {e}")

    def run_automation(self, log_message):
        while self.running:
            self.fechar_caixa(log_message)
            time.sleep(2)

    def start_automation(self, log_message):
        if not self.running:
            self.running = True
            self.automation_thread = threading.Thread(target=self.run_automation, args=(log_message,))
            self.automation_thread.start()
            log_message("Automação iniciada.")

    def stop_automation(self, log_message):
        self.running = False
        log_message("Automação parada.")

class AdminManager:
    def __init__(self, licenca_manager):
        self.licenca_manager = licenca_manager
        self.admin_usuario = "lpg"
        self.admin_senha = "*automa1"

    def abrir_menu_admin(self, root):
        usuario = simpledialog.askstring("Admin", "Usuário:", parent=root)
        senha = simpledialog.askstring("Admin", "Senha:", parent=root, show="*")
        if usuario == self.admin_usuario and senha == self.admin_senha:
            self.menu_gerenciar_licencas(root)
        else:
            messagebox.showerror("Erro", "Credenciais inválidas.")

    def menu_gerenciar_licencas(self, root):
        janela_admin = tk.Toplevel(root)
        janela_admin.title("Gerenciar Licenças")

        ttk.Label(janela_admin, text="Dias de Validade:").grid(row=0, column=0, padx=5, pady=5)
        entry_dias = ttk.Entry(janela_admin, width=30)
        entry_dias.grid(row=0, column=1, padx=5, pady=5)

        def gerar_licenca():
            try:
                dias = int(entry_dias.get())
                if dias > 0:
                    try:
                        client = ntplib.NTPClient()
                        response = client.request('pool.ntp.org')
                        current_time = datetime.fromtimestamp(response.tx_time, timezone.utc)
                    except Exception as e:
                        messagebox.showerror("Erro", f"Não foi possível obter horário da internet: {str(e)}")
                        return

                    data_expiracao = (current_time + timedelta(days=dias)).strftime("%Y-%m-%d")
                    licenca = hashlib.sha256(data_expiracao.encode()).hexdigest()
                    licencas = self.licenca_manager.carregar_licencas()
                    licencas["licenca"] = licenca
                    licencas["expiracao"] = data_expiracao
                    self.licenca_manager.salvar_licencas(licencas)
                    messagebox.showinfo("Sucesso", f"Licença gerada com sucesso!\nLicença: {licenca}\nExpira em: {data_expiracao}")
                else:
                    messagebox.showerror("Erro", "Dias de validade devem ser maiores que 0.")
            except ValueError:
                messagebox.showerror("Erro", "Por favor, insira um número válido de dias.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao gerar licença: {str(e)}")

        ttk.Button(janela_admin, text="Gerar Licença", command=gerar_licenca).grid(row=1, column=0, columnspan=2, padx=5, pady=5)


class InterfaceGrafica:
    def __init__(self, root, licenca_manager, automacao, admin_manager):
        self.root = root
        self.licenca_manager = licenca_manager
        self.automacao = automacao
        self.admin_manager = admin_manager
        self.licenca_valida = self.verificar_licenca_completa()

        self.style = ttk.Style()
        self.style.configure('TButton', font=('calibri', 10, 'bold'), borderwidth='4')
        self.style.configure('TLabel', font=('calibri', 10, 'bold'))
        self.style.configure('TEntry', font=('calibri', 10, 'bold'))

        self.menu_admin = tk.Menu(root)
        root.config(menu=self.menu_admin)
        self.menu_admin.add_command(label="Admin", command=lambda: self.admin_manager.abrir_menu_admin(root))

        self.criar_interface()

    def verificar_licenca_completa(self):
        try:
            licencas = self.licenca_manager.carregar_licencas()
            return self.licenca_manager.verificar_licenca(licencas)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na verificação de licença: {str(e)}")
            return False

    def calcular_dias_restantes(self):
        licencas = self.licenca_manager.carregar_licencas()
        if licencas["expiracao"]:
            data_expiracao = datetime.strptime(licencas["expiracao"], "%Y-%m-%d").date()
            current_time = self.licenca_manager.get_ntp_time().date()
            dias_restantes = (data_expiracao - current_time).days
            return dias_restantes
        return 0

    def criar_interface(self):
        if not self.licenca_valida:
            self.mostrar_tela_licenca_expirada()
        else:
            self.mostrar_tela_principal()

    def mostrar_tela_licenca_expirada(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.menu_admin = tk.Menu(self.root)
        self.root.config(menu=self.menu_admin)
        self.menu_admin.add_command(label="Admin", command=lambda: self.admin_manager.abrir_menu_admin(self.root))

        ttk.Label(self.root, text="Licença Expirada ou Inválida.", font=('calibri', 12, 'bold')).grid(row=0, column=0, padx=10, pady=10)
        ttk.Label(self.root, text="Contate o administrador para renovar a licença.").grid(row=1, column=0, padx=10, pady=10)

    def mostrar_tela_principal(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        # Adicionando o contador de dias restantes
        dias_restantes = self.calcular_dias_restantes()
        self.label_dias_restantes = ttk.Label(self.root, text=f"Dias restantes para expiração da licença: {dias_restantes}", font=('calibri', 10, 'bold'))
        self.label_dias_restantes.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        self.label_url = ttk.Label(self.root, text="URL:")
        self.label_url.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_url = ttk.Entry(self.root, width=30)
        self.entry_url.grid(row=1, column=1, padx=5, pady=5)

        self.label_username = ttk.Label(self.root, text="Operador:")
        self.label_username.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_username = ttk.Entry(self.root, width=30)
        self.entry_username.grid(row=2, column=1, padx=5, pady=5)

        self.label_password = ttk.Label(self.root, text="Senha:")
        self.label_password.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_password = ttk.Entry(self.root, show="*", width=30)
        self.entry_password.grid(row=3, column=1, padx=5, pady=5)

        self.label_schedule_start_time = ttk.Label(self.root, text="Horário de Início (HH:MM):")
        self.label_schedule_start_time.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.entry_schedule_start_time = ttk.Entry(self.root, width=30)
        self.entry_schedule_start_time.grid(row=4, column=1, padx=5, pady=5)

        self.label_schedule_end_time = ttk.Label(self.root, text="Horário de Término (HH:MM):")
        self.label_schedule_end_time.grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.entry_schedule_end_time = ttk.Entry(self.root, width=30)
        self.entry_schedule_end_time.grid(row=5, column=1, padx=5, pady=5)

        self.login_button = ttk.Button(self.root, text="Fazer login", command=self.login)
        self.login_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

        self.start_button = ttk.Button(self.root, text="Iniciar Fechamento de Caixa", command=self.schedule_automation)
        self.start_button.grid(row=7, column=0, columnspan=2, padx=5, pady=5)

        self.stop_button = ttk.Button(self.root, text="Parar Fechamento de Caixa", command=self.stop_automation, state="disabled")
        self.stop_button.grid(row=8, column=0, columnspan=2, padx=5, pady=5)

        self.text_log = scrolledtext.ScrolledText(self.root, width=50, height=10, wrap=tk.WORD)
        self.text_log.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

    def log_message(self, message):
        self.text_log.insert(tk.END, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        self.text_log.yview(tk.END)
        print(message)

    def login(self):
        url = self.entry_url.get()
        username = self.entry_username.get()
        password = self.entry_password.get()
        self.automacao.login(url, username, password, self.log_message)

    def schedule_automation(self):
        schedule_start_time_str = self.entry_schedule_start_time.get()
        schedule_end_time_str = self.entry_schedule_end_time.get()
        try:
            schedule_start_time = datetime.strptime(schedule_start_time_str, "%H:%M").time()
            schedule_end_time = datetime.strptime(schedule_end_time_str, "%H:%M").time()
            now = datetime.now()
            schedule_start_datetime = datetime.combine(now.date(), schedule_start_time)
            schedule_end_datetime = datetime.combine(now.date(), schedule_end_time)

            if schedule_start_time < now.time():
                schedule_start_datetime += timedelta(days=1)
            if schedule_end_time < now.time():
                schedule_end_datetime += timedelta(days=1)

            start_delay = (schedule_start_datetime - now).total_seconds()
            end_delay = (schedule_end_datetime - now).total_seconds()
            self.log_message(f"Delay de início calculado: {start_delay} segundos.")
            self.log_message(f"Delay de término calculado: {end_delay} segundos.")

            if start_delay <= 0 or end_delay <= 0:
                self.log_message("O horário agendado já passou para hoje. Por favor, defina horários futuros.")
                return

            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")

            self.log_message(f"Automação agendada para iniciar às {schedule_start_time_str} e terminar às {schedule_end_time_str}.")
            threading.Timer(start_delay, self.start_automation).start()
            threading.Timer(end_delay, self.stop_automation).start()

        except ValueError:
            self.log_message("Formato de horário inválido. Use HH:MM.")

    def start_automation(self):
        self.automacao.start_automation(self.log_message)

    def stop_automation(self):
        self.automacao.stop_automation(self.log_message)
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Conferência Automática")
    criptografia = Criptografia()
    licenca_manager = LicencaManager(criptografia)
    automacao = Automacao()
    admin_manager = AdminManager(licenca_manager)
    app = InterfaceGrafica(root, licenca_manager, automacao, admin_manager)
    img = Image.new("RGB", (1, 1), (173, 216, 230))
    icone = ImageTk.PhotoImage(img)
    root.iconphoto(True, icone)
    root.mainloop()
