import sys
import os
import re

# --- CONFIGURAÇÃO GRÁFICA ---
# Define que o PyQt deve usar o ANGLE (DirectX) em vez de OpenGL puro.
os.environ['QT_OPENGL'] = 'angle'
# ----------------------------

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

    def formatar_texto(self, texto: str) -> str:
        # Escape básico
        texto = (texto.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;")
                 .replace('"', "&quot;")
                 .replace("'", "&#39;"))
        # Markdown simples
        texto = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', texto)
        texto = re.sub(r'(?m)^### (.*)', r'<h3>\1</h3>', texto)
        texto = re.sub(r'(?m)^## (.*)', r'<h2>\1</h2>', texto)
        texto = re.sub(r'(?m)^# (.*)', r'<h1>\1</h1>', texto)
        return texto

    def adicionar_html(self, texto: str, remetente: str, raw_html: bool = False) -> None:
        if not self.chat_tela: return

        if raw_html:
            texto_final = texto
        else:
            texto_final = self.formatar_texto(texto)

        js_content = json.dumps(texto_final)

        # Script para rolar a tela após renderização do MathJax
        js_scroll_logic = """
            if (window.MathJax) {
                MathJax.typesetPromise().then(() => {
                    window.scrollTo(0, document.body.scrollHeight);
                });
            } else {
                window.scrollTo(0, document.body.scrollHeight);
            }
        """

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
                msg.style.whiteSpace = 'pre-wrap'; 
                msg.innerHTML = {js_content}; 
                wrapper.appendChild(msg);
                document.getElementById('chat').appendChild(wrapper);
                {js_scroll_logic}
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
                    msg.style.whiteSpace = 'pre-wrap'; 
                    msg.innerHTML = {js_content};
                    wrapper.appendChild(msg);
                    document.getElementById('chat').appendChild(wrapper);
                    {js_scroll_logic}
                """
                self.div_bot_criada = True
            else:
                js = f"""
                var wrapper = document.getElementById('msg_{self.j}');
                if (wrapper) {{
                    var msg_div = wrapper.querySelector('.bot');
                    msg_div.style.whiteSpace = 'pre-wrap'; 
                    var span = document.createElement('span');
                    span.innerHTML = {js_content};
                    msg_div.appendChild(span);
                    if (window.MathJax) {{ 
                        MathJax.typesetPromise([span]).then(() => {{
                             window.scrollTo(0, document.body.scrollHeight);
                        }}); 
                    }} else {{
                        window.scrollTo(0, document.body.scrollHeight);
                    }}
                }}
                """

        try:
            self.chat_tela.page().runJavaScript(js)
        except Exception as e:
            print("Error running JavaScript:", e)

    def limpar_chat(self):
        """Limpa a tela do chat mantendo o estilo base"""
        self.j = 0
        self.div_bot_criada = False
        if self.chat_tela:
            # FIX: Usar JS para limpar evita race condition com setHtml
            self.chat_tela.page().runJavaScript("document.getElementById('chat').innerHTML = '';")


class MinhaJanela(QWidget):
    def __init__(self):
        super().__init__()
        self.orig_dir = os.getcwd()
        self.thread = None
        self.sidebar_estendida = True
        self.gerando_resposta = False

        # --- ESTADO DA CONVERSA ---
        self.historico_atual = []
        self.nome_arquivo_atual = None
        self.buffer_resposta_bot = ""

        self.setWindowTitle("PyChatBot")
        self.setFixedSize(1024, 800)
        self.setup_ui()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress and source is self.chat_prompt:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return super().eventFilter(source, event)
                self.chat_botao.click()
                return True
        return super().eventFilter(source, event)

    # --- Métodos auxiliares de UI ---
    def desabilitar_controles(self) -> None:
        self.botao_arquivo.setDisabled(True)
        self.botao_modelo.setDisabled(True)

    def habilitar_controles(self) -> None:
        self.botao_arquivo.setDisabled(False)
        self.botao_modelo.setDisabled(False)

    def receber_parte_resposta(self, texto: str, remetente: str):
        """Chamado a cada pedaço de texto que o modelo gera"""
        self.chat_handler.adicionar_html(texto, remetente)
        if remetente == 'bot':
            self.buffer_resposta_bot += texto

    def on_resposta_finalizada(self) -> None:
        """Chamado quando o modelo termina (prompt >>> detectado)"""
        self.gerando_resposta = False
        self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
        self.habilitar_controles()

        # Salvar a resposta completa do bot no histórico
        if self.buffer_resposta_bot:
            self.historico_atual.append({"role": "bot", "content": self.buffer_resposta_bot})
            self.buffer_resposta_bot = ""
            self.salvar_conversa()

    def on_thread_finished(self) -> None:
        """Se a thread morrer inesperadamente"""
        if self.gerando_resposta:
            self.gerando_resposta = False
            self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
            self.habilitar_controles()
            if self.buffer_resposta_bot:
                self.historico_atual.append({"role": "bot", "content": self.buffer_resposta_bot})
                self.salvar_conversa()

    def salvar_conversa(self):
        """Salva a conversa atual em JSON e atualiza a lista lateral"""
        novo_nome = funcs.salvar_conversa_json(self.historico_atual, self.nome_arquivo_atual)
        if novo_nome:
            self.nome_arquivo_atual = novo_nome
            self.atualizar_lista_conversas()

    def nova_conversa(self):
        """Reseta o chat para uma nova conversa"""
        self.historico_atual = []
        self.nome_arquivo_atual = None
        self.buffer_resposta_bot = ""
        self.chat_handler.limpar_chat()

        if self.thread and self.thread.isRunning():
            self.thread.stop_thread()
            self.thread.wait()
            self.thread.deleteLater()
            self.thread = None
            self.gerando_resposta = False
            self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
            self.habilitar_controles()

    def recuperar_conversa(self, nome_arquivo: str) -> None:
        """Carrega uma conversa do arquivo JSON"""
        dados = funcs.ler_conversa_json(nome_arquivo)
        if not dados:
            return

        self.nova_conversa()
        self.historico_atual = dados
        self.nome_arquivo_atual = nome_arquivo

        for msg in self.historico_atual:
            self.chat_handler.adicionar_html(msg['content'], msg['role'])

    def excluir_conversa(self, nome_arquivo: str) -> None:
        """Exclui a conversa e atualiza a lista"""
        if funcs.excluir_conversa(nome_arquivo):
            # Se a conversa excluída for a atual, limpa a tela
            if self.nome_arquivo_atual == nome_arquivo:
                self.nova_conversa()
            self.atualizar_lista_conversas()

    def atualizar_lista_conversas(self):
        """Recria os botões da barra lateral"""
        if hasattr(self, 'layout_lista_conversas'):
            while self.layout_lista_conversas.count():
                item = self.layout_lista_conversas.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            # --- BOTÃO NOVA CONVERSA (AGORA NO TOPO DA LISTA) ---
            btn_nova = QPushButton("Nova Conversa +")
            # Estilo azulado para destacar
            btn_nova.setStyleSheet(estilos.estilo_botao_conversa().replace("rgb(180, 180, 180)", "rgb(173, 216, 230)"))
            btn_nova.clicked.connect(self.nova_conversa)
            self.layout_lista_conversas.addWidget(btn_nova)
            self.layout_lista_conversas.addSpacing(5)

            # --- LISTA DE CONVERSAS SALVAS ---
            for conversa in funcs.listar_conversas():
                caminho = os.path.join(os.getcwd(), "data", "conversas", conversa)
                texto_botao = conversa.replace(".json", "").replace("_", " ")[:18]
                try:
                    with open(caminho, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                        if dados and len(dados) > 0:
                            texto_botao = dados[0]['content'][:18] + "..."
                except:
                    pass

                # Container horizontal para [Botão Conversa] [Botão Excluir]
                container = QWidget()
                layout_h = QHBoxLayout(container)
                layout_h.setContentsMargins(0, 0, 0, 0)
                layout_h.setSpacing(2)

                # Botão da conversa
                botao = QPushButton(texto_botao)
                botao.clicked.connect(lambda checked, c=conversa: self.recuperar_conversa(c))
                botao.setStyleSheet(estilos.estilo_botao_conversa())

                # Botão de excluir
                btn_del = QPushButton("X")
                btn_del.setFixedSize(20, 30)  # Tamanho fixo pequeno
                btn_del.setStyleSheet("""
                    QPushButton {
                        background-color: #ff6b6b; color: white; border: none; border-radius: 3px; font-weight: bold;
                    }
                    QPushButton:hover { background-color: #ff4c4c; }
                """)
                btn_del.clicked.connect(lambda checked, c=conversa: self.excluir_conversa(c))

                layout_h.addWidget(botao)
                layout_h.addWidget(btn_del)

                self.layout_lista_conversas.addWidget(container)

            self.layout_lista_conversas.addStretch()

    def setup_ui(self):
        self.chat_handler = ChatHandler()
        self.chat_handler.orig_dir = self.orig_dir

        def click_botao_prompt() -> None:
            if self.gerando_resposta:
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

                self.habilitar_controles()
                return

            texto = self.chat_prompt.toPlainText().strip()
            if not texto:
                return

            self.gerando_resposta = True
            self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\trabalhando.svg"))
            self.chat_botao.repaint()

            self.desabilitar_controles()

            self.historico_atual.append({"role": "user", "content": texto})
            self.buffer_resposta_bot = ""

            if self.thread is None or not self.thread.isRunning():
                modelo_selecionado = self.botao_modelo.currentText()
                if not modelo_selecionado:
                    self.chat_tela.setHtml("<h3>Erro: Nenhum modelo selecionado.</h3>")
                    self.gerando_resposta = False
                    self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
                    return

                self.thread = PromptThread(modelo_selecionado)
                self.thread.linha.connect(self.receber_parte_resposta)
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
            try:
                nome_arquivo, dados_arquivo = funcs.carregar_arquivo()
                if nome_arquivo:
                    self.arquivo_carregado.setHtml(nome_arquivo)
                    self.arquivo_carregado.setAlignment(Qt.AlignmentFlag.AlignCenter)
            except Exception as e:
                print(f"Erro ao carregar arquivo: {e}")

        def minimizar_sidebar() -> None:
            width_atual = sidebar.width()
            if self.sidebar_estendida:
                destino = 0
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
                destino = 200
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

        self.chat_tela = QWebEngineView()
        self.chat_tela.setStyleSheet(estilos.estilo_chat_tela())
        self.chat_tela.setMinimumHeight(300)
        self.chat_tela.setMaximumHeight(700)
        self.chat_tela.setHtml(estilos.html_base())
        self.chat_handler.chat_tela = self.chat_tela

        self.prompt_barra = QHBoxLayout()
        self.chat_prompt = QTextEdit()
        self.chat_prompt.setMaximumHeight(40)
        self.chat_prompt.setMinimumWidth(900)
        self.chat_prompt.setFont(QFont("Arial", 12))
        self.chat_prompt.textChanged.connect(esconder_mostrar_botao)
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

        self.botao_modelo = QComboBox()
        try:
            modelos = funcs.listar_modelos()
            for modelo in modelos: self.botao_modelo.addItem(modelo)
        except:
            self.botao_modelo.addItem("Nenhum modelo encontrado")

        self.botao_modelo.addItem("Adicionar modelo")

        # --- LÓGICA DE TROCA DE MODELO ATUALIZADA ---
        def ao_trocar_modelo(index):
            texto_atual = self.botao_modelo.currentText()

            if texto_atual == "Adicionar modelo":
                # Bloqueia sinais para não disparar eventos recursivos
                self.botao_modelo.blockSignals(True)

                novo_modelo = funcs.adicionar_modelo_gguf()

                # Limpa e recarrega a lista
                self.botao_modelo.clear()
                modelos_atualizados = funcs.listar_modelos()
                for m in modelos_atualizados:
                    self.botao_modelo.addItem(m)
                self.botao_modelo.addItem("Adicionar modelo")

                if novo_modelo:
                    # Seleciona o novo modelo
                    self.botao_modelo.setCurrentText(novo_modelo)
                else:
                    # Se cancelou, volta para o primeiro da lista
                    if self.botao_modelo.count() > 1:
                        self.botao_modelo.setCurrentIndex(0)

                self.botao_modelo.blockSignals(False)

        self.botao_modelo.currentIndexChanged.connect(ao_trocar_modelo)
        self.botao_modelo.setMaximumWidth(600)
        self.botao_modelo.setMinimumWidth(250)
        self.botao_modelo.setMinimumHeight(20)
        self.botao_modelo.setMaximumHeight(40)
        self.botao_modelo.setStyleSheet(estilos.estilo_botao_modelos())

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

        # REMOVIDO DAQUI O BOTÃO DE NOVA CONVERSA - AGORA ESTÁ EM atualizar_lista_conversas

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

        def sobre_pop(tamanho):
            texto_sobre = """
           <p align="justify">
           <b>PyChatBot Portable</b><br><br>
           Este programa foi criado por <b>João Alberto</b> em 2025.<br><br>
           Ele nasceu do meu profundo amor e fascínio por Large Language Models (LLMs). 
           O objetivo deste projeto é tornar essa tecnologia incrível acessível, privada e portátil para todos, 
           permitindo explorar o potencial da IA diretamente do seu computador.
           </p>
           """
            janela = janelas.janela_mensagem(texto_sobre, tamanho)
            janela.exec()

        sobre.clicked.connect(lambda: sobre_pop((480, 300)))
        layout_sidebar.addWidget(sobre)
        layout_sidebar.addWidget(QPushButton("Opção 3"))
        layout_sidebar.addSpacing(15)

        titulo_conversas = QLabel("Histórico")
        titulo_conversas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_conversas.setStyleSheet(estilos.estilo_titulo_conversas())
        layout_sidebar.addWidget(titulo_conversas)
        layout_sidebar.addSpacing(5)

        self.layout_lista_conversas = QVBoxLayout()
        layout_sidebar.addLayout(self.layout_lista_conversas)
        self.atualizar_lista_conversas()

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

        self.atalho_enter = QShortcut(QKeySequence("Return"), self)
        self.atalho_enter.activated.connect(click_botao_prompt)
        self.atalho_enter_num = QShortcut(QKeySequence("Enter"), self)
        self.atalho_enter_num.activated.connect(click_botao_prompt)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MinhaJanela()
    janela.show()
    sys.exit(app.exec())
