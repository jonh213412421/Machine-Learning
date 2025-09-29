import os
import time
import google.generativeai as genai
from openpyxl.workbook import Workbook
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from openpyxl import workbook
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuração da chave de API da Gemini
genai.configure(api_key="AIzaSyBCPEMihVWyBYAifjxHCB3cOXR5-IoaYCs")
WEBDRIVER = os.path.join(os.getcwd(), "webdriver", "msedgedriver.exe")

def iniciar():
    if not os.path.exists(os.path.join(os.getcwd(), "webdriver", "msedgedriver.exe")):
        print("Erro: Edge Driver não foi localizado. Ele deve estar localizado na pasta 'webdriver'")
    if not os.path.exists(os.path.join(os.getcwd(), "bancos de dados")):
        os.mkdir(os.path.join(os.getcwd(), "bancos de dados"))

def converter_site_para_pdf(url_site, nome_arquivo_pdf):
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


def perguntar_a_ia(texto: str, vars: str) -> str:
    vars = vars.split("--")
    vars = "\n".join(vars)
    """Usa a IA Gemini para responder a uma pergunta baseada no texto fornecido."""
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Prepara o prompt para a IA
    prompt = f"""
    Analise a página seguir.
    com base nela, crie uma tabela e a preencha com os seguintes dados: {vars}. Cada um desses dados deve representar
    uma coluna na tabela. os dados da tabela devem ser separados com um espaço simples. Não coloque títulos nas colunas
    Se atenha apenas aos dados fornecidos. Extraia todos os dados da página.
    Exemplo 1:
    dados: "idade", "altura", "tipo sanguíneo"
    resultado: 
    15 1.67 O+
    17 1.75 O-
    18 1.80 B+
    
    Exemplo 2:
    dados: "país", "PIB em bilhões de dólares", "índice Gini"
    resultado: 
    Brasil 10.000 0.706
    EUA 100.000 0.850
    Japão 50.000 0.900
    
    PÁGINA:
    {texto}
    """
    try:
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"Erro ao gerar conteúdo com a IA: {e}"

def salvar_planilha(vars, dados):
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
                ws.cell(row=linha+2, column=i+1, value=dados[linha].split(" ")[i])
            except IndexError:
                print(IndexError)
    wb.save(os.path.join(os.getcwd(), "planilha.xlsx"))

if _name_ == "_main_":
    iniciar()
    url_do_site = input("entre com o site que quer extrair informações: ")
    vars = input("quais variáveis deseja extrair? separe-as com '--'.\n ")
    #if not "http://" in url_do_site or not "https://" in url_do_site:
    #    url_do_site = "https://" + url_do_site
    nome_do_arquivo_pdf = url_do_site.replace("http://", "")
    nome_do_arquivo_pdf = nome_do_arquivo_pdf.replace("https://", "")
    nome_do_arquivo_pdf = nome_do_arquivo_pdf.replace("www.", "")
    nome_do_arquivo_pdf = nome_do_arquivo_pdf.split(".")[0]
    nome_do_arquivo_pdf = nome_do_arquivo_pdf + ".pdf"

    # 1. Converte o site para PDF
    conteudo_do_site = converter_site_para_pdf(url_do_site, nome_do_arquivo_pdf)

    # 3. Faz a pergunta à IA com base no texto extraído
    dados = perguntar_a_ia(conteudo_do_site, vars)
    print("\nResposta da IA:\n")
    print(dados)
    salvar_planilha(vars, dados)
