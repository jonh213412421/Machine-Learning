import subprocess
import os
import time

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
env["LC_ALL"] = "C.UTF-8"
env["OLLAMA_MODELS"] = os.path.join(os.getcwd(), "Ollama/.ollama")
#O problema é esta porta
env["OLLAMA_HOST"] = "127.0.0.1:55555"

ollama_exe = os.path.join(os.getcwd(), "Ollama", "ollama.exe")


resposta = subprocess.run(
    [ollama_exe, "run", "gemma3", "olá"],
    input="", # stdin vazio se não precisar digitar mais nada
    capture_output=True, # Captura stdout E stderr
    text=True,
    shell=False,
    encoding="utf-8",
    env=env
)

print(resposta.stdout.strip())
