import sys
import os
import funcs
import traceback
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit, QFrame

class PromptThread(QThread):
    linha = pyqtSignal(str)  # emitida a cada linha
    erro = pyqtSignal(str)   # emitida em caso de exceção

    def __init__(self, modelo, prompt):
        super().__init__()
        self.modelo = modelo
        self.prompt = prompt

    def run(self):
        try:
            for linha in funcs.fazer_prompt(self.modelo, self.prompt):
                self.linha.emit(str(linha))  # sinal emitido a cada linha
        except Exception:
            self.erro.emit(traceback.format_exc())


# Criamos uma classe que "É UMA" janela (herda de QWidget)
class MinhaJanela(QWidget):
    def __init__(self):
        super().__init__()  # Inicializa o QWidget padrão

        # Configurações iniciais da janela
        self.setWindowTitle("PyChatBot")
        self.resize(1024, 800)

        # Chama a função que cria os botões e textos
        self.setup_ui()

    def setup_ui(self):

        def click_botao_prompt():
            self.thread = PromptThread(self.botao_modelo.currentText(), self.chat_prompt.toPlainText())
            self.thread.linha.connect(lambda r: self.chat_tela.append(r))
            self.thread.erro.connect(lambda e: self.chat_tela.append(f"Erro:\n{e}"))
            self.thread.start()

        self.chat_tela = QTextEdit()
        self.chat_tela.setReadOnly(True)
        self.chat_tela.setMinimumHeight(300)
        self.chat_tela.setMaximumHeight(700)

        self.prompt_barra = QHBoxLayout()
        self.chat_prompt = QTextEdit()
        self.chat_prompt.setMinimumHeight(20)
        self.chat_prompt.setMaximumHeight(40)
        self.chat_prompt.setMinimumWidth(700)
        self.chat_prompt.setMaximumWidth(1600)
        self.chat_prompt.setFont(QFont("Arial", 15))

        self.chat_botao = QPushButton()
        self.chat_botao.setIcon(QIcon(f"{os.getcwd()}\\ícones\\seta_enviar.jpg"))
        self.chat_botao.setMinimumHeight(20)
        self.chat_botao.setMaximumHeight(40)
        self.chat_botao.clicked.connect(click_botao_prompt)

        self.prompt_barra.addWidget(self.chat_prompt, alignment=Qt.AlignmentFlag.AlignLeft, stretch=2)
        self.prompt_barra.addWidget(self.chat_botao, alignment=Qt.AlignmentFlag.AlignLeft, stretch=1)

        self.botao_modelo = QComboBox()
        for modelo in funcs.listar_modelos():
            self.botao_modelo.addItem(modelo)
        self.botao_modelo.addItem("Adicionar modelo")
        self.botao_modelo.currentIndexChanged.connect( lambda index: funcs.selecionar_modelo(self.botao_modelo.currentText()))
        self.botao_modelo.setMaximumWidth(600)
        self.botao_modelo.setMinimumWidth(250)
        self.botao_modelo.setMinimumHeight(20)
        self.botao_modelo.setMaximumHeight(40)

        self.botao_arquivo = QPushButton("Carregar Arquivo")
        self.botao_arquivo.setMaximumWidth(200)
        self.botao_arquivo.setMinimumWidth(100)
        self.botao_arquivo.setMinimumHeight(20)
        self.botao_arquivo.setMaximumHeight(40)
        self.botao_arquivo.clicked.connect(funcs.carregar_arquivo)

        layout_inferior = QHBoxLayout()
        layout_inferior.addWidget(self.botao_modelo)
        layout_inferior.addWidget(self.botao_arquivo)

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
