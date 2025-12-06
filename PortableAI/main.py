import sys
import os
import re

# Configuração gráfica
os.environ['QT_OPENGL'] = 'angle'

import json
import funcs
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent
from PyQt6.QtGui import QIcon, QFont, QShortcut, QKeySequence, QColor, QPixmap, QTransform
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit, \
    QFrame, QSlider, QGraphicsDropShadowEffect, QSizePolicy, QLineEdit
from PyQt6.QtWebEngineWidgets import QWebEngineView
import janelas
import estilos
from threads import PromptThread, CarregarArquivoThread

# Tenta importar markdown com segurança
try:
    import markdown

    TEM_MARKDOWN = True
except ImportError:
    TEM_MARKDOWN = False
    print("AVISO: Biblioteca 'markdown' não encontrada. Instale com 'pip install markdown' para formatação correta.")


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

    def formatar_texto(self, texto: str, limpar_artefatos: bool = True) -> str:
        """
        Formata o texto para HTML/Markdown.
        :param texto: O texto a ser formatado.
        :param limpar_artefatos: Se True, remove saudações e artefatos de IA (usar apenas para o Bot).
        """
        texto_limpo = texto

        # 1. Limpeza de artefatos (Garbage Collection Refinada) - APENAS SE SOLICITADO
        if limpar_artefatos:
            def limpar_recursivo(t):
                # Remove saudações, roles e lixo comum de início de resposta
                padrao = r'^[\s\W]*(?:Hello|Hi|Olá|Oi|Saudações|Claro|Certo|Aqui está|Abaixo|system|user|assistant|analysis|model|context|###|[:\-]|\d+\/)+'
                novo_t = re.sub(padrao, '', t, flags=re.IGNORECASE).strip()
                return novo_t

            for _ in range(10):
                temp = limpar_recursivo(texto_limpo)
                if temp == texto_limpo:
                    break
                texto_limpo = temp
            texto = texto_limpo

        # 2. Normalização básica pré-processamento
        texto = re.sub(r'^(#+)([^ \n])', r'\1 \2', texto, flags=re.MULTILINE)  # Headers
        texto = re.sub(r'-{2,}\s*#{2,}', '\n\n', texto)  # Separadores ruins
        texto = texto.replace("||", "|\n|")  # Quebra de linhas de tabela coladas

        # 3. Processamento de Blocos (Máquina de Estados para Tabelas)
        lines = texto.splitlines()
        processed_lines = []
        in_table = False

        # Regex simples para identificar se a linha tem cara de tabela (tem pelo menos um pipe)
        table_row_pattern = re.compile(r'\|')

        for line in lines:
            line = line.strip()

            # Se a linha está vazia
            if not line:
                if in_table:
                    continue  # Ignora (remove) linhas vazias DENTRO de tabelas para compactar
                else:
                    processed_lines.append('')  # Mantém linhas vazias fora
                continue

            # Verifica se é linha de tabela (e ignora blocos de código )
            is_table_row = table_row_pattern.search(line) and not line.startswith('')

            if is_table_row:
                # Normaliza pipes nas bordas (Obrigatório para o parser)
                if not line.startswith('|'): line = '| ' + line
                if not line.endswith('|'): line = line + ' |'

                if not in_table:
                    # Entrando no modo tabela
                    in_table = True
                    # Garante linha em branco antes da tabela (Requisito do Markdown)
                    if processed_lines and processed_lines[-1] != '':
                        processed_lines.append('')

                processed_lines.append(line)
            else:
                if in_table:
                    # Saindo do modo tabela
                    in_table = False
                    processed_lines.append('')  # Garante separação ao sair

                processed_lines.append(line)

        texto = '\n'.join(processed_lines)

        # 4. Ajustes finais e Conversão
        if TEM_MARKDOWN:
            try:
                # Usa extensões essenciais
                html = markdown.markdown(texto, extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists'])

                # CSS Injetado (Estilo Limpo e Profissional)
                estilo_css = """
                <style>
                    table {
                        border-collapse: collapse;
                        width: 100%;
                        margin: 1rem 0;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                        font-size: 14px;
                        line-height: 1.5;
                        color: #24292e;
                        border: 1px solid #dfe2e5;
                        background-color: #fff;
                    }
                    thead {
                        display: table-header-group;
                        vertical-align: middle;
                        border-color: inherit;
                    }
                    tr {
                        background-color: #fff;
                        border-top: 1px solid #c6cbd1;
                    }
                    tr:nth-child(2n) {
                        background-color: #f6f8fa;
                    }
                    th, td {
                        padding: 8px 13px;
                        border: 1px solid #dfe2e5;
                        text-align: left;
                    }
                    th {
                        font-weight: 600;
                        background-color: #f3f4f4;
                    }
                </style>
                """
                return estilo_css + html
            except Exception as e:
                print(f"Erro Markdown: {e}")

        return texto.replace("\n", "<br>")

    def mostrar_digitando(self):
        if not self.chat_tela: return

        js = """
        (function() {
            var chat = document.getElementById('chat');
            if (!chat) return;

            var old = document.getElementById('typing_indicator');
            if (old) old.remove();

            var wrapper = document.createElement('div');
            wrapper.id = 'typing_indicator';
            wrapper.className = 'msg-wrapper bot-wrapper';
            var msg = document.createElement('div');
            msg.className = 'msg bot';
            msg.innerHTML = '<div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';

            wrapper.appendChild(msg);
            chat.appendChild(wrapper);
            window.scrollTo(0, document.body.scrollHeight);
        })();
        """
        self.chat_tela.page().runJavaScript(js)

    def esconder_digitando(self):
        if not self.chat_tela: return
        js = "var el = document.getElementById('typing_indicator'); if(el) el.remove();"
        self.chat_tela.page().runJavaScript(js)

    def adicionar_aviso(self, html_aviso: str):
        if not self.chat_tela: return

        js_content = json.dumps(html_aviso)
        js = f"""
        (function() {{
            var chat = document.getElementById('chat');
            if (!chat) return;

            var typing = document.getElementById('typing_indicator');
            if(typing) typing.remove();

            var wrapper = document.createElement('div');
            wrapper.className = 'msg-wrapper bot-wrapper'; 

            var msg = document.createElement('div');
            msg.className = 'msg bot'; 
            msg.innerHTML = {js_content};

            wrapper.appendChild(msg);
            chat.appendChild(wrapper);
            window.scrollTo(0, document.body.scrollHeight);
        }})();
        """
        self.chat_tela.page().runJavaScript(js)

    def adicionar_html(self, texto: str, remetente: str, raw_html: bool = False, streaming: bool = False) -> None:
        if not self.chat_tela: return

        if raw_html:
            texto_final = texto
        else:
            if remetente == 'bot':
                texto_final = self.formatar_texto(texto, limpar_artefatos=True)
            elif remetente == 'user':
                texto_final = self.formatar_texto(texto, limpar_artefatos=False)
            else:
                texto_limpo = re.sub(r'^(system|user|assistant)+', '', texto, flags=re.IGNORECASE)
                texto_final = (texto_limpo.replace("&", "&amp;")
                               .replace("<", "&lt;")
                               .replace(">", "&gt;")
                               .replace("\n", "<br>"))

        js_content = json.dumps(texto_final)
        js_scroll = "window.scrollTo(0, document.body.scrollHeight);"

        js_mathjax = ""
        # MathJax só roda na mensagem final do bot
        if not streaming and remetente == 'bot':
            js_mathjax = "if(window.MathJax && typeof msg_div !== 'undefined') { MathJax.typesetPromise([msg_div]).then(() => " + js_scroll + "); }"

        if remetente == 'user':
            wrapper_id = f"msg_{self.j}"
            wrapper_class = "user-wrapper"
            msg_class = "user"
            self.div_bot_criada = False
            self.j += 1

            js = f"""
            (function() {{
                var chat = document.getElementById('chat');
                if (!chat) return;

                var wrapper = document.createElement('div');
                wrapper.id = '{wrapper_id}';
                wrapper.className = '{wrapper_class} msg-wrapper';
                var msg = document.createElement('div');
                msg.className = '{msg_class} msg';
                msg.innerHTML = {js_content}; 
                wrapper.appendChild(msg);
                chat.appendChild(wrapper);

                var typing = document.getElementById('typing_indicator');
                if (typing) chat.appendChild(typing);

                {js_scroll}
            }})();
            """

        else:  # BOT
            if not self.div_bot_criada:
                wrapper_id = f"msg_{self.j}"
                self.div_bot_criada = True
                self.j += 1

                js = f"""
                (function() {{
                    var chat = document.getElementById('chat');
                    if (!chat) return;

                    var wrapper = document.createElement('div');
                    wrapper.id = '{wrapper_id}';
                    wrapper.className = 'bot-wrapper msg-wrapper';
                    var msg = document.createElement('div');
                    msg.className = 'bot msg';
                    var msg_div = msg;
                    msg.innerHTML = {js_content};
                    wrapper.appendChild(msg);
                    chat.appendChild(wrapper);

                    var typing = document.getElementById('typing_indicator');
                    if (typing) chat.appendChild(typing);
                    else if ({str(streaming).lower()}) {{
                        var tWrap = document.createElement('div');
                        tWrap.id = 'typing_indicator';
                        tWrap.className = 'msg-wrapper bot-wrapper';
                        tWrap.innerHTML = '<div class="msg bot"><div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>';
                        chat.appendChild(tWrap);
                    }}

                    {js_mathjax}
                    if (!window.MathJax) {{ {js_scroll} }}
                }})();
                """
            else:
                prev_id = f"msg_{self.j - 1}"

                js = f"""
                (function() {{
                    var wrapper = document.getElementById('{prev_id}');
                    if (wrapper) {{
                        var msg_div = wrapper.querySelector('.bot');
                        msg_div.innerHTML = {js_content};

                        var chat = document.getElementById('chat');
                        var typing = document.getElementById('typing_indicator');

                        if ({str(streaming).lower()}) {{
                             if (!typing) {{
                                 var tWrap = document.createElement('div');
                                 tWrap.id = 'typing_indicator';
                                 tWrap.className = 'msg-wrapper bot-wrapper';
                                 tWrap.innerHTML = '<div class="msg bot"><div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div></div>';
                                 chat.appendChild(tWrap);
                             }} else if (chat.lastElementChild !== typing) {{
                                 chat.appendChild(typing);
                             }}
                        }}

                        {js_mathjax}
                        if (!window.MathJax) {{ {js_scroll} }}
                    }}
                }})();
                """

        self.chat_tela.page().runJavaScript(js)

    def limpar_chat(self):
        self.j = 0
        self.div_bot_criada = False
        if self.chat_tela:
            self.chat_tela.page().runJavaScript("document.getElementById('chat').innerHTML = '';")


class MinhaJanela(QWidget):
    def __init__(self):
        super().__init__()
        self.orig_dir = os.getcwd()
        self.thread = None
        self.sidebar_estendida = True
        self.gerando_resposta = False

        self.historico_atual = []
        self.nome_arquivo_atual = None
        self.buffer_resposta_bot = ""

        self.setWindowTitle("PyChatBot")
        self.setMinimumSize(900, 700)
        self.resize(1024, 800)
        self.setup_ui()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress and source is self.chat_prompt:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return super().eventFilter(source, event)
                self.chat_botao.click()
                return True
        return super().eventFilter(source, event)

    def desabilitar_controles(self) -> None:
        self.botao_arquivo.setDisabled(True)
        self.botao_modelo.setDisabled(True)
        self.slider_temp.setDisabled(True)

    def habilitar_controles(self) -> None:
        self.botao_arquivo.setDisabled(False)
        self.botao_modelo.setDisabled(False)
        if self.thread is None or not self.thread.isRunning():
            self.slider_temp.setDisabled(False)

    def receber_parte_resposta(self, texto: str, remetente: str):
        if remetente == 'bot':
            self.buffer_resposta_bot += texto
            self.chat_handler.adicionar_html(self.buffer_resposta_bot, remetente, streaming=True)
        else:
            pass

    def on_resposta_finalizada(self) -> None:
        self.gerando_resposta = False
        self.chat_handler.esconder_digitando()
        self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
        self.habilitar_controles()

        if self.buffer_resposta_bot:
            self.chat_handler.adicionar_html(self.buffer_resposta_bot, 'bot', streaming=False)
            self.historico_atual.append({"role": "bot", "content": self.buffer_resposta_bot})
            self.buffer_resposta_bot = ""
            self.salvar_conversa()

    def on_thread_finished(self) -> None:
        if self.gerando_resposta:
            self.gerando_resposta = False
            self.chat_handler.esconder_digitando()
            self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
            self.habilitar_controles()
            if self.buffer_resposta_bot:
                self.historico_atual.append({"role": "bot", "content": self.buffer_resposta_bot})
                self.salvar_conversa()

    def salvar_conversa(self):
        novo_nome = funcs.salvar_conversa_json(self.historico_atual, self.nome_arquivo_atual)
        if novo_nome:
            self.nome_arquivo_atual = novo_nome
            self.atualizar_lista_conversas()

    def nova_conversa(self):
        self.historico_atual = []
        self.nome_arquivo_atual = None
        self.buffer_resposta_bot = ""
        self.chat_handler.limpar_chat()
        self.chat_handler.esconder_digitando()

        if self.thread and self.thread.isRunning():
            self.thread.stop_thread()
            self.thread.wait()
            self.thread.deleteLater()
            self.thread = None

        self.gerando_resposta = False
        self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
        self.habilitar_controles()

        if hasattr(self, 'botao_parar'):
            self.botao_parar.setVisible(False)

    def recuperar_conversa(self, nome_arquivo: str) -> None:
        dados = funcs.ler_conversa_json(nome_arquivo)
        if not dados: return
        self.nova_conversa()
        self.historico_atual = dados
        self.nome_arquivo_atual = nome_arquivo
        for msg in self.historico_atual:
            self.chat_handler.adicionar_html(msg['content'], msg['role'], streaming=False)

    def excluir_conversa(self, nome_arquivo: str) -> None:
        if funcs.excluir_conversa(nome_arquivo):
            if self.nome_arquivo_atual == nome_arquivo:
                self.nova_conversa()
            self.atualizar_lista_conversas()

    def atualizar_lista_conversas(self):
        if hasattr(self, 'layout_lista_conversas'):
            while self.layout_lista_conversas.count():
                item = self.layout_lista_conversas.takeAt(0)
                if item.widget(): item.widget().deleteLater()

            btn_nova = QPushButton("Nova Conversa +")
            btn_nova.setStyleSheet(estilos.estilo_botao_conversa().replace("rgb(180, 180, 180)", "rgb(173, 216, 230)"))
            btn_nova.clicked.connect(self.nova_conversa)
            self.layout_lista_conversas.addWidget(btn_nova)
            self.layout_lista_conversas.addSpacing(5)

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

                container = QWidget()
                layout_h = QHBoxLayout(container)
                layout_h.setContentsMargins(0, 0, 0, 0)
                layout_h.setSpacing(2)

                botao = QPushButton(texto_botao)
                botao.clicked.connect(lambda checked, c=conversa: self.recuperar_conversa(c))
                botao.setStyleSheet(estilos.estilo_botao_conversa())

                btn_del = QPushButton("X")
                btn_del.setFixedSize(20, 30)
                btn_del.setStyleSheet(
                    "QPushButton { background-color: #ff6b6b; color: white; border: none; border-radius: 3px; font-weight: bold; } QPushButton:hover { background-color: #ff4c4c; }")
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
                self.chat_handler.esconder_digitando()
                self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))

                msg_cancel = estilos.mensagem_operacao_cancelada()

                if self.buffer_resposta_bot:
                    self.chat_handler.adicionar_html(self.buffer_resposta_bot, 'bot', streaming=False)
                    self.historico_atual.append({"role": "bot", "content": self.buffer_resposta_bot + " [Cancelado]"})

                self.chat_handler.adicionar_aviso(msg_cancel)
                self.buffer_resposta_bot = ""
                self.habilitar_controles()
                return

            texto = self.chat_prompt.toPlainText().strip()
            if not texto: return

            self.gerando_resposta = True
            self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\trabalhando.svg"))
            self.chat_botao.repaint()
            self.desabilitar_controles()

            self.historico_atual.append({"role": "user", "content": texto})
            self.buffer_resposta_bot = ""

            self.chat_handler.adicionar_html(texto, 'user', streaming=False)
            self.chat_handler.mostrar_digitando()

            if self.thread is None or not self.thread.isRunning():
                modelo_selecionado = self.botao_modelo.currentText()
                if not modelo_selecionado:
                    self.chat_tela.setHtml("<h3>Erro: Nenhum modelo selecionado.</h3>")
                    self.gerando_resposta = False
                    self.chat_handler.esconder_digitando()
                    self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
                    self.habilitar_controles()
                    return

                try:
                    temp_val = self.slider_temp.value() / 100.0
                except:
                    temp_val = 0.7

                self.thread = PromptThread(modelo_selecionado, temperature=temp_val, n_experts=0)
                self.thread.linha.connect(self.receber_parte_resposta)
                self.thread.erro.connect(lambda e: print(f"Erro Thread: {e}"))
                self.thread.sinal_resposta_finalizada.connect(self.on_resposta_finalizada)
                self.thread.finished.connect(self.on_thread_finished)
                self.thread.start()

                self.botao_parar.setVisible(True)

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
                    # ALTERADO DE setHtml PARA setText
                    self.arquivo_carregado.setText(nome_arquivo)
                    self.arquivo_carregado.setAlignment(Qt.AlignmentFlag.AlignCenter)
            except Exception as e:
                print(f"Erro ao carregar arquivo: {e}")

        def minimizar_sidebar() -> None:
            width_atual = sidebar.width()
            if self.sidebar_estendida:
                destino = 0
                self.sidebar_estendida = False
                self.animacao_sidebar = QPropertyAnimation(sidebar, b"maximumWidth")
                self.animacao_sidebar.setDuration(300)
                self.animacao_sidebar.setStartValue(width_atual)
                self.animacao_sidebar.setEndValue(destino)
                self.animacao_sidebar.setEasingCurve(QEasingCurve.Type.InOutBack)
                self.animacao_sidebar.start()
                maximizador_menu.setIcon(QIcon(f"{self.orig_dir}\\ícones\\expansão_menu.svg"))
            else:
                destino = 200
                self.sidebar_estendida = True
                self.animacao_sidebar = QPropertyAnimation(sidebar, b"maximumWidth")
                self.animacao_sidebar.setDuration(300)
                self.animacao_sidebar.setStartValue(width_atual)
                self.animacao_sidebar.setEndValue(destino)
                self.animacao_sidebar.setEasingCurve(QEasingCurve.Type.InOutCubic)
                self.animacao_sidebar.start()

                # Inverte o ícone para indicar recolhimento (espelha horizontalmente)
                icon_base = QIcon(f"{self.orig_dir}\\ícones\\expansão_menu.svg")
                pixmap = icon_base.pixmap(64, 64)
                transformed_pixmap = pixmap.transformed(QTransform().scale(-1, 1))
                maximizador_menu.setIcon(QIcon(transformed_pixmap))

        self.chat_tela = QWebEngineView()
        self.chat_tela.setStyleSheet(estilos.estilo_chat_tela())
        self.chat_tela.setMinimumHeight(300)
        self.chat_tela.setHtml(estilos.html_base())
        self.chat_handler.chat_tela = self.chat_tela

        self.prompt_barra = QHBoxLayout()
        self.prompt_barra.setSpacing(5)

        self.chat_prompt = QTextEdit()
        self.chat_prompt.setMaximumHeight(40)
        self.chat_prompt.setFont(QFont("Arial", 12))
        self.chat_prompt.textChanged.connect(esconder_mostrar_botao)
        self.chat_prompt.installEventFilter(self)
        self.chat_prompt.setAcceptRichText(False)

        self.chat_prompt.setStyleSheet("""
           QTextEdit {
               color: black;
               background-color: white;
               border: 2px solid #aaa; 
               border-radius: 10px;
               padding: 8px;
               font-size: 14px;
           }
           QTextEdit:focus {
               border: 2px solid #5c9eff; 
           }
       """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.chat_prompt.setGraphicsEffect(shadow)

        self.chat_botao = QPushButton()
        self.chat_botao.setIcon(QIcon(f"{os.getcwd()}\\ícones\\seta_enviar.svg"))
        self.chat_botao.setMinimumWidth(50)
        self.chat_botao.setMinimumHeight(20)
        self.chat_botao.setMaximumHeight(40)
        self.chat_botao.setStyleSheet(estilos.estilo_chat_botao())
        self.chat_botao.clicked.connect(click_botao_prompt)
        self.chat_botao.setVisible(False)
        self.chat_handler.chat_botao = self.chat_botao

        self.prompt_barra.addWidget(self.chat_prompt, stretch=1)
        self.prompt_barra.addWidget(self.chat_botao, stretch=0)

        self.botao_modelo = QComboBox()
        try:
            modelos = funcs.listar_modelos()
            for modelo in modelos: self.botao_modelo.addItem(modelo)
        except:
            self.botao_modelo.addItem("Nenhum modelo encontrado")

        self.botao_modelo.addItem("Adicionar modelo")

        def ao_trocar_modelo(index):
            texto_atual = self.botao_modelo.currentText()
            if texto_atual == "Adicionar modelo":
                self.botao_modelo.blockSignals(True)
                novo_modelo = funcs.adicionar_modelo_gguf()
                self.botao_modelo.clear()
                modelos_atualizados = funcs.listar_modelos()
                for m in modelos_atualizados: self.botao_modelo.addItem(m)
                self.botao_modelo.addItem("Adicionar modelo")
                if novo_modelo:
                    self.botao_modelo.setCurrentText(novo_modelo)
                    self.nova_conversa()
                else:
                    if self.botao_modelo.count() > 1: self.botao_modelo.setCurrentIndex(0)
                self.botao_modelo.blockSignals(False)
            else:
                self.nova_conversa()

        self.botao_modelo.currentIndexChanged.connect(ao_trocar_modelo)
        self.botao_modelo.setMaximumWidth(600)
        self.botao_modelo.setMinimumWidth(250)
        self.botao_modelo.setMinimumHeight(35)
        self.botao_modelo.setMaximumHeight(50)
        self.botao_modelo.setStyleSheet(estilos.estilo_botao_modelos())

        # --- BOTÃO PARAR MODELO ---
        self.botao_parar = QPushButton("Parar Modelo")
        self.botao_parar.setMinimumHeight(35)
        self.botao_parar.setMaximumHeight(50)
        self.botao_parar.setMinimumWidth(250)
        self.botao_parar.setMaximumWidth(600)

        self.botao_parar.setStyleSheet("""
           QPushButton {
               background-color: #ffcccc; 
               border: 1px solid #ff8888; 
               border-radius: 10px; 
               color: #330000;
               font-family: Segoe UI;
               font-size: 12px;
               font-weight: bold;
               padding: 5px;
           }
           QPushButton:hover { background-color: #ffaaaa; }
           QPushButton:pressed { background-color: #ff8888; }
       """)
        self.botao_parar.clicked.connect(self.nova_conversa)
        self.botao_parar.setVisible(False)

        self.botao_arquivo = QPushButton("Carregar Arquivo")
        self.botao_arquivo.setMaximumWidth(200)
        self.botao_arquivo.setMinimumWidth(120)  # Leve aumento na largura
        self.botao_arquivo.setMinimumHeight(35)  # AUMENTADO de 20 para 35
        self.botao_arquivo.setMaximumHeight(50)  # AUMENTADO de 40 para 50
        self.botao_arquivo.setStyleSheet(estilos.estilo_botao_arquivo())
        self.botao_arquivo.clicked.connect(carregar_arquivo)

        # --- MODIFICAÇÃO: SUBSTITUÍDO QTextEdit POR QLineEdit PARA ARREDONDAMENTO CORRETO ---
        self.arquivo_carregado = QLineEdit()
        self.arquivo_carregado.setReadOnly(True)
        self.arquivo_carregado.setText("Nenhum arquivo carregado")
        self.arquivo_carregado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.arquivo_carregado.setStyleSheet(estilos.estilo_arquivo_carregado())
        self.arquivo_carregado.setMaximumWidth(200)
        self.arquivo_carregado.setMinimumWidth(120)
        self.arquivo_carregado.setMinimumHeight(35)
        self.arquivo_carregado.setMaximumHeight(50)

        # --- LAYOUT MODELOS + PARAR ---
        layout_modelo_vertical = QVBoxLayout()
        layout_modelo_vertical.setSpacing(10)
        layout_modelo_vertical.setContentsMargins(0, 0, 0, 0)
        layout_modelo_vertical.addWidget(self.botao_modelo)
        layout_modelo_vertical.addWidget(self.botao_parar)

        layout_inferior = QHBoxLayout()
        layout_inferior.addLayout(layout_modelo_vertical)
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

        lbl_temp = QLabel("Temperatura")
        lbl_temp.setStyleSheet(estilos.estilo_titulo_quantidade_tokens_arquivo())
        layout_sidebar.addWidget(lbl_temp)

        self.slider_temp = QSlider(Qt.Orientation.Horizontal)
        self.slider_temp.setMinimum(0)
        self.slider_temp.setMaximum(500)
        self.slider_temp.setValue(70)

        self.mostrador_temp = QTextEdit()
        self.mostrador_temp.setReadOnly(True)
        self.mostrador_temp.setMaximumHeight(22)
        self.mostrador_temp.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mostrador_temp.setText("0.70")
        self.mostrador_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mostrador_temp.setStyleSheet(estilos.estilo_mostrar_quantidade_tokens_arquivo())

        def atualizar_temp(valor):
            temp_float = valor / 100.0
            self.mostrador_temp.setText(f"{temp_float:.2f}")
            self.mostrador_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.slider_temp.valueChanged.connect(atualizar_temp)
        layout_sidebar.addWidget(self.slider_temp)
        layout_sidebar.addWidget(self.mostrador_temp)
        layout_sidebar.addSpacing(15)

        quantidade_tokens_arquivo = QVBoxLayout()
        titulo_tokens = QLabel("Limite de Tokens")
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

        def atualizar_tokens(v):
            mostrador_tokens.setText(str(v))
            mostrador_tokens.setAlignment(Qt.AlignmentFlag.AlignCenter)

        slider_tokens.valueChanged.connect(lambda v: atualizar_tokens(v))

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
