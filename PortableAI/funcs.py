import subprocess
import os
import time
import tkinter as tk
from tkinter import filedialog
import sys

def listar_modelos() -> str:
    return os.listdir("./Llama/Modelos")

def selecionar_modelo(opcao) -> str:
    if opcao == "Adicionar modelo":
        return filedialog.askopenfilename(initialdir="./Llama/Modelos", filetypes=(("model files", "*.gguf"),))

def carregar_arquivo() -> str:
    return filedialog.askopenfilename(initialdir=os.getcwd(), filetypes=(("pdf", "*.pdf"), ("text files", "*.txt"),))

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
        for line in iter(resposta.stdout.readline, ''):
            sys.stdout.write(line)  # envia para o terminal
            sys.stdout.flush()  # garante que aparece imediatamente
            yield line.rstrip()

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











