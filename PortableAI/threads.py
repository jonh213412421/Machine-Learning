import os
import re
import queue
import subprocess
import threading
from PyQt6.QtCore import QThread, pyqtSignal
import time
import sys
import funcs


class PromptThread(QThread):
    linha = pyqtSignal(str, str)  # texto, remetente ('user' ou 'bot')
    erro = pyqtSignal(str)
    botao_prompt = pyqtSignal(bool)
    sinal_resposta_finalizada = pyqtSignal()

    def __init__(self, modelo, temperature=0.7, n_experts=0):
        super().__init__()
        self.modelo = modelo
        self.temperature = temperature
        self.n_experts = n_experts

        self.proc = None
        self.thread_running = False
        self.prompt_queue = queue.Queue()
        self.base_dir = os.getcwd()
        self.model_path = os.path.join(self.base_dir, "Llama", "Modelos", self.modelo)
        self.ignorar_primeiro_prompt = True

    def limpar_ansi(self, txt):
        txt = re.sub(r'\x1B\[[0-9;]*[mK]', '', txt)
        txt = re.sub(r'<\|.*?\|>', '', txt)
        return txt

    def enviar_prompt(self, prompt: str):
        self.prompt_queue.put(prompt)

    def _reader_loop(self):
        text_buffer = ""
        byte_buffer = bytearray()

        while self.thread_running and self.proc:
            try:
                byte = self.proc.stdout.read(1)

                if not byte:
                    if self.proc.poll() is not None:
                        break
                    time.sleep(0.01)
                    continue

                byte_buffer.extend(byte)

                try:
                    char = byte_buffer.decode("utf-8")
                    byte_buffer.clear()
                except UnicodeDecodeError:
                    continue

                text_buffer += char

                # 1. Emissão por quebra de linha ou limite de caracteres
                if char == '\n' or len(text_buffer) >= 50:
                    # Limpa apenas códigos ANSI, mas MANTÉM espaços e quebras de linha (\n)
                    texto_raw = self.limpar_ansi(text_buffer)

                    # Cria versão limpa apenas para verificação de lixo
                    texto_check = texto_raw.strip()

                    eh_lixo = False
                    # Se for apenas o prompt do sistema, marca como lixo
                    if texto_check in [">", ">>>"]:
                        eh_lixo = True

                    if not eh_lixo:
                        # Se detectar vazamento de prompt (ex: "> Olá"), limpa apenas o início
                        if texto_check.startswith("> "):
                            texto_raw = re.sub(r'^\s*> ', '', texto_raw, count=1)

                        # IMPORTANTE: Emite o texto RAW (com espaços e \n) para a interface
                        # Isso garante que a formatação do bot não seja perdida
                        self.linha.emit(texto_raw, 'bot')

                    text_buffer = ""

                # 2. Detecção robusta de Fim de Turno (Prompt)
                elif text_buffer.endswith(">") or text_buffer.endswith("> ") or \
                        text_buffer.endswith(">>>") or text_buffer.endswith(">>> "):

                    # Verifica se realmente é o prompt final
                    limpo = self.limpar_ansi(text_buffer)
                    match_prompt = re.search(r'(>|>>>)\s*$', limpo)

                    if match_prompt:
                        conteudo = limpo[:match_prompt.start()]

                        # Se sobrou texto válido antes do prompt, emite agora
                        if conteudo:
                            self.linha.emit(conteudo, 'bot')

                        if self.ignorar_primeiro_prompt:
                            self.ignorar_primeiro_prompt = False
                        else:
                            self.sinal_resposta_finalizada.emit()

                        text_buffer = ""

            except Exception as e:
                print(f"Erro leitura: {e}")
                break

    def run(self):
        self.thread_running = True

        pasta_llama = os.path.join(self.base_dir, "Llama")
        caminho_executavel = os.path.join(pasta_llama, "llama-cli.exe")

        if not os.path.exists(caminho_executavel):
            self.erro.emit(f"Executável não encontrado:\n{caminho_executavel}")
            self.thread_running = False
            return

        if not os.path.exists(self.model_path):
            self.erro.emit(f"Modelo não encontrado:\n{self.model_path}")
            self.thread_running = False
            return

        try:
            caminho_modelo_relativo = os.path.relpath(self.model_path, pasta_llama)
        except ValueError:
            caminho_modelo_relativo = self.model_path

        cmd = [
            caminho_executavel,
            "-m", caminho_modelo_relativo,
            "--interactive",
            "--conversation",
            "--temp", str(self.temperature),
            "--no-display-prompt"
        ]

        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

            self.proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=False,
                bufsize=0,
                cwd=pasta_llama,
                creationflags=flags
            )

            reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
            reader_thread.start()

            while self.thread_running:
                try:
                    prompt = self.prompt_queue.get(timeout=0.5)
                    self.linha.emit(prompt, 'user')

                    if self.proc and self.proc.stdin:
                        bytes_prompt = (prompt + "\n").encode("utf-8")
                        self.proc.stdin.write(bytes_prompt)
                        self.proc.stdin.flush()

                except queue.Empty:
                    continue
                except Exception as e:
                    self.erro.emit(f"Erro envio: {e}")

        except Exception as e:
            self.erro.emit(f"Falha ao iniciar modelo: {str(e)}")
        finally:
            self.thread_running = False
            if self.proc:
                try:
                    self.proc.terminate()
                except:
                    pass

    def stop_thread(self):
        self.thread_running = False
        if self.proc:
            try:
                self.proc.terminate()
            except:
                pass


class CarregarArquivoThread(QThread):
    status = pyqtSignal(str)
    nome_arquivo = pyqtSignal(str)
    dados_arquivo = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.thread_running = False

    def run(self):
        self.thread_running = True
        try:
            aux1, aux2 = funcs.carregar_arquivo()
            self.nome_arquivo.emit(aux1)
            self.dados_arquivo.emit(aux2)
        except Exception as e:
            self.status.emit(str(e))
        finally:
            self.thread_running = False
