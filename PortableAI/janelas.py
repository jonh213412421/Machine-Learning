from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QDialog


class janela_mensagem(QDialog):
   def __init__(self, mensagem, tamanho):
       super().__init__()
       self.mensagem = mensagem
       self.tamanho = tamanho


       self.setWindowTitle("Sobre")
       self.setFixedSize(480, 240)
       layout = QVBoxLayout()


       self.label = QLabel(self.mensagem)
       self.label.setWordWrap(True)
       layout.addWidget(self.label)
       self.botao = QPushButton("Fechar")
       self.botao.clicked.connect(self.accept)  # Closes the dialog
       layout.addWidget(self.botao)
       self.setLayout(layout)

