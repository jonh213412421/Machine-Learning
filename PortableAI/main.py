import sys
import os
import html
import funcs
import traceback
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QIcon, QFont, QTextCursor, QTextCharFormat, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit, QFrame

# thread para rodar o modelo
class PromptThread(QThread):
    linha = pyqtSignal(str)  # emitida a cada linha
    erro = pyqtSignal(str)   # emitida em caso de exceção

    def __init__(self, modelo, prompt):
        super().__init__()
        funcs.iniciar() # -> verifica a integridade dos diretórios
        self.thread = None
        self.thread_running = False
        self.modelo = modelo
        self.prompt = prompt

    def run(self):
        self.thread_running = True
        i = 0
        try:
            for linha in funcs.fazer_prompt(self.modelo, self.prompt):
                i += 1
                if not self.thread_running:
                    break  # para o loop imediatamente
                if i == 105:
                    self.linha.emit(str("<br>"))
                    i = 0
                self.linha.emit(str(linha)) #-> emite sinal para printar na tela
        except Exception:
            self.erro.emit(traceback.format_exc())
        finally:
            self.linha.emit(str("<br><br>"))
            self.thread_running = False
            print(self.thread_running)

    def stop(self):
        self.thread_running = False  # chamada externa para cancelar

# Criamos uma classe que "É UMA" janela (herda de QWidget)
class MinhaJanela(QWidget):
    def __init__(self):
        super().__init__()  # Inicializa o QWidget padrão
        self.orig_dir = os.getcwd()
        self.thread = None

        # Configurações iniciais da janela
        self.setWindowTitle("PyChatBot")
        self.resize(1024, 800)

        # Chama a função que cria os botões e textos
        self.setup_ui()

    def setup_ui(self):

        def adicionar_html(r) -> None:
            # Move o cursor para o final
            cursor = janela.chat_tela.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            r_escaped = html.escape(r)
            # Insere texto com estilo sem quebrar linha
            r = r.replace(" ", "&nbsp;") # <- para adicionar os espaços
            cursor.insertHtml(f"<span style='font-family: Arial; font-size: 12pt; color: black; margin-bottom: 25px; display: inline-block'>{r}</span>")

            # Atualiza o cursor
            janela.chat_tela.setTextCursor(cursor)

        def animacao_botao() -> None:
            # Animar botão (encolher e expandir)
            rect = self.chat_botao.geometry()
            self.chat_botao.setIcon(QIcon())
            anim = QPropertyAnimation(self.chat_botao, b"geometry")
            anim.setDuration(150)  # 150ms
            anim.setStartValue(rect)
            anim.setKeyValueAt(0.5, QRect(rect.x() + 3, rect.y() + 3, rect.width() - 6, rect.height() - 6))
            anim.setEndValue(rect)
            anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            anim.start()
            self.button_animation = anim  # manter referência

            # Chamar função original
            click_botao_prompt()

        def click_botao_prompt() -> None:
            if self.thread is None or not self.thread.thread_running:
                self.thread = PromptThread(self.botao_modelo.currentText(), self.chat_prompt.toPlainText())
                self.thread.linha.connect(adicionar_html)
                self.thread.erro.connect(lambda e: self.chat_tela.append(f"Erro:\n{e}"))
                self.thread.start()
            else:
                if self.thread:
                    self.thread.stop()
                self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.jpg"))
                self.chat_tela.append("<i>Operação cancelada pelo usuário.</i>")

        #funções para atividades dinâmicas
        def esconder_mostrar_botao() -> None:
            text = self.chat_prompt.toPlainText().strip()
            if text:
                self.chat_botao.show()
            else:
                self.chat_botao.hide()

        #trabalhar aqui. Carregamento do arquivo e administração dos dados
        def carregar_arquivo() -> None:
            nome, dados = funcs.carregar_arquivo()
            if nome and dados:
                self.arquivo_carregado.setText(nome)

        # Tela principal
        self.chat_tela = QTextEdit()
        self.chat_tela.setReadOnly(True)
        self.chat_tela.setMinimumHeight(300)
        self.chat_tela.setMaximumHeight(700)
        self.chat_tela.setAlignment(Qt.AlignmentFlag.AlignLeft)

        #união da barra para escrever o prompt com o botão de enviar o prompt
        self.prompt_barra = QHBoxLayout()
        #parte para escrever
        self.chat_prompt = QTextEdit()
        self.chat_prompt.setMaximumHeight(40)
        self.chat_prompt.setMinimumWidth(1000)
        self.chat_prompt.setMaximumWidth(1600)
        self.chat_prompt.setFont(QFont("Arial", 15))
        self.chat_prompt.textChanged.connect(esconder_mostrar_botao)
        #botão para enviar
        self.chat_botao = QPushButton()
        self.chat_botao.setIcon(QIcon(f"{os.getcwd()}\\ícones\\seta_enviar.jpg"))
        self.chat_botao.setMinimumHeight(20)
        self.chat_botao.setMaximumHeight(40)
        self.chat_botao.clicked.connect(animacao_botao)
        self.chat_botao.setVisible(False)
        #parte que junta
        self.prompt_barra.addWidget(self.chat_prompt, alignment=Qt.AlignmentFlag.AlignLeft, stretch=2)
        self.prompt_barra.addWidget(self.chat_botao, alignment=Qt.AlignmentFlag.AlignLeft, stretch=1)

        #barra para escolher o modelo
        self.botao_modelo = QComboBox()
        for modelo in funcs.listar_modelos():
            self.botao_modelo.addItem(modelo)
        self.botao_modelo.addItem("Adicionar modelo")
        self.botao_modelo.currentIndexChanged.connect( lambda index: funcs.selecionar_modelo(self.botao_modelo.currentText()))
        self.botao_modelo.setMaximumWidth(600)
        self.botao_modelo.setMinimumWidth(250)
        self.botao_modelo.setMinimumHeight(20)
        self.botao_modelo.setMaximumHeight(40)

        #botão para carregar arquivo
        self.botao_arquivo = QPushButton("Carregar Arquivo")
        self.botao_arquivo.setMaximumWidth(200)
        self.botao_arquivo.setMinimumWidth(100)
        self.botao_arquivo.setMinimumHeight(20)
        self.botao_arquivo.setMaximumHeight(40)
        self.botao_arquivo.clicked.connect(carregar_arquivo)
        #mostrador de arquivo carregado
        self.arquivo_carregado = QTextEdit()
        self.arquivo_carregado.setReadOnly(True)
        self.arquivo_carregado.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.arquivo_carregado.setPlaceholderText("Nenhum arquivo carregado")
        self.arquivo_carregado.setMaximumWidth(200)
        self.arquivo_carregado.setMinimumWidth(100)
        self.arquivo_carregado.setMinimumHeight(20)
        self.arquivo_carregado.setMaximumHeight(40)

        layout_inferior = QHBoxLayout()
        layout_inferior.addWidget(self.botao_modelo)
        layout_inferior.addWidget(self.botao_arquivo)
        layout_inferior.addWidget(self.arquivo_carregado)

        layout_principal_area = QVBoxLayout()
        layout_principal_area.addWidget(self.chat_tela)
        layout_principal_area.addLayout(self.prompt_barra)
        layout_principal_area.addLayout(layout_inferior)

        # -------------------------
        #        SIDEBAR
        # -------------------------
        sidebar = QFrame()
        sidebar.resize(0, 5)
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)

        layout_sidebar = QVBoxLayout(sidebar)
        layout_sidebar.addWidget(QLabel("Menu"))
        layout_sidebar.addWidget(QPushButton("Opção 1"))
        layout_sidebar.addWidget(QPushButton("Opção 2"))
        layout_sidebar.addWidget(QPushButton("Opção 3"))
        layout_sidebar.addStretch()

        # -------------------------
        #  LAYOUT GERAL (horizontal)
        # -------------------------
        layout_geral = QHBoxLayout()
        layout_geral.addWidget(sidebar)              # ← barra lateral
        layout_geral.addLayout(layout_principal_area)  # ← sua área principal

        self.setLayout(layout_geral)


# Bloco de execução padrão
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MinhaJanela()
    janela.show()
    sys.exit(app.exec())
