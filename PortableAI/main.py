import subprocess
import os

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
env["LC_ALL"] = "C.UTF-8"

resposta = subprocess.Popen([r".\Ollama\ollama.exe", "run", "gemma3", "olá"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True, encoding="utf-8", env=env)
output, error = resposta.communicate()
print("Ollama Output:", output.strip())
