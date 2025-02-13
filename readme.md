## Instalação

### 1. Instale as Dependências

Certifique-se de ter o `pipenv` instalado para gerenciar o ambiente virtual e as dependências do projeto.

```
pipenv install selenium webdriver_manager pyinstaller
```

### 2. Criando o Executável

Após instalar as dependências, você pode criar um executável do script fecharCaixas.py usando o PyInstaller.

```
pipenv run pyinstaller --onefile fecharCaixas.py
pipenv run pyinstaller fecharCaixas.spec
```

### Dependencias

Selenium: Biblioteca para automatização de navegadores.

WebDriver Manager: Gerenciador de WebDrivers para Selenium.

PyInstaller: Ferramenta para converter scripts Python em executáveis.
