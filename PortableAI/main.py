import subprocess
import os
import time
import tkinter as tk
from tkinter import filedialog
import sys

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
