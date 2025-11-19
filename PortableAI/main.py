import sys
import funcs
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit


# Criamos uma classe que "É UMA" janela (herda de QWidget)
class MinhaJanela(QWidget):
    def __init__(self):
        super().__init__()  # Inicializa o QWidget padrão

        # Configurações iniciais da janela
        self.setWindowTitle("Tutorial PyQt6")
        self.resize(300, 200)

        # Chama a função que cria os botões e textos
        self.setup_ui()

    def setup_ui(self):
        # --- 1. Criar os Widgets (As peças) ---
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setMinimumHeight(300)
        self.chat.setMaximumHeight(700)
        self.botao = QComboBox()
        for modelo in funcs.listar_modelos():
            self.botao.addItem(modelo)
        self.botao.setPlaceholderText("Selecione ou busque um arquivo...")
        self.botao.setMaximumWidth(600)
        self.botao.setMinimumWidth(150)

        layout_selecao_modelo = QHBoxLayout()
        layout_selecao_modelo.addStretch(8)
        layout_selecao_modelo.addWidget(self.botao)

        # --- 2. Criar o Layout (A organização) ---
        # QVBoxLayout organiza as coisas Verticalmente (um embaixo do outro)
        layout = QVBoxLayout()

        # Adicionamos as peças no layout
        layout.addWidget(self.chat)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(layout)
        layout_principal.addLayout(layout_selecao_modelo)

        # --- 3. Aplicar o layout na janela ---
        self.setLayout(layout_principal)


# Bloco de execução padrão
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MinhaJanela()
    janela.show()
    sys.exit(app.exec())
