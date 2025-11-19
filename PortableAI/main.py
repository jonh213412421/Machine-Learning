import subprocess
import os
import time
import tkinter as tk
from tkinter import filedialog
import sys

def iniciar() -> None:
    try:
        if not os.path.exists(os.path.join(os.getcwd(), "data")):
            os.mkdir(os.path.join(os.getcwd(), "data"))

        if not os.path.isfile(os.path.join(os.getcwd(), "data", "paths.txt")):
            with open(os.path.join(os.getcwd(), "data", "paths.txt"), "w") as arquivo:
                arquivo.write("modelos:\n\n")

    except Exception as e:
        print(f"Erro ao iniciar: {e}")


def adicionar_modelo() -> None:
    try:
        if not os.path.isdir(os.path.join(os.getcwd(), "data")):
            os.mkdir(os.path.join(os.getcwd(), "data"))
            modelo_path = filedialog.askopenfilename(initialdir="./Llama/Modelos", filetypes=(("model files", "*.gguf"),))
            modelo_nome = os.path.basename(modelo_path)
            if not os.path.isfile(os.path.join(os.getcwd(), "data", "paths.txt")):
                with open(os.path.join(os.getcwd(), "data", "paths.txt"), "w") as arquivo:
                    arquivo.write("modelos:\n\n")
                    arquivo.write(f"md->{modelo_nome}:")
                    arquivo.write("\n")
                    arquivo.write(modelo_path)
                    arquivo.write("\n")

        else:
            modelo_path = filedialog.askopenfilename()
            modelo_nome = os.path.basename(modelo_path)
            with open(os.path.join(os.getcwd(), "data", "paths.txt"), "r") as arquivo:
                linhas = arquivo.readlines()
                for linha in linhas:
                    print(linha)
                    if linha.startswith(modelo_nome):
                        return None
            with open(os.path.join(os.getcwd(), "data", "paths.txt"), "a") as arquivo:
                arquivo.write(f"md->{modelo_nome}:")
                arquivo.write("\n")
                arquivo.write(modelo_path)
                arquivo.write("\n")

    except Exception as e:
        print(f"Erro ao adicionar modelo: {e}")

def selecionar_modelo() -> str:
    return filedialog.askopenfilename(initialdir="./Llama/Modelos", filetypes=(("model files", "*.gguf"),))


def fazer_prompt(modelo: str, prompt: str) -> None:
    print("[RODANDO PROMPT]")

    os.chdir(os.path.join(os.getcwd(), "Llama"))

    # Comando final
    cmd = f"llama-run.exe .\\Modelos\\{modelo} -p {prompt}'"

    try:
        subprocess.run(cmd,
                       stdin=subprocess.DEVNULL,  # -> SE PEDIR QUALQUER INTERVENÇÃO DO USUÁRIO, ELE CANCELA!!
                       stdout=sys.stdout,
                       stderr=sys.stdout,
                       encoding="utf-8",
                       shell=True,
                       text=True)
    except Exception as e:
        print(f"Erro ao executar o modelo: {e}")


# iniciar()
#adicionar_modelo()
#fazer_prompt("iu", "oi")
modelo = selecionar_modelo()
modelo = os.path.basename(modelo)
prompt = "você fala português?"
fazer_prompt(modelo, prompt)











