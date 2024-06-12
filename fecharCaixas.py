import tkinter as tk
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

        self.login_button = ttk.Button(root, text="Fazer login", command=self.login)
        self.login_button.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        self.start_button = ttk.Button(root, text="Iniciar Fechamento de Caixa", command=self.start_automation)
        self.start_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        self.stop_button = ttk.Button(root, text="Parar Fechamento de Caixa", command=self.stop_automation, state="disabled")
        self.stop_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        self.driver = None
        self.automation_thread = None
        self.running = False

    def login(self):
        if self.driver:
            self.driver.quit()
        self.driver = webdriver.Chrome()
        self.driver.get("http://localhost:6262/lpg/index.php?sec=main")
        time.sleep(2) 


        username = self.entry_username.get()
        password = self.entry_password.get()
        self.driver.find_element(By.ID, "username").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)

        self.driver.find_element(By.CLASS_NAME, "btn-primary").click()

        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[text()='Clique para realizar o fechamento dos caixas!']"))
        ).click()
        self.start_automation()

    def start_automation(self):
        if not self.running:
            self.running = True
            self.automation_thread = threading.Thread(target=self.run_automation)
            self.automation_thread.start()
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")

    def stop_automation(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def run_automation(self):
        while self.running:
            self.fechar_caixa()
            time.sleep(2) 

    def fechar_caixa(self):
        try:
            
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
        except Exception as e:
            print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomationApp(root)
    root.mainloop()
