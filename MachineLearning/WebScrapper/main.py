import os
import time
import google.generativeai as genai
from openpyxl.reader.excel import load_workbook
from openpyxl.workbook import Workbook
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from tkinter import filedialog
from PIL import Image
from openpyxl import workbook

# Configuração da chave de API da Gemini
genai.configure(api_key="")
WEBDRIVER = os.path.join(os.getcwd(), "webdriver", "msedgedriver.exe")

def iniciar():
    if not os.path.exists(os.path.join(os.getcwd(), "webdriver", "msedgedriver.exe")):
        print("Erro: Edge Driver não foi localizado. Ele deve estar localizado na pasta 'webdriver'")
    if not os.path.exists(os.path.join(os.getcwd(), "bancos de dados")):
        os.mkdir(os.path.join(os.getcwd(), "bancos de dados"))

def obter_dados_texto(url_site: str) -> None:
    options = EdgeOptions()
    options.add_argument("--headless")  # Modo headless
    options.add_argument("--window-position=3000,0")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Cria o objeto Service com o caminho do driver
    service = EdgeService(executable_path=WEBDRIVER)

    # Inicia o driver com o Edge headless
    driver = webdriver.Edge(
        service=service,
        options=options
    )
    try:
        driver.get(url_site)
        time.sleep(1)
        return driver.page_source
    except Exception as e:
        print(f"erro ao obter código da página: {e}")


def perguntar_a_ia_texto(texto: str, vars: str) -> str:
    vars = vars.split("--")
    vars = ", ".join(vars)
    """Usa a IA Gemini para responder a uma pergunta baseada no texto fornecido."""
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Prepara o prompt para a IA
    prompt = f"""
    Analise a página seguir.
    com base nela, crie uma tabela e a preencha com os seguintes dados: {vars}. Cada um desses dados deve representar
    uma coluna na tabela. os dados da tabela devem ser separados com uma barra '/'. Não coloque títulos nas colunas
    Se atenha apenas aos dados fornecidos. Extraia todos os dados da página.
    Exemplo 1:
    dados: "idade", "altura", "tipo sanguíneo"
    resultado: 
    15/1.67/O+
    17/1.75/O-
    18/1.80/B+
    
    Exemplo 2:
    dados: "país", "PIB em bilhões de dólares", "índice Gini"
    resultado: 
    Brasil/10.000/0.706
    EUA/100.000/0.850
    Japão/50.000/0.900
    
    PÁGINA:
    {texto}
    """
    try:
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"Erro ao gerar conteúdo com a IA: {e}"


def perguntar_a_ia_imagem(caminho_imagem: str, vars: str) -> str:
    vars = vars.split("--")
    vars = ", ".join(vars)
    imagem = Image.open(caminho_imagem)
    """Usa a IA Gemini para responder a uma pergunta baseada no texto fornecido."""
    model = genai.GenerativeModel('gemini-2.5-flash-image-preview')

    # Prepara o prompt para a IA
    prompt = f"""
    Analise a imagem a seguir. Use o reconhecimento de imagem.
    com base nela, crie uma tabela e a preencha com os seguintes dados: {vars}. Cada um desses dados deve representar
    uma coluna na tabela. os dados da tabela devem ser separados com uma barra '/'. Não coloque títulos nas colunas
    Se atenha apenas aos dados fornecidos. Extraia todos os dados da página.
    Exemplo 1:
    dados: "idade", "altura", "tipo sanguíneo"
    resultado: 
    15/1.67/O+
    17/1.75/O-
    18/1.80/B+

    Exemplo 2:
    dados: "país", "PIB em bilhões de dólares", "índice Gini"
    resultado: 
    Brasil/10.000/0.706
    EUA/100.000/0.850
    Japão/50.000/0.900
    """

    try:
        resposta = model.generate_content([prompt, imagem])
        return resposta.text
    except Exception as e:
        return f"Erro ao gerar conteúdo com a IA: {e}"

def salvar_planilha(vars, dados) -> None:
    try:
        dados = dados.splitlines()[1:-1]
        print(dados)
        num_linhas = len(dados)
        vars = vars.split("--")[1:]
        print(vars)
        num_cols = len(vars)
        print(f"\n{num_linhas} linhas ne planilha.")
        print(f"\n{num_cols} colunas na planilha.")
        wb = Workbook()
        ws = wb.active
        for i in range(num_cols):
            ws.cell(row=1, column=i+1, value=vars[i])
            for linha in range(num_linhas):
                try:
                    ws.cell(row=linha+2, column=i+1, value=dados[linha].split("/")[i])
                except Exception as e:
                    print(e)
        wb.save(os.path.join(os.getcwd(), "bancos de dados", f"database-{time.strftime("%Y-%m-%d_%H-%M-%S")}.xlsx"))
        print("Dados salvos!")
    except Exception as e:
        print(f"Erro: {e}")

def cat_data(caminhos: list) -> None:
    i = 0
    wb_combinado = Workbook()
    ws = wb_combinado.active
    for caminho in caminhos:
        wb = load_workbook(caminho)
        sh = wb.active
        for linha in sh.iter_rows(values_only=True):
            if i > 0:
                ws.append(linha)
            i += 1
        i = 0
    wb_combinado.save(os.path.join(os.getcwd(), "bancos de dados", f"database-combined-{time.strftime("%Y-%m-%d_%H-%M-%S")}.xlsx"))
    print("Pronto!")

if _name_ == "_main_":
    iniciar()
    op = input("O que deseja fazer?\n1) Extrair dados de um site\n2) Extrair dados de uma imagem\n3) concatenar dados\n")
    if op == "1":
        try:
            url_do_site = input("entre com o site que quer extrair informações: ")
            vars = input("quais variáveis deseja extrair? separe-as com '--'.\n ")
            if not url_do_site.startswith("http://") and not url_do_site.startswith("https://"):
                url_do_site = "https://" + url_do_site
            nome_do_arquivo_pdf = url_do_site.replace("http://", "")
            nome_do_arquivo_pdf = nome_do_arquivo_pdf.replace("https://", "")
            nome_do_arquivo_pdf = nome_do_arquivo_pdf.replace("www.", "")
            nome_do_arquivo_pdf = nome_do_arquivo_pdf.split(".")[0]
            nome_do_arquivo_pdf = nome_do_arquivo_pdf + ".pdf"

            # 1. Converte o site para PDF
            conteudo_do_site = obter_dados_texto(url_do_site)

            # 3. Faz a pergunta à IA com base no texto extraído
            dados = perguntar_a_ia_texto(conteudo_do_site, vars)
            print("\nResposta da IA:\n")
            print(dados)
            salvar_planilha(vars, dados)
        except Exception as e:
            print(f"Erro: {e}")

    if op == "2":
        try:
            caminho_imagem = filedialog.askopenfile(initialdir=os.getcwd(), filetypes=[("Todos", "."), ("PDF", ".pdf"), ("JPG", ".jpg"), ("JPEG", ".jpeg"), ("PNG", ".png")], title="Escolha o arquivo de imagem")
            vars = input("quais variáveis deseja extrair? separe-as com '--'.\n ")
            caminho_imagem = caminho_imagem.name
            dados = perguntar_a_ia_imagem(caminho_imagem, vars)
            print("\nResposta da IA:\n")
            print(dados)
            print(f"caminho da imagem: {caminho_imagem}")
            salvar_planilha(vars, dados)
        except Exception as e:
            print(f"Erro: {e}")

    if op == "3":
        try:
            caminhos = filedialog.askopenfilenames(initialdir=os.getcwd(), title="Escolha os arquivos")
            if caminhos:
                cat_data(caminhos)
            else:
                print("Nenhum arquivo foi selecionado.")
        except Exception as e:
            print(f"Erro: {e}")
