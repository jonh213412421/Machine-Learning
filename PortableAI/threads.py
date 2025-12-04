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

    # Atualizado __init__ para receber temperature em vez de system_prompt
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
        ignore_list = [
            "load_backend:", "build:", "main:", "print_info:", "load:",
            "load_tensors:", "common_init_from_params:", "sampler",
            "generate:", "== Running", "- Press", "- To return",
            "- If you want", "- Not using", "system_info:", "......",
            "repeat_last_n", "dry_multiplier", "top_k",
            "mirostat", "repeat_penalty", "frequency_penalty",
            "You are a helpful assistant", "Hello<|im_end|>", "Hi there", "How are you?"
        ]

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

                if char == '\n':
                    texto_limpo = self.limpar_ansi(text_buffer.strip())
                    text_buffer = ""

                    eh_lixo = False
                    for prefix in ignore_list:
                        if texto_limpo.startswith(prefix):
                            eh_lixo = True
                            break
                    if texto_limpo.startswith("llama_"): eh_lixo = True
                    if texto_limpo in [">", ">>>"]: eh_lixo = True

                    if not eh_lixo and texto_limpo:
                        if texto_limpo.startswith("> "): texto_limpo = texto_limpo[2:]
                        self.linha.emit(texto_limpo, 'bot')

                elif text_buffer.endswith(">") or text_buffer.endswith(">>>"):
                    limpo = self.limpar_ansi(text_buffer).strip()

                    if limpo in [">", ">>>"]:
                        if self.ignorar_primeiro_prompt:
                            self.ignorar_primeiro_prompt = False
                            text_buffer = ""
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

        # Monta o comando com o argumento de temperatura
        cmd = [
            caminho_executavel,
            "-m", caminho_modelo_relativo,
            "--interactive",
            "--conversation",
            "--temp", str(self.temperature)  # Adicionado controle de temperatura
        ]

        # Argumento opcional de experts (se suportado no futuro)
        # if self.n_experts > 0:
        #     cmd.extend(["-ne", str(self.n_experts)])

        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

            self.proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
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
