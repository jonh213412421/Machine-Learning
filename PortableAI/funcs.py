import subprocess
import os
from tkinter import filedialog
import sys
import PyPDF2
from langdetect import detect
import spacy


def iniciar() -> str:


   if not os.path.exists(os.path.join(os.getcwd(), 'Llama')) or not os.path.exists(os.path.join(os.getcwd(), 'ícones')):
       return "Erro! Falha na integridade dos diretórios."


   if not os.path.isfile(os.path.join(os.getcwd(), 'Llama', 'llama-run.exe')):
       return "Erro! llama-run.exe não está presente no diretório Llama."


   if not os.path.exists(os.path.join(os.getcwd(), 'data')):
       os.mkdir(os.path.join(os.getcwd(), 'data'))
       return "Erro! diretório 'Data' não está presente"


def listar_modelos() -> str:
   return os.listdir("./Llama/Modelos")


def selecionar_modelo(opcao) -> str:
   if opcao == "Adicionar modelo":
       return filedialog.askopenfilename(initialdir="./Llama/Modelos", filetypes=(("model files", "*.gguf"),))
   else:
       print(f"Modelo selecionado: {opcao}")
       return f"Modelo selecionado: {opcao}"


def carregar_arquivo() -> ((str, str)):
   try:
       caminho = filedialog.askopenfilename(initialdir=os.getcwd(), filetypes=(("pdf", "*.pdf"), ("text files", "*.txt"),))
       if caminho:
           if caminho.endswith(".pdf"):
               with open(caminho, "rb") as arquivo:
                   pdf = PyPDF2.PdfReader(arquivo)
                   texto = ""
                   for pagina in pdf.pages:
                       texto += pagina.extract_text() + "\n"
               print(texto)
               return os.path.basename(caminho), texto


           if caminho.endswith(".txt"):
               with open(caminho, "r") as arquivo:
                   texto = arquivo.read()
               print(texto)
               return os.path.basename(caminho), texto


           else:
               return "", "Tipo inválido de arquivo"
       else:
           return "", "Tipo inválido de arquivo"


   except Exception as e:
       return "--", f"Erro ao carregar o arquivo: {e}"


def fazer_prompt(modelo: str, prompt: str) -> str:
   print("[RODANDO PROMPT]")


   dir_inicial = os.getcwd()
   os.chdir(os.path.join(dir_inicial, "Llama"))


   # Comando final
   cmd = f"llama-run.exe .\\Modelos\\{modelo} -p {prompt}'"


   try:
       with subprocess.Popen(
           cmd,
           stdin=subprocess.DEVNULL,
           stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT,
           shell=True,
           text=True,
           encoding="utf-8",
           bufsize=1
       ) as proc:
           for linha in proc.stdout:
               yield linha  # envia linha por linha
       proc.wait()


   except Exception as e:
       yield f"\nErro ao executar o modelo: {e}\n"


   finally:
       os.chdir(dir_inicial)


def extrair_palavras_chave(prompt: str) -> list:
   try:
       if detect(prompt) == "pt":
           nlp = spacy.load("pt_core_news_sm")
           meta = nlp(prompt)
       else:
           nlp = spacy.load("en_core_web_sm")
           meta = nlp(prompt)
       palavras_filtradas = [token.text for token in meta if token.pos_ in ["NOUN", "ADJ", "ADV", "PRON", "PROPN"]]
       return palavras_filtradas


   except Exception as e:
       print(f"Erro ao extrair palavras chave: {e}")


extrair_palavras_chave("quem foi napoleão bonaparte?")
# iniciar()
#adicionar_modelo()
#fazer_prompt("iu", "oi")
#modelo = selecionar_modelo()
#modelo = os.path.basename(modelo)
#prompt = "você fala português?"
#fazer_prompt(modelo, prompt)

