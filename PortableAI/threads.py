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

    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo
        self.proc = None
        self.thread_running = False
        self.prompt_queue = queue.Queue()
        self.base_dir = os.getcwd()
        self.model_path = os.path.join(self.base_dir, "Llama", "Modelos", self.modelo)
        # Flag inicializada como True para ignorar o '>' que aparece na inicialização do modelo
        self.ignorar_primeiro_prompt = True

    def limpar_ansi(self, txt):
        return re.sub(r'\x1B\[[0-9;]*[mK]', '', txt)

    def enviar_prompt(self, prompt: str):
        self.prompt_queue.put(prompt)

    def _reader_loop(self):
        """
        Lê a saída (stdout) byte a byte para evitar bloqueios em prompts sem 'newline'.
        Usa um buffer de bytes para corrigir a decodificação UTF-8 de caracteres acentuados.
        """
        # Lista de prefixos para ignorar
        ignore_list = [
            "load_backend:", "build:", "main:", "print_info:", "load:",
            "load_tensors:", "common_init_from_params:", "sampler",
            "generate:", "== Running", "- Press", "- To return",
            "- If you want", "- Not using", "system_info:", "......",
            "<|im_start|>", "repeat_last_n", "dry_multiplier", "top_k",
            "mirostat", "repeat_penalty", "frequency_penalty",
            "You are a helpful assistant", "Hello<|im_end|>", "Hi there", "How are you?"
        ]

        # Buffer de texto (acumula caracteres até formar uma linha ou prompt)
        text_buffer = ""
        # Buffer de bytes (acumula bytes até formar um caractere UTF-8 válido)
        byte_buffer = bytearray()

        while self.thread_running and self.proc:
            try:
                # 1. Lê 1 byte bruto
                byte = self.proc.stdout.read(1)

                if not byte:
                    if self.proc.poll() is not None:
                        break
                    time.sleep(0.01)
                    continue

                # 2. Adiciona ao buffer de bytes
                byte_buffer.extend(byte)

                # 3. Tenta descodificar os bytes acumulados
                try:
                    char = byte_buffer.decode("utf-8")
                    # Se funcionou, limpamos o buffer de bytes e processamos o caractere
                    byte_buffer.clear()
                except UnicodeDecodeError:
                    # Se falhou, é porque o caractere está incompleto (ex: 1º byte de um 'ã').
                    # Continuamos o loop para ler o próximo byte e juntar.
                    continue

                # 4. Adiciona o caractere decodificado ao buffer de texto
                text_buffer += char

                # 5. Se encontrou quebra de linha, processa a mensagem
                if char == '\n':
                    texto_limpo = self.limpar_ansi(text_buffer.strip())
                    text_buffer = ""  # Limpa o buffer de texto

                    # Filtros de lixo
                    eh_lixo = False
                    for prefix in ignore_list:
                        if texto_limpo.startswith(prefix):
                            eh_lixo = True
                            break
                    if texto_limpo.startswith("llama_"): eh_lixo = True
                    # Ignora linhas vazias ou contendo apenas o prompt isolado no meio do fluxo
                    if texto_limpo in [">", ">>>"]: eh_lixo = True

                    if not eh_lixo and texto_limpo:
                        if texto_limpo.startswith("> "): texto_limpo = texto_limpo[2:]
                        self.linha.emit(texto_limpo, 'bot')

                # 6. Detecção do sinal de fim (PROMPT) sem quebra de linha
                # Verifica se o buffer termina com os marcadores conhecidos
                elif text_buffer.endswith(">") or text_buffer.endswith(">>>"):
                    # Verificação rigorosa: o buffer deve conter APENAS o prompt
                    limpo = self.limpar_ansi(text_buffer).strip()

                    if limpo in [">", ">>>"]:
                        # LÓGICA DE CORREÇÃO DO BOTÃO:
                        # Se for o primeiro '>' (startup), ignoramos para não resetar o botão antes da hora.
                        if self.ignorar_primeiro_prompt:
                            self.ignorar_primeiro_prompt = False
                            # Limpamos o buffer para não processar este '>' como texto
                            text_buffer = ""
                        else:
                            # Caso contrário, é o fim real da resposta.
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
            "--conversation"
        ]

        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

            self.proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,  # Modo binário (crucial para o byte_buffer funcionar)
                bufsize=0,  # Sem buffer do SO
                cwd=pasta_llama,
                creationflags=flags
            )

            reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
            reader_thread.start()

            while self.thread_running:
                try:
                    prompt = self.prompt_queue.get(timeout=0.5)
                    self.linha.emit(prompt, 'user')

                    # REMOVIDO: self.ignorar_primeiro_prompt = True
                    # Não devemos ignorar o prompt de retorno após enviar uma mensagem,
                    # apenas o prompt inicial de startup (tratado no __init__).

                    if self.proc and self.proc.stdin:
                        # Codifica para bytes antes de enviar
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
