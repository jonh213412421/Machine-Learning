# -*- coding: utf-8 -*-


import sys
import os
import subprocess
import threading
import numpy as np
import hashlib
from scipy.io import wavfile
from scipy.fft import fft, fftfreq


# --- NOVOS IMPORTS PARA CRIPTOGRAFIA E MANIPULAÇÃO DE ÁUDIO ---
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


from PyQt6.QtWidgets import (
   QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
   QPushButton, QLabel, QTextEdit, QLineEdit, QFileDialog, QMessageBox,
   QDialog
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread


# ==============================================================================
# CONSTANTES E MAPEAMENTO DE SÍMBOLOS
# ==============================================================================


# ALTURA_SENOIDE: Aumentada para criar um sinal mais robusto e detectável.
ALTURA_SENOIDE = 0.01
# DURACAO: Aumentada para melhorar a precisão da decodificação do FFT.
DURACAO = 0.1
FREQUENCIA_AMOSTRAS = 8000
# MAGNITUDE_THRESHOLD: Filtro de ruído. Ignora picos de frequência fracos.
# Este valor pode precisar de ajuste dependendo do ruído de fundo.
MAGNITUDE_THRESHOLD = 50000


# Mapeamento binário -> frequência
frequencia_inicial = 200
frequencia_final = 4000
alfabeto = [format(c, '08b') for c in range(256)]
passo = (frequencia_final - frequencia_inicial) / (len(alfabeto) - 1)
mapeamento_de_simbolos = {
   letra: frequencia_inicial + i * passo for i, letra in enumerate(alfabeto)
}
# Criamos um mapa reverso para facilitar a decodificação
mapeamento_reverso = {v: k for k, v in mapeamento_de_simbolos.items()}


# --- Caminho para o FFMPEG ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_EXE = os.path.join(BASE_DIR, 'ffmpeg', 'bin', 'ffmpeg.exe')
FFPROBE_EXE = os.path.join(BASE_DIR, 'ffmpeg', 'bin', 'ffprobe.exe')


# --- Estilo da Aplicação (QSS) ---
STYLESHEET = """
QWidget {
   background-color: #2E3440;
   color: #D8DEE9;
   font-family: "Segoe UI", Arial, sans-serif;
   font-size: 14px;
}
QMainWindow, QDialog {
   background-color: #2E3440;
}
QLabel#welcomeLabel {
   font-size: 28px;
   font-weight: bold;
   color: #88C0D0;
}
QLabel#statusLabel {
   color: #A3BE8C;
}
QPushButton {
   background-color: #5E81AC;
   color: #ECEFF4;
   border: none;
   padding: 10px 20px;
   border-radius: 5px;
   font-size: 16px;
}
QPushButton:hover {
   background-color: #81A1C1;
}
QPushButton:pressed {
   background-color: #4C566A;
}
QLineEdit, QTextEdit {
   background-color: #3B4252;
   border: 1px solid #4C566A;
   border-radius: 4px;
   padding: 8px;
   color: #ECEFF4;
}
"""




# ==============================================================================
# FUNÇÃO PARA GERAR A CHAVE AES A PARTIR DO ÁUDIO
# ==============================================================================
def get_aes_key_from_audio(mp3_path):
   """
   Deriva uma chave AES de 32 bytes a partir dos 5 segundos do meio de um arquivo MP3.
   Usa SHA-256 para garantir um tamanho de chave fixo e seguro.


   Esta versão usa o ffprobe e scipy, eliminando a dependência do pydub.
   """
   temp_wav_path = os.path.join(BASE_DIR, "temp_key_audio.wav")
   try:
       # Primeiro, use o ffprobe para obter a duração do áudio
       # Melhoria: Captura a saída completa e verifica o código de retorno para melhor depuração.
       probe_command = [FFPROBE_EXE, '-i', mp3_path, '-show_entries', 'format=duration', '-v', 'quiet', '-of',
                        'csv=p=0']


       probe_result = subprocess.run(probe_command, capture_output=True, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)


       if probe_result.returncode != 0:
           raise RuntimeError(
               f"Erro no FFprobe. Verifique o arquivo MP3 e se o FFprobe está acessível.\nErro: {probe_result.stderr}")


       duration_str = probe_result.stdout.strip()


       if not duration_str:
           raise RuntimeError("Não foi possível obter a duração do arquivo de áudio. A saída do FFprobe estava vazia.")


       duration = float(duration_str)
       if duration < 5:
           raise ValueError("O arquivo de áudio é muito curto para gerar uma chave (menos de 5 segundos).")


       # Calcule o tempo de início e duração para o segmento do meio (5 segundos)
       start_time = max(0, (duration / 2) - 2.5)


       # Use o ffmpeg para extrair e converter o segmento de 5 segundos para um arquivo WAV temporário
       extract_command = [
           FFMPEG_EXE, '-y',
           '-ss', str(start_time),
           '-i', mp3_path,
           '-t', '5',
           '-ar', str(FREQUENCIA_AMOSTRAS),  # Garante a mesma taxa de amostragem
           '-acodec', 'pcm_s16le',
           temp_wav_path
       ]
       result = subprocess.run(extract_command, capture_output=True, text=True,
                               creationflags=subprocess.CREATE_NO_WINDOW)
       if result.returncode != 0:
           raise RuntimeError(f"Erro no FFMPEG ao extrair o áudio para a chave: {result.stderr}")


       # Leia o áudio WAV com scipy
       rate, audio_data = wavfile.read(temp_wav_path)


       # Obtém os bytes do áudio para o hash
       audio_bytes = audio_data.tobytes()


       # Cria um hash SHA-256 para uma chave de 32 bytes (256 bits)
       key_hash = hashlib.sha256(audio_bytes).digest()


       return key_hash


   except Exception as e:
       raise RuntimeError(f"Erro ao gerar a chave de criptografia: {str(e)}")
   finally:
       if os.path.exists(temp_wav_path):
           os.remove(temp_wav_path)




# ==============================================================================
# WORKER THREADS PARA EVITAR TRAVAMENTO DA GUI
# ==============================================================================


class WorkerSignals(QObject):
   finished = pyqtSignal()
   error = pyqtSignal(str)
   success = pyqtSignal(str)
   progress = pyqtSignal(str)




class EncryptWorker(QObject):
   def __init__(self, text, mp3_path, output_path):
       super().__init__()
       self.signals = WorkerSignals()
       self.text = text
       self.mp3_path = mp3_path
       self.output_path = output_path
       self.temp_wav_path = os.path.join(BASE_DIR, "temp_data.wav")


   def run(self):
       try:
           self.signals.progress.emit("Gerando chave AES a partir do áudio...")
           aes_key = get_aes_key_from_audio(self.mp3_path)


           self.signals.progress.emit("Criptografando mensagem...")
           encrypted_data = self._encrypt_text_with_aes(self.text, aes_key)


           self.signals.progress.emit("Gerando arquivo WAV a partir dos dados criptografados...")
           self._generate_wav_from_bytes(encrypted_data, self.temp_wav_path)


           self.signals.progress.emit("Combinando áudios com FFMPEG...")
           self._combine_audio(self.temp_wav_path, self.mp3_path, self.output_path)


           if os.path.exists(self.temp_wav_path):
               os.remove(self.temp_wav_path)


           self.signals.success.emit(f"Arquivo '{os.path.basename(self.output_path)}' criado com sucesso!")
       except Exception as e:
           if os.path.exists(self.temp_wav_path):
               os.remove(self.temp_wav_path)
           self.signals.error.emit(f"Ocorreu um erro: {str(e)}")
       finally:
           self.signals.finished.emit()


   def _encrypt_text_with_aes(self, text, key):
       """
       Criptografa o texto usando AES.
       """
       # A AES exige que a chave e os dados sejam bytes, por isso, codificamos o texto.
       data = text.encode('utf-8')
       cipher = AES.new(key, AES.MODE_ECB)
       # Pad garante que o tamanho dos dados seja um múltiplo do tamanho do bloco (16 bytes)
       padded_data = pad(data, AES.block_size)
       return cipher.encrypt(padded_data)


   def _generate_wav_from_bytes(self, byte_data, output_filename):
       # A amplitude é baseada na constante fornecida
       amplitude = np.iinfo(np.int16).max * ALTURA_SENOIDE


       # Gera a base de tempo para um único caractere
       t = np.linspace(0., DURACAO, int(FREQUENCIA_AMOSTRAS * DURACAO), endpoint=False)


       signal = np.array([], dtype=np.int16)


       # Para cada byte nos dados, encontra a frequência e gera a onda
       for byte_value in byte_data:
           binary_byte = format(byte_value, '08b')
           if binary_byte in mapeamento_de_simbolos:
               freq = mapeamento_de_simbolos[binary_byte]
               wave_segment = amplitude * np.sin(2. * np.pi * freq * t)
               signal = np.append(signal, wave_segment)


       if len(signal) == 0:
           raise ValueError("Os dados criptografados não produziram nenhum sinal de áudio.")


       wavfile.write(output_filename, FREQUENCIA_AMOSTRAS, signal.astype(np.int16))


   def _combine_audio(self, wav_path, mp3_path, output_path):
       command = [
           FFMPEG_EXE, '-y',
           '-i', wav_path,
           '-stream_loop', '-1', '-i', mp3_path,
           '-map', '1:a:0', '-map', '0:a:0',
           '-c:a', 'aac', '-b:a', '192k',
           '-shortest', output_path
       ]
       result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
       if result.returncode != 0:
           raise RuntimeError(f"Erro no FFMPEG: {result.stderr}")




class DecryptWorker(QObject):
   def __init__(self, mp4_path, mp3_path):
       super().__init__()
       self.signals = WorkerSignals()
       self.mp4_path = mp4_path
       self.mp3_path = mp3_path
       self.extracted_wav_path = os.path.join(BASE_DIR, "extracted_data.wav")


   def run(self):
       try:
           self.signals.progress.emit("Extraindo faixa de dados do arquivo MP4...")
           self._extract_hidden_track(self.mp4_path, self.extracted_wav_path)


           self.signals.progress.emit("Analisando áudio e recuperando dados criptografados...")
           encrypted_bytes = self._recover_bytes_from_wav(self.extracted_wav_path)


           self.signals.progress.emit("Gerando chave AES a partir do MP3 original...")
           aes_key = get_aes_key_from_audio(self.mp3_path)


           self.signals.progress.emit("Descriptografando a mensagem...")
           original_text = self._decrypt_bytes_with_aes(encrypted_bytes, aes_key)


           if os.path.exists(self.extracted_wav_path):
               os.remove(self.extracted_wav_path)


           self.signals.success.emit(original_text)
       except Exception as e:
           if os.path.exists(self.extracted_wav_path):
               os.remove(self.extracted_wav_path)
           self.signals.error.emit(f"Ocorreu um erro: {str(e)}")
       finally:
           self.signals.finished.emit()


   def _decrypt_bytes_with_aes(self, ciphertext, key):
       """
       Descriptografa os dados usando AES.
       """
       cipher = AES.new(key, AES.MODE_ECB)
       decrypted_padded = cipher.decrypt(ciphertext)
       return unpad(decrypted_padded, AES.block_size).decode('utf-8')


   def _extract_hidden_track(self, mp4_path, output_wav_path):
       command = [
           FFMPEG_EXE, '-y',
           '-i', mp4_path,
           '-map', '0:a:1',
           '-acodec', 'pcm_s16le',
           '-ar', str(FREQUENCIA_AMOSTRAS),  # Garante a mesma taxa de amostragem
           output_wav_path
       ]
       result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
       if result.returncode != 0:
           raise RuntimeError(f"Erro no FFMPEG ao extrair áudio: {result.stderr}")


   def _recover_bytes_from_wav(self, wav_path):
       rate, data = wavfile.read(wav_path)
       if rate != FREQUENCIA_AMOSTRAS:
           raise ValueError(f"Taxa de amostragem incorreta! Esperado {FREQUENCIA_AMOSTRAS}, obtido {rate}")


       samples_per_char = int(DURACAO * rate)
       num_chunks = len(data) // samples_per_char


       recovered_bytes = bytearray()


       for i in range(num_chunks):
           chunk = data[i * samples_per_char: (i + 1) * samples_per_char]


           # FFT para encontrar a frequência dominante
           yf = fft(chunk)
           xf = fftfreq(len(chunk), 1 / rate)


           # Pega a frequência correspondente à maior amplitude no espectro positivo
           idx = np.argmax(np.abs(yf[:len(chunk) // 2]))


           # Aplica o filtro de ruído (Threshold)
           if np.abs(yf[idx]) < MAGNITUDE_THRESHOLD:
               continue  # Ignora este chunk por ser considerado ruído/silêncio


           detected_freq = abs(xf[idx])


           # Encontra o símbolo mais próximo da frequência detectada
           closest_freq = min(mapeamento_reverso.keys(), key=lambda f: abs(f - detected_freq))
           binary_char = mapeamento_reverso[closest_freq]


           # Converte o binário para um valor de byte
           byte_value = int(binary_char, 2)
           recovered_bytes.append(byte_value)


       return bytes(recovered_bytes)




# ==============================================================================
# JANELAS DA INTERFACE GRÁFICA (GUI)
# ==============================================================================


class ResultDialog(QDialog):
   def __init__(self, text, parent=None):
       super().__init__(parent)
       self.setWindowTitle("Mensagem Recuperada")
       self.setMinimumSize(600, 400)


       layout = QVBoxLayout(self)
       label = QLabel("A mensagem recuperada do arquivo é:")
       layout.addWidget(label)


       self.text_display = QTextEdit()
       self.text_display.setReadOnly(True)
       self.text_display.setText(text)
       layout.addWidget(self.text_display)


       close_button = QPushButton("Fechar")
       close_button.clicked.connect(self.accept)
       layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)
       self.setLayout(layout)




class EncryptWindow(QWidget):
   def __init__(self):
       super().__init__()
       self.setWindowTitle("Criptografar Mensagem")
       self.setMinimumSize(600, 500)


       layout = QVBoxLayout(self);
       layout.setSpacing(15)
       self.msg_input = QTextEdit();
       self.msg_input.setPlaceholderText("Sua mensagem secreta aqui...")
       self.mp3_path_input = QLineEdit();
       self.mp3_path_input.setReadOnly(True)
       self.mp3_select_button = QPushButton("Procurar MP3...");
       self.mp3_select_button.clicked.connect(self.select_mp3)
       mp3_layout = QHBoxLayout();
       mp3_layout.addWidget(self.mp3_path_input);
       mp3_layout.addWidget(self.mp3_select_button)
       self.encrypt_button = QPushButton("Criptografar e Gerar MP4");
       self.encrypt_button.clicked.connect(self.start_process)
       self.status_label = QLabel("");
       self.status_label.setObjectName("statusLabel")


       layout.addWidget(QLabel("Digite a mensagem a ser escondida:"))
       layout.addWidget(self.msg_input)
       layout.addWidget(QLabel("Selecione o arquivo de áudio MP3 para disfarce:"))
       layout.addLayout(mp3_layout)
       layout.addStretch()
       layout.addWidget(self.status_label)
       layout.addWidget(self.encrypt_button)
       self.setLayout(layout)


   def select_mp3(self):
       file_name, _ = QFileDialog.getOpenFileName(self, "Selecionar MP3", "", "Arquivos MP3 (*.mp3)")
       if file_name: self.mp3_path_input.setText(file_name)


   def start_process(self):
       text, mp3_path = self.msg_input.toPlainText(), self.mp3_path_input.text()
       if not text: QMessageBox.warning(self, "Aviso", "Por favor, digite uma mensagem."); return
       if not mp3_path: QMessageBox.warning(self, "Aviso", "Por favor, selecione um arquivo MP3."); return
       if not os.path.exists(FFMPEG_EXE): QMessageBox.critical(self, "Erro Crítico",
                                                               f"FFMPEG não encontrado em:\n{FFMPEG_EXE}"); return


       output_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo MP4", "", "Arquivos MP4 (*.mp4)")
       if not output_path: return


       self.encrypt_button.setEnabled(False);
       self.status_label.setText("Iniciando processo...")
       self.thread, self.worker = QThread(), EncryptWorker(text, mp3_path, output_path)
       self.worker.moveToThread(self.thread)
       self.thread.started.connect(self.worker.run)
       self.worker.signals.finished.connect(self.thread.quit);
       self.worker.signals.finished.connect(self.worker.deleteLater)
       self.thread.finished.connect(self.thread.deleteLater)
       self.worker.signals.progress.connect(lambda msg: self.status_label.setText(msg))
       self.worker.signals.error.connect(self.process_error)
       self.worker.signals.success.connect(self.process_success)
       self.thread.start()


   def process_finished(self):
       self.encrypt_button.setEnabled(True);
       self.status_label.setText("")


   def process_error(self, err):
       self.process_finished();
       QMessageBox.critical(self, "Erro", err)


   def process_success(self, msg):
       self.process_finished();
       QMessageBox.information(self, "Sucesso", msg);
       self.close()




class DecryptWindow(QWidget):
   def __init__(self):
       super().__init__()
       self.setWindowTitle("Descriptografar Mensagem")
       self.setMinimumSize(600, 300)


       layout = QVBoxLayout(self);
       layout.setSpacing(15)
       self.mp4_path_input = QLineEdit();
       self.mp4_path_input.setReadOnly(True)
       self.mp4_select_button = QPushButton("Procurar MP4...");
       self.mp4_select_button.clicked.connect(self.select_mp4)
       mp4_layout = QHBoxLayout();
       mp4_layout.addWidget(self.mp4_path_input);
       mp4_layout.addWidget(self.mp4_select_button)
       self.mp3_path_input = QLineEdit();
       self.mp3_path_input.setReadOnly(True)  # Apenas para seguir o fluxo do usuário
       self.mp3_select_button = QPushButton("Procurar MP3 original...");
       self.mp3_select_button.clicked.connect(self.select_mp3)
       mp3_layout = QHBoxLayout();
       mp3_layout.addWidget(self.mp3_path_input);
       mp3_layout.addWidget(self.mp3_select_button)
       self.decrypt_button = QPushButton("Recuperar Mensagem");
       self.decrypt_button.clicked.connect(self.start_process)
       self.status_label = QLabel("");
       self.status_label.setObjectName("statusLabel")


       layout.addWidget(QLabel("Selecione o arquivo MP4 que contém a mensagem:"))
       layout.addLayout(mp4_layout)
       layout.addWidget(QLabel("Selecione o arquivo MP3 original (usado na criação):"))
       layout.addLayout(mp3_layout)
       layout.addStretch()
       layout.addWidget(self.status_label)
       layout.addWidget(self.decrypt_button)
       self.setLayout(layout)


   def select_mp4(self):
       file_name, _ = QFileDialog.getOpenFileName(self, "Selecionar MP4", "", "Arquivos MP4 (*.mp4)")
       if file_name: self.mp4_path_input.setText(file_name)


   def select_mp3(self):
       file_name, _ = QFileDialog.getOpenFileName(self, "Selecionar MP3", "", "Arquivos MP3 (*.mp3)")
       if file_name: self.mp3_path_input.setText(file_name)


   def start_process(self):
       mp4_path, mp3_path = self.mp4_path_input.text(), self.mp3_path_input.text()
       if not mp4_path or not mp3_path: QMessageBox.warning(self, "Aviso",
                                                            "Por favor, selecione ambos os arquivos."); return
       if not os.path.exists(FFMPEG_EXE): QMessageBox.critical(self, "Erro Crítico",
                                                               f"FFMPEG não encontrado em:\n{FFMPEG_EXE}"); return


       self.decrypt_button.setEnabled(False);
       self.status_label.setText("Iniciando recuperação...")
       self.thread, self.worker = QThread(), DecryptWorker(mp4_path, mp3_path)
       self.worker.moveToThread(self.thread)
       self.thread.started.connect(self.worker.run)
       self.worker.signals.finished.connect(self.thread.quit);
       self.worker.signals.finished.connect(self.worker.deleteLater)
       self.thread.finished.connect(self.thread.deleteLater)
       self.worker.signals.progress.connect(lambda msg: self.status_label.setText(msg))
       self.worker.signals.error.connect(self.process_error)
       self.worker.signals.success.connect(self.process_success)
       self.thread.start()


   def process_finished(self):
       self.decrypt_button.setEnabled(True);
       self.status_label.setText("")


   def process_error(self, err):
       self.process_finished();
       QMessageBox.critical(self, "Erro", err)


   def process_success(self, text):
       self.process_finished()
       if not text.strip():
           QMessageBox.warning(self, "Concluído", "Nenhuma mensagem de texto foi encontrada.")
       else:
           ResultDialog(text, self).exec()
       self.close()




class MainWindow(QMainWindow):
   def __init__(self):
       super().__init__()
       self.setWindowTitle("Audio Steganographer V2")
       self.setFixedSize(500, 300)
       self.central_widget = QWidget()
       self.setCentralWidget(self.central_widget)
       layout = QVBoxLayout(self.central_widget)
       layout.setAlignment(Qt.AlignmentFlag.AlignCenter);
       layout.setSpacing(20)
       welcome_label = QLabel("Bem-vindo!");
       welcome_label.setObjectName("welcomeLabel");
       welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
       encrypt_button = QPushButton("Criptografar Mensagem");
       encrypt_button.clicked.connect(self.open_encrypt_window)
       decrypt_button = QPushButton("Descriptografar Mensagem");
       decrypt_button.clicked.connect(self.open_decrypt_window)
       layout.addWidget(welcome_label);
       layout.addWidget(encrypt_button);
       layout.addWidget(decrypt_button)
       self.encrypt_win = None;
       self.decrypt_win = None


   def open_encrypt_window(self):
       if self.encrypt_win is None or not self.encrypt_win.isVisible(): self.encrypt_win = EncryptWindow(); self.encrypt_win.show()


   def open_decrypt_window(self):
       if self.decrypt_win is None or not self.decrypt_win.isVisible(): self.decrypt_win = DecryptWindow(); self.decrypt_win.show()




if __name__ == '__main__':
   try:
       from Crypto.Cipher import AES
   except ImportError:
       app = QApplication(sys.argv)
       QMessageBox.critical(None, "Erro de Inicialização",
                            "Por favor, instale a biblioteca de criptografia:\n"
                            "'pip install pycryptodome'")
       sys.exit(1)


   # Nova verificação para garantir que ambos os executáveis do FFmpeg estão presentes.
   if not os.path.exists(FFMPEG_EXE) or not os.path.exists(FFPROBE_EXE):
       app = QApplication(sys.argv)
       missing_exec = ""
       if not os.path.exists(FFMPEG_EXE):
           missing_exec += f"FFmpeg não encontrado em:\n{FFMPEG_EXE}\n"
       if not os.path.exists(FFPROBE_EXE):
           missing_exec += f"FFprobe não encontrado em:\n{FFPROBE_EXE}\n"
       QMessageBox.critical(None, "Erro Crítico de Inicialização",
                            f"Alguns executáveis do FFmpeg estão faltando.\n\n{missing_exec}Verifique se a pasta 'ffmpeg/bin' contém ambos os arquivos.")
       sys.exit(1)


   app = QApplication(sys.argv)
   app.setStyleSheet(STYLESHEET)
   window = MainWindow()
   window.show()
   sys.exit(app.exec())

