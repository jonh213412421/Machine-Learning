import subprocess
import os
from tkinter import filedialog
import sys
import PyPDF2

def iniciar() -> None:
    if not os.path.exists(os.path.join(os.getcwd(), 'Llama')) or not os.path.exists(os.path.join(os.getcwd(), 'ícones')):
        return "Erro! Falha na integridade dos diretórios."

    if not os.path.isfile(os.path.join(os.getcwd(), 'Llama', 'llama-run.exe')):
        return "Erro! llama-run.exe não está presente no diretório Llama."

def listar_modelos() -> str:
    return os.listdir("./Llama/Modelos")

def selecionar_modelo(opcao) -> str:
    if opcao == "Adicionar modelo":
        return filedialog.askopenfilename(initialdir="./Llama/Modelos", filetypes=(("model files", "*.gguf"),))

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
    except Exception as e:
        return f"Erro ao carregar o arquivo: {e}"

def fazer_prompt(modelo: str, prompt: str) -> str:
    print("[RODANDO PROMPT]")

    os.chdir(os.path.join(os.getcwd(), "Llama"))

    # Comando final
    cmd = f"llama-run.exe .\\Modelos\\{modelo} -p {prompt}'"

    try:
        resposta = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL, #-> RETORNA NULO PARA QUALQUER INPUT SOLICITADO DO USUÁRIO
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
            encoding="utf-8"
        )
        while True:
            char = resposta.stdout.read(1)

            sys.stdout.write(char)
            sys.stdout.flush()
            yield char

        resposta.stdout.close()
        resposta.wait()
    except Exception as e:
        print(f"Erro ao executar o modelo: {e}")
        return "Erro!"

print(listar_modelos())
# iniciar()
#adicionar_modelo()
#fazer_prompt("iu", "oi")
#modelo = selecionar_modelo()
#modelo = os.path.basename(modelo)
#prompt = "você fala português?"
#fazer_prompt(modelo, prompt)











