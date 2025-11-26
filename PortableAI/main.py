import sys
import os
import funcs
import traceback
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QTextCursor, QTextCharFormat, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit, \
   QFrame, QSlider, QTextBrowser

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
           # coloca o prompt na primeira linha
           self.linha.emit(f"<div style='text-align: right;'><span style='color: #222222; font-family: Segoe UI; font-size: 18px;'>{self.prompt}</span></div><br>")
           for linha in funcs.fazer_prompt(self.modelo, self.prompt):
               if not self.thread_running:
                   break  # para o loop imediatamente
               if linha == "":
                   i += 1
                   if i > 5:
                       break
               else:
                   self.linha.emit(f"<span style='color: #222222; font-family: Segoe UI; font-size: 18px;'>{linha}</span>")  # -> emite sinal para printar na tela
                   i -= 1
                   if i < 0:
                       i = 0


       except Exception:
           self.erro.emit(traceback.format_exc())
       finally:
           self.thread_running = False


   def stop(self):
       self.thread_running = False  # chamada externa para cancelar


# Criamos uma classe que "É UMA" janela (herda de QWidget)
class MinhaJanela(QWidget):
   def __init__(self):
       super().__init__()  # Inicializa o QWidget padrão
       self.orig_dir = os.getcwd()
       self.thread = None
       self.sidebar_estendida = True
       # Configurações iniciais da janela
       self.setWindowTitle("PyChatBot")
       self.setFixedSize(1024, 800)


       # Chama a função que cria os botões e textos
       self.setup_ui()


   def setup_ui(self):


       def adicionar_html(texto) -> None:
           cursor = janela.chat_tela.textCursor()
           cursor.movePosition(QTextCursor.MoveOperation.End)


           # Se quiser cor específica, defina no formato do cursor antes de escrever
           formato = QTextCharFormat()
           formato.setFont(QFont("Arial", 12))
           formato.setForeground(QColor("black"))
           cursor.setCharFormat(formato)


           cursor.insertHtml(texto)  # Usa insertText em vez de insertHtml para evitar bugs de tags quebradas


           # Atualiza o scroll
           janela.chat_tela.setTextCursor(cursor)
           janela.chat_tela.ensureCursorVisible()


       def click_botao_prompt() -> None:
           # se for executado enquanto o programa está rodando, ele volta ao estado inicial
           def voltar_ao_inicio() -> None:
               self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
               habilitar_botao_carregamento_arquivo()
               hablitar_botao_modelo()
           # se não tiver rodado ainda, começa a thread
           if self.thread is None or not self.thread.thread_running:
               self.thread = PromptThread(self.botao_modelo.currentText(), self.chat_prompt.toPlainText())
               self.thread.linha.connect(adicionar_html)
               self.thread.erro.connect(lambda e: self.chat_tela.append(f"Erro:\n{e}"))
               self.thread.finished.connect(voltar_ao_inicio)
               desabilitar_botao_carregamento_arquivo()
               desablitar_botao_modelo()
               self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\trabalhando.svg"))
               self.thread.start()
           else:
               if self.thread:
                   self.thread.stop()
               self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
               habilitar_botao_carregamento_arquivo()
               hablitar_botao_modelo()
               self.chat_tela.append("<i>Operação cancelada pelo usuário.</i><br><br>")


       #funções para atividades dinâmicas
       def esconder_mostrar_botao() -> None:
           text = self.chat_prompt.toPlainText().strip()
           if text:
               self.chat_botao.show()
           else:
               self.chat_botao.hide()


       #desabilita o carregamento de arquivos. Necessário fazer enquanto o programa trabalha.
       def desabilitar_botao_carregamento_arquivo() -> None:
           self.botao_arquivo.setDisabled(True)


       #habilita o carregamento de arquivos novamente
       def habilitar_botao_carregamento_arquivo() -> None:
           self.botao_arquivo.setDisabled(False)


       def desablitar_botao_modelo() -> None:
           self.botao_modelo.setDisabled(True)


       def hablitar_botao_modelo() -> None:
           self.botao_modelo.setDisabled(False)


       #trabalhar aqui. Carregamento do arquivo e administração dos dados
       def carregar_arquivo() -> None:
           nome, dados = funcs.carregar_arquivo()
           if nome and dados:
               self.arquivo_carregado.setText(nome)
           else:
               self.arquivo_carregado.setText("")


       def minimizar_sidebar():
           width_atual = sidebar.width()
           width_fechada = 0
           width_aberta = 200


           if self.sidebar_estendida == True:
               destino = width_fechada
               self.sidebar_estendida = False
               maximizador_menu.setIcon(QIcon(f"{self.orig_dir}\\ícones\\expansão_menu.svg"))
           else:
               destino = width_aberta
               self.sidebar_estendida = True
               maximizador_menu.setIcon(QIcon(f"{self.orig_dir}\\ícones\\minimização_menu.svg"))


           # Cria animação
           self.animacao = QPropertyAnimation(sidebar, b"maximumWidth")
           self.animacao.setDuration(300)
           self.animacao.setStartValue(width_atual)
           self.animacao.setEndValue(destino)
           self.animacao.setEasingCurve(QEasingCurve.Type.InOutCubic)
           self.animacao.start()


       # Tela principal
       self.chat_tela = QTextBrowser()
       #tem que passar a estilização em tempo real
       self.chat_tela.setStyleSheet("""
           QTextBrowser {
               background-color: #DEE6EE;  /* fundo cinza claro */
               color: #222222;             /* cor do texto */
               border: 1px solid #ccc;     /* borda leve */
               border-radius: 8px;         /* cantos arredondados */
               padding: 8px;               /* espaçamento interno */
           }
       """)
       self.chat_tela.setReadOnly(True)
       self.chat_tela.setMinimumHeight(300)
       self.chat_tela.setMaximumHeight(700)
       self.chat_tela.setAlignment(Qt.AlignmentFlag.AlignLeft)


       #união da barra para escrever o prompt com o botão de enviar o prompt
       self.prompt_barra = QHBoxLayout()
       #parte para escrever
       self.chat_prompt = QTextEdit()
       self.chat_prompt.setMaximumHeight(40)
       self.chat_prompt.setMinimumWidth(900)
       self.chat_prompt.setFont(QFont("Arial", 12))
       self.chat_prompt.textChanged.connect(esconder_mostrar_botao)
       #botão para enviar
       self.chat_botao = QPushButton()
       self.chat_botao.setIcon(QIcon(f"{os.getcwd()}\\ícones\\seta_enviar.svg"))
       #tira a margem
       self.chat_botao.setStyleSheet("margin: 0px; border: none;")
       self.chat_botao.setMinimumWidth(50)
       self.chat_botao.setMinimumHeight(20)
       self.chat_botao.setMaximumHeight(40)
       # dá estilo para a seta
       self.chat_botao.setStyleSheet("""
           QPushButton {
               background-color: rgb(245, 245, 245);     /* mais claro */
               border: none;
               border-radius: 20px;
               margin: 0px;
               padding: 0px;
           }
           QPushButton:pressed {
               background-color: rgb(230, 230, 230);     /* mais escuro ao pressionar */
           }
           QPushButton:hover {
               background-color: rgb(230, 230, 230);     /* mais escuro ao pressionar */
           }
       """)
       self.chat_botao.clicked.connect(click_botao_prompt)
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
       #dá estilo ao botão de arquivo carregado
       self.botao_arquivo.setStyleSheet("""
           QPushButton {
               background-color: rgb(180, 180, 180);     /* mais claro */
               border: none;
               border-radius: 20px;
               margin: 0px;
               padding: 0px;
           }
           QPushButton:pressed {
               background-color: rgb(230, 230, 230);     /* mais escuro ao pressionar */
                   padding-top: 2px;                       /* Faz o botão parecer afundar */
                   padding-bottom: -2px;
           }
           QPushButton:hover {
               background-color: rgb(150, 150, 150);     /* mais escuro ao pressionar */
           }
       """)
       self.botao_arquivo.clicked.connect(carregar_arquivo)
       #mostrador de arquivo carregado
       self.arquivo_carregado = QTextEdit()
       self.arquivo_carregado.setReadOnly(True)
       self.arquivo_carregado.setAlignment(Qt.AlignmentFlag.AlignCenter)
       self.arquivo_carregado.setPlaceholderText("Nenhum arquivo carregado")
       self.arquivo_carregado.setStyleSheet("""
           QTextEdit {
               background-color: #DEE6EE; 
               border: none;
               padding: 0px;
           }""")
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


       #sidebar
       sidebar = QFrame()
       sidebar.resize(0, 5)
       sidebar.setMaximumWidth(200)
       sidebar.setFrameShape(QFrame.Shape.StyledPanel)
       sidebar.setStyleSheet("""
           QFrame {
               background: qlineargradient(
               x1: 0, y1: 0,
               x2: 0, y2: 1,
               stop: 0 #EFF3F8,   /* Cinza muito claro com um toque frio de azul no topo */
               stop: 1 #DEE6EE    /* Um azul-acinzentado ligeiramente mais profundo na base */
       );      /* Cinza bem escuro */
               border-right: 1px solid #333;    /* Linha separadora sutil */
           }
       """)


       botao_minimizar_menu = QPushButton("Minimizar")
       botao_minimizar_menu.clicked.connect(minimizar_sidebar)
       menu = QLabel("Menu")
       menu.setStyleSheet("""
           QLabel {
               color: black;              /* Texto cinza claro */
               font-weight: bold;           /* Negrito */
               font-size: 16px;             /* Tamanho pequeno mas legível */
               letter-spacing: 2px;         /* Espaçamento entre letras (Estilo chique) */
               background: transparent;
               border-bottom: 1px solid #333; /* Linha abaixo do texto */
               padding-bottom: 5px;
           }
       """)
       layout_sidebar = QVBoxLayout(sidebar)
       layout_sidebar.addWidget(menu)
       layout_sidebar.addSpacing(15)


       # slider superior
       quantidade_tokens_arquivo = QVBoxLayout()
       titulo_quantidade_tokens_arquivo = QLabel("Quantidade de tokens")
       titulo_quantidade_tokens_arquivo.setStyleSheet("""
           QLabel {
               color: black;              /* Texto cinza claro */
               font-weight: bold;           /* Negrito */
               font-size: 12px;             /* Tamanho pequeno mas legível */
               letter-spacing: 2px;         /* Espaçamento entre letras (Estilo chique) */
               background: transparent;
               border-bottom: 1px solid #333; /* Linha abaixo do texto */
               padding-bottom: 5px;
           }
       """)
       titulo_quantidade_tokens_arquivo.setMaximumHeight(20)
       slider_quantidade_tokens_arquivo = QSlider(Qt.Orientation.Horizontal)
       slider_quantidade_tokens_arquivo.setMinimum(2000)  # valor mínimo
       slider_quantidade_tokens_arquivo.setMaximum(64000)  # valor máximo
       slider_quantidade_tokens_arquivo.setValue(10000)  # valor inicial opcional
       mostrador_quantidade_tokens_arquivo = QTextEdit()
       mostrador_quantidade_tokens_arquivo.setReadOnly(True)
       mostrador_quantidade_tokens_arquivo.setMaximumHeight(22)
       mostrador_quantidade_tokens_arquivo.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
       mostrador_quantidade_tokens_arquivo.setText(str(slider_quantidade_tokens_arquivo.value()))
       mostrador_quantidade_tokens_arquivo.setAlignment(Qt.AlignmentFlag.AlignCenter)
       mostrador_quantidade_tokens_arquivo.setStyleSheet("""
           QTextEdit {
               color: black;              /* Texto cinza claro */
               font-weight: bold;           /* Negrito */
               font-size: 12px;             /* Tamanho pequeno mas legível */
               letter-spacing: 2px;         /* Espaçamento entre letras (Estilo chique) */
               background: transparent;
               border: none;
           }
       """)
       #mecanismo para atualizar valores
       def atualizar_valor_slider(valor):
           mostrador_quantidade_tokens_arquivo.setText(f"{valor}")
           mostrador_quantidade_tokens_arquivo.setAlignment(Qt.AlignmentFlag.AlignCenter)
       slider_quantidade_tokens_arquivo.valueChanged.connect(lambda valor: atualizar_valor_slider(valor))
       quantidade_tokens_arquivo.addWidget(titulo_quantidade_tokens_arquivo)
       quantidade_tokens_arquivo.addWidget(slider_quantidade_tokens_arquivo)
       quantidade_tokens_arquivo.addWidget(mostrador_quantidade_tokens_arquivo)
       layout_sidebar.addLayout(quantidade_tokens_arquivo)
       layout_sidebar.addSpacing(15)
       #trabalhar aqui
       caixa_de_historico = QVBoxLayout()


       layout_sidebar.addWidget(QPushButton("Opção 2"))
       layout_sidebar.addWidget(QPushButton("Opção 3"))
       layout_sidebar.addStretch()


       maximizador_menu = QPushButton()
       #começa minimizada
       minimizar_sidebar()
       maximizador_menu.setIcon(QIcon(f"{self.orig_dir}\\ícones\\expansão_menu.svg"))
       maximizador_menu.clicked.connect(minimizar_sidebar)


       #  LAYOUT GERAL (horizontal)
       layout_geral = QHBoxLayout()
       layout_geral.addWidget(maximizador_menu)
       layout_geral.setAlignment(maximizador_menu, Qt.AlignmentFlag.AlignTop)
       layout_geral.addWidget(sidebar)              # ← barra lateral
       layout_geral.addLayout(layout_principal_area)  # ← sua área principal


       self.setLayout(layout_geral)
       self.setWindowIcon(QIcon(f"{self.orig_dir}\\ícones\\chatbot.svg"))


       # atalho do enter. Melhorar!
       atalho_enter = QShortcut(QKeySequence("Return"), self)
       atalho_enter.activated.connect(lambda: self.chat_botao.clicked.emit())


# Bloco de execução padrão
if __name__ == "__main__":
   app = QApplication(sys.argv)
   janela = MinhaJanela()
   janela.show()
   sys.exit(app.exec())
