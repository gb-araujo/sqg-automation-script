# SQG Automation Script

Aplicacao desktop em Python para automatizar o fechamento de caixas em um sistema web. O projeto combina interface grafica com Tkinter, automacao de navegador com Selenium e geracao de executavel com PyInstaller.

## Funcionalidades

- Interface desktop para informar URL, operador, senha e horario de execucao.
- Login automatizado no sistema via Selenium.
- Execucao agendada com horario de inicio e termino.
- Log em tela para acompanhar cada tentativa de fechamento.
- Controle local de licenca com arquivo criptografado.
- Empacotamento em executavel para uso em maquinas Windows.

## Tecnologias

- Python
- Tkinter
- Selenium
- WebDriver Manager
- Cryptography/Fernet
- NTP para validacao de horario
- PyInstaller

## Requisitos

- Python 3.10 ou superior
- Google Chrome instalado
- Pipenv ou ambiente virtual Python equivalente

## Instalacao

```bash
git clone https://github.com/gb-araujo/sqg-automation-script.git
cd sqg-automation-script
pipenv install selenium webdriver_manager pyinstaller pillow cryptography ntplib
```

Tambem e possivel instalar as dependencias em um ambiente virtual comum:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install selenium webdriver_manager pyinstaller pillow cryptography ntplib
```

## Execucao em desenvolvimento

```bash
pipenv run python fecharCaixas.py
```

ou, usando ambiente virtual:

```bash
python fecharCaixas.py
```

## Gerar executavel

```bash
pipenv run pyinstaller --onefile fecharCaixas.py
```

Se quiser usar a configuracao ja existente:

```bash
pipenv run pyinstaller fecharCaixas.spec
```

O executavel sera gerado na pasta `dist/`.

## Dados locais

O aplicativo cria arquivos de apoio na pasta `~/.sqgcx`, incluindo chave criptografica e informacoes de licenca. Esses arquivos sao locais da maquina do usuario e nao devem ser versionados.

## Seguranca

Nao armazene credenciais reais no codigo-fonte. Para uso em producao, prefira variaveis de ambiente, arquivo local ignorado pelo Git ou outro mecanismo seguro de configuracao.
