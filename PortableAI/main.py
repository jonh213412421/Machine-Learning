import sys
import os
import json
import funcs
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent
from PyQt6.QtGui import QIcon, QFont, QShortcut, QKeySequence
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit, \
    QFrame, QSlider
from PyQt6.QtWebEngineWidgets import QWebEngineView
import janelas
import estilos
from threads import PromptThread, CarregarArquivoThread


class ChatHandler:
    def __init__(self):
        self.bot_container_id = None
        self.div_bot_criada = False
        self.j = 0
        self.chat_tela = None
        self.chat_botao = None
        self.orig_dir = ""

    def habilitar_botao_prompt(self, botao_prompt: bool):
        if self.chat_botao and botao_prompt:
            self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
            self.chat_botao.setEnabled(True)

    def adicionar_html(self, texto: str, remetente: str, raw_html: bool = False) -> None:
        if not self.chat_tela:
            return

        # 1. Preparar o conteúdo
        if raw_html:
            texto_final = texto
        else:
            texto_final = (
                str(texto).replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;")
                .replace("\n", "<br>")
            )

        # 2. Serializar para JavaScript
        js_content = json.dumps(texto_final)

        if remetente == 'user':
            wrapper_class = "user-wrapper"
            msg_class = "user"
            self.div_bot_criada = False

            js = f"""
                var wrapper = document.createElement('div');
                wrapper.id = 'msg_{self.j}';
                wrapper.className = '{wrapper_class} msg-wrapper';
                var msg = document.createElement('div');
                msg.className = '{msg_class} msg';
                msg.innerHTML = {js_content}; 
                wrapper.appendChild(msg);
                document.getElementById('chat').appendChild(wrapper);
                window.scrollTo(0, document.body.scrollHeight);
            """
            self.j += 1
        else:
            if not self.div_bot_criada:
                js = f"""
                    var wrapper = document.createElement('div');
                    wrapper.id = 'msg_{self.j}';
                    wrapper.className = 'bot-wrapper msg-wrapper';
                    var msg = document.createElement('div');
                    msg.className = 'bot msg';
                    msg.innerHTML = {js_content};
                    wrapper.appendChild(msg);
                    document.getElementById('chat').appendChild(wrapper);
                    window.scrollTo(0, document.body.scrollHeight);
                """
                self.div_bot_criada = True
            else:
                js = f"""
                var wrapper = document.getElementById('msg_{self.j}');
                if (wrapper) {{
                    var msg_div = wrapper.querySelector('.bot');
                    msg_div.innerHTML += {js_content};
                    window.scrollTo(0, document.body.scrollHeight);
                }}
                """

        try:
            self.chat_tela.page().runJavaScript(js)
        except Exception as e:
            print("Error running JavaScript:", e)


class MinhaJanela(QWidget):
    def __init__(self):
        super().__init__()
        self.orig_dir = os.getcwd()
        self.thread = None
        self.sidebar_estendida = True
        self.gerando_resposta = False
        self.setWindowTitle("PyChatBot")
        self.setFixedSize(1024, 800)
        self.setup_ui()

    # --- Event Filter para capturar o Enter na caixa de texto ---
    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress and source is self.chat_prompt:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Se Shift estiver pressionado, permite a quebra de linha normal
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return super().eventFilter(source, event)

                # Caso contrário, clica no botão (Enviar) e consome o evento (não cria linha)
                self.chat_botao.click()
                return True
        return super().eventFilter(source, event)

    # --- Métodos auxiliares de UI ---
    def desabilitar_botao_carregamento_arquivo(self) -> None:
        self.botao_arquivo.setDisabled(True)

    def habilitar_botao_carregamento_arquivo(self) -> None:
        self.botao_arquivo.setDisabled(False)

    def desabilitar_botao_modelo(self) -> None:
        self.botao_modelo.setDisabled(True)

    def habilitar_botao_modelo(self) -> None:
        self.botao_modelo.setDisabled(False)

    def on_resposta_finalizada(self) -> None:
        self.gerando_resposta = False
        self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
        self.habilitar_botao_carregamento_arquivo()
        self.habilitar_botao_modelo()

    def on_thread_finished(self) -> None:
        if self.gerando_resposta:
            self.gerando_resposta = False
            self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
            self.habilitar_botao_carregamento_arquivo()
            self.habilitar_botao_modelo()

    def setup_ui(self):
        self.chat_handler = ChatHandler()
        self.chat_handler.orig_dir = self.orig_dir

        def click_botao_prompt() -> None:
            if self.gerando_resposta:
                # STOP
                if self.thread and self.thread.isRunning():
                    try:
                        self.thread.linha.disconnect()
                        self.thread.sinal_resposta_finalizada.disconnect()
                        self.thread.finished.disconnect()
                    except:
                        pass

                    self.thread.stop_thread()
                    self.thread.wait()
                    self.thread.deleteLater()
                    self.thread = None

                self.gerando_resposta = False
                self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))

                msg_cancel = estilos.mensagem_operacao_cancelada()
                self.chat_handler.adicionar_html(f"<br><i>{msg_cancel}</i>", 'bot', raw_html=True)

                self.habilitar_botao_carregamento_arquivo()
                self.habilitar_botao_modelo()
                return

            # ENVIAR
            texto = self.chat_prompt.toPlainText().strip()
            if not texto:
                return

            self.gerando_resposta = True
            self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\trabalhando.svg"))
            self.chat_botao.repaint()

            self.desabilitar_botao_carregamento_arquivo()
            self.desabilitar_botao_modelo()

            if self.thread is None or not self.thread.isRunning():
                modelo_selecionado = self.botao_modelo.currentText()
                if not modelo_selecionado:
                    self.chat_tela.setHtml("<h3>Erro: Nenhum modelo selecionado.</h3>")
                    self.gerando_resposta = False
                    self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
                    return

                self.thread = PromptThread(modelo_selecionado)
                self.thread.linha.connect(lambda msg, user: self.chat_handler.adicionar_html(msg, user))
                self.thread.erro.connect(lambda e: print(f"Erro Thread: {e}"))
                self.thread.sinal_resposta_finalizada.connect(self.on_resposta_finalizada)
                self.thread.finished.connect(self.on_thread_finished)
                self.thread.start()

            self.thread.enviar_prompt(texto)
            self.chat_prompt.clear()

        def esconder_mostrar_botao() -> None:
            if self.gerando_resposta:
                self.chat_botao.show()
                return

            text = self.chat_prompt.toPlainText().strip()
            if text:
                self.chat_botao.show()
            else:
                self.chat_botao.hide()

        def carregar_arquivo() -> None:
            def atualizar_mostrador(nome_arquivo) -> None:
                self.arquivo_carregado.setHtml(nome_arquivo)
                self.arquivo_carregado.setAlignment(Qt.AlignmentFlag.AlignCenter)

            try:
                self.thread_arquivos = CarregarArquivoThread()
                self.thread_arquivos.nome_arquivo.connect(atualizar_mostrador)
                self.thread_arquivos.start()
            except Exception as e:
                print(e)

        def minimizar_sidebar() -> None:
            width_atual = sidebar.width()
            width_fechada = 0
            width_aberta = 200

            if self.sidebar_estendida:
                destino = width_fechada
                self.sidebar_estendida = False
                self.chat_prompt.setMinimumWidth(900)
                self.animacao = QPropertyAnimation(self.chat_prompt, b"maximumWidth")
                self.animacao.setDuration(300)
                self.animacao.setStartValue(width_atual)
                self.animacao.setEndValue(destino)
                self.animacao.setEasingCurve(QEasingCurve.Type.InOutBack)
                self.animacao.start()
                maximizador_menu.setIcon(QIcon(f"{self.orig_dir}\\ícones\\expansão_menu.svg"))
            else:
                destino = width_aberta
                self.sidebar_estendida = True
                self.chat_prompt.setMinimumWidth(700)
                self.animacao = QPropertyAnimation(self.chat_prompt, b"maximumWidth")
                self.animacao.setDuration(300)
                self.animacao.setStartValue(width_atual)
                self.animacao.setEndValue(destino)
                self.animacao.setEasingCurve(QEasingCurve.Type.InOutCubic)
                self.animacao.start()
                maximizador_menu.setIcon(QIcon(f"{self.orig_dir}\\ícones\\minimização_menu.svg"))

            self.animacao_sidebar = QPropertyAnimation(sidebar, b"maximumWidth")
            self.animacao_sidebar.setDuration(300)
            self.animacao_sidebar.setStartValue(width_atual)
            self.animacao_sidebar.setEndValue(destino)
            self.animacao_sidebar.setEasingCurve(QEasingCurve.Type.InOutCubic)
            self.animacao_sidebar.start()

        # Tela principal
        self.chat_tela = QWebEngineView()
        self.chat_tela.setStyleSheet(estilos.estilo_chat_tela())
        self.chat_tela.setMinimumHeight(300)
        self.chat_tela.setMaximumHeight(700)
        self.chat_tela.setHtml(estilos.html_base())
        self.chat_handler.chat_tela = self.chat_tela

        # Prompt barra
        self.prompt_barra = QHBoxLayout()
        self.chat_prompt = QTextEdit()
        self.chat_prompt.setMaximumHeight(40)
        self.chat_prompt.setMinimumWidth(900)
        self.chat_prompt.setFont(QFont("Arial", 12))
        self.chat_prompt.textChanged.connect(esconder_mostrar_botao)

        # INSTALA O FILTRO DE EVENTOS
        self.chat_prompt.installEventFilter(self)

        self.chat_botao = QPushButton()
        self.chat_botao.setIcon(QIcon(f"{os.getcwd()}\\ícones\\seta_enviar.svg"))
        self.chat_botao.setMinimumWidth(50)
        self.chat_botao.setMinimumHeight(20)
        self.chat_botao.setMaximumHeight(40)
        self.chat_botao.setStyleSheet(estilos.estilo_chat_botao())
        self.chat_botao.clicked.connect(click_botao_prompt)
        self.chat_botao.setVisible(False)
        self.chat_handler.chat_botao = self.chat_botao

        self.prompt_barra.addWidget(self.chat_prompt, alignment=Qt.AlignmentFlag.AlignLeft, stretch=2)
        self.prompt_barra.addWidget(self.chat_botao, alignment=Qt.AlignmentFlag.AlignLeft, stretch=1)

        # Botão Modelo
        self.botao_modelo = QComboBox()
        try:
            modelos = funcs.listar_modelos()
            for modelo in modelos:
                self.botao_modelo.addItem(modelo)
        except:
            self.botao_modelo.addItem("Nenhum modelo encontrado")

        self.botao_modelo.addItem("Adicionar modelo")
        self.botao_modelo.currentIndexChanged.connect(
            lambda index: funcs.selecionar_modelo(self.botao_modelo.currentText()))
        self.botao_modelo.setMaximumWidth(600)
        self.botao_modelo.setMinimumWidth(250)
        self.botao_modelo.setMinimumHeight(20)
        self.botao_modelo.setMaximumHeight(40)
        self.botao_modelo.setStyleSheet(estilos.estilo_botao_modelos())

        # Botão Arquivo
        self.botao_arquivo = QPushButton("Carregar Arquivo")
        self.botao_arquivo.setMaximumWidth(200)
        self.botao_arquivo.setMinimumWidth(100)
        self.botao_arquivo.setMinimumHeight(20)
        self.botao_arquivo.setMaximumHeight(40)
        self.botao_arquivo.setStyleSheet(estilos.estilo_botao_arquivo())
        self.botao_arquivo.clicked.connect(carregar_arquivo)

        self.arquivo_carregado = QTextEdit()
        self.arquivo_carregado.setReadOnly(True)
        self.arquivo_carregado.setHtml("Nenhum arquivo carregado")
        self.arquivo_carregado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.arquivo_carregado.setStyleSheet(estilos.estilo_arquivo_carregado())
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

        # Sidebar
        sidebar = QFrame()
        sidebar.resize(0, 5)
        sidebar.setMaximumWidth(200)
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setStyleSheet(estilos.estilo_sidebar())

        menu = QLabel("Menu")
        menu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        menu.setStyleSheet(estilos.estilo_menu())

        layout_sidebar = QVBoxLayout(sidebar)
        layout_sidebar.addWidget(menu)
        layout_sidebar.addSpacing(15)

        # Slider
        quantidade_tokens_arquivo = QVBoxLayout()
        titulo_tokens = QLabel("Quantidade de tokens")
        titulo_tokens.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_tokens.setStyleSheet(estilos.estilo_titulo_quantidade_tokens_arquivo())
        titulo_tokens.setMaximumHeight(20)

        slider_tokens = QSlider(Qt.Orientation.Horizontal)
        slider_tokens.setMinimum(2000)
        slider_tokens.setMaximum(64000)
        slider_tokens.setValue(10000)

        mostrador_tokens = QTextEdit()
        mostrador_tokens.setReadOnly(True)
        mostrador_tokens.setMaximumHeight(22)
        mostrador_tokens.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        mostrador_tokens.setText(str(slider_tokens.value()))
        mostrador_tokens.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mostrador_tokens.setStyleSheet(estilos.estilo_mostrar_quantidade_tokens_arquivo())

        slider_tokens.valueChanged.connect(lambda v: mostrador_tokens.setText(str(v)))

        quantidade_tokens_arquivo.addWidget(titulo_tokens)
        quantidade_tokens_arquivo.addWidget(slider_tokens)
        quantidade_tokens_arquivo.addWidget(mostrador_tokens)
        layout_sidebar.addLayout(quantidade_tokens_arquivo)
        layout_sidebar.addSpacing(15)

        sobre = QPushButton("Sobre")
        sobre.setStyleSheet(estilos.estilo_botao_sobre())

        def sobre_pop(tamanho: tuple[int, int]) -> None:
            janela = janelas.janela_mensagem("""<p align="justify">PyChatBot 2025.</p>""", tamanho)
            janela.exec()

        sobre.clicked.connect(lambda: sobre_pop((480, 240)))
        layout_sidebar.addWidget(sobre)
        layout_sidebar.addWidget(QPushButton("Opção 3"))
        layout_sidebar.addSpacing(15)

        titulo_conversas = QLabel("Conversas")
        titulo_conversas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_conversas.setStyleSheet(estilos.estilo_titulo_conversas())
        layout_sidebar.addWidget(titulo_conversas)
        layout_sidebar.addSpacing(15)

        try:
            for conversa in funcs.listar_conversas():
                caminho = os.path.join(os.getcwd(), "data", "conversas", conversa)
                if os.path.exists(caminho):
                    with open(caminho, "r", encoding="utf-8") as f:
                        resumo = f.read(21)
                        if len(resumo) > 20: resumo = resumo[:20] + "..."

                    botao_conversa = QPushButton(resumo)
                    botao_conversa.clicked.connect(lambda checked, c=conversa: self.recuperar_conversa(c))
                    botao_conversa.setStyleSheet(estilos.estilo_botao_conversa())
                    layout_sidebar.addWidget(botao_conversa, Qt.AlignmentFlag.AlignTop)
                    layout_sidebar.addSpacing(5)
        except Exception:
            pass

        layout_sidebar.addStretch()

        maximizador_menu = QPushButton()
        minimizar_sidebar()
        maximizador_menu.setIcon(QIcon(f"{self.orig_dir}\\ícones\\expansão_menu.svg"))
        maximizador_menu.clicked.connect(minimizar_sidebar)

        layout_geral = QHBoxLayout()
        layout_geral.addWidget(maximizador_menu, alignment=Qt.AlignmentFlag.AlignTop)
        layout_geral.addWidget(sidebar)
        layout_geral.addLayout(layout_principal_area)

        self.setLayout(layout_geral)
        self.setWindowIcon(QIcon(f"{self.orig_dir}\\ícones\\chatbot.svg"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MinhaJanela()
    janela.show()
    sys.exit(app.exec())
