import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import pytz
import time
import threading

class AutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Automação de Fechamento de Caixas")

        self.style = ttk.Style()
        self.style.configure('TButton', font=('calibri', 10, 'bold'), borderwidth='4')
        self.style.configure('TLabel', font=('calibri', 10, 'bold'))
        self.style.configure('TEntry', font=('calibri', 10, 'bold'))

        self.label_username = ttk.Label(root, text="Operador:")
        self.label_username.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_username = ttk.Entry(root)
        self.entry_username.grid(row=0, column=1, padx=5, pady=5)

        self.label_password = ttk.Label(root, text="Senha:")
        self.label_password.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_password = ttk.Entry(root, show="*")
        self.entry_password.grid(row=1, column=1, padx=5, pady=5)

        self.label_schedule_start_time = ttk.Label(root, text="Horário de Início (HH:MM):")
        self.label_schedule_start_time.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_schedule_start_time = ttk.Entry(root)
        self.entry_schedule_start_time.grid(row=2, column=1, padx=5, pady=5)

        self.label_schedule_end_time = ttk.Label(root, text="Horário de Término (HH:MM):")
        self.label_schedule_end_time.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.entry_schedule_end_time = ttk.Entry(root)
        self.entry_schedule_end_time.grid(row=3, column=1, padx=5, pady=5)

        self.login_button = ttk.Button(root, text="Fazer login", command=self.login)
        self.login_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        self.start_button = ttk.Button(root, text="Iniciar Fechamento de Caixa", command=self.schedule_automation)
        self.start_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

        self.stop_button = ttk.Button(root, text="Parar Fechamento de Caixa", command=self.stop_automation, state="disabled")
        self.stop_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

        self.text_log = scrolledtext.ScrolledText(root, width=50, height=10, wrap=tk.WORD)
        self.text_log.grid(row=7, column=0, columnspan=2, padx=5, pady=5)

        self.driver = None
        self.automation_thread = None
        self.running = False

    def log_message(self, message):
        self.text_log.insert(tk.END, f"{message}\n")
        self.text_log.yview(tk.END)
        print(message)  # Também imprime no console para verificação rápida

    def login(self):
        try:
            if self.driver:
                self.driver.quit()
            self.driver = webdriver.Chrome()
            self.driver.get("http://127.0.0.1:57571/")
            time.sleep(2)

            username = self.entry_username.get()
            password = self.entry_password.get()
            self.driver.find_element(By.ID, "username").send_keys(username)
            self.driver.find_element(By.ID, "password").send_keys(password)

            self.driver.find_element(By.CLASS_NAME, "btn-primary").click()

            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[text()='Clique para realizar o fechamento dos caixas!']"))
            ).click()
            self.log_message("Login realizado com sucesso.")
        except Exception as e:
            self.log_message(f"Erro ao fazer login: {e}")

    def schedule_automation(self):
        schedule_start_time_str = self.entry_schedule_start_time.get()
        schedule_end_time_str = self.entry_schedule_end_time.get()
        try:
            schedule_start_time = datetime.strptime(schedule_start_time_str, "%H:%M").time()
            schedule_end_time = datetime.strptime(schedule_end_time_str, "%H:%M").time()
            now = datetime.now(pytz.timezone('America/Sao_Paulo'))
            schedule_start_datetime = datetime.combine(now.date(), schedule_start_time)
            schedule_end_datetime = datetime.combine(now.date(), schedule_end_time)
            schedule_start_datetime = pytz.timezone('America/Sao_Paulo').localize(schedule_start_datetime)
            schedule_end_datetime = pytz.timezone('America/Sao_Paulo').localize(schedule_end_datetime)

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
        if not self.running:
            self.running = True
            self.automation_thread = threading.Thread(target=self.run_automation)
            self.automation_thread.start()
            self.log_message("Automação iniciada.")

    def stop_automation(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.log_message("Automação parada.")

    def run_automation(self):
        while self.running:
            self.fechar_caixa()
            time.sleep(2)

    def fechar_caixa(self):
        try:
            self.log_message("Tentando fechar o caixa...")
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
            self.log_message("Fechamento de caixa realizado com sucesso.")
        except Exception as e:
            self.log_message(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationApp(root)
    root.mainloop()
