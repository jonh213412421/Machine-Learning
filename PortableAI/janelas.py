from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect, QFrame, QHBoxLayout


class janela_mensagem(QDialog):
    def __init__(self, mensagem, tamanho):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # Remove a barra de título padrão
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # Fundo transparente para arredondamento

        # Variável para movimentação da janela
        self.old_pos = None

        # Dimensões
        if isinstance(tamanho, tuple):
            w, h = tamanho
            self.resize(w, h)
        else:
            self.setFixedSize(480, 280)

        # Layout Principal (transparente)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)  # Margem para a sombra não cortar
        self.setLayout(main_layout)

        # Container Visual (Frame Branco com bordas redondas)
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)

        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.container.setGraphicsEffect(shadow)

        main_layout.addWidget(self.container)

        # Layout interno do container
        content_layout = QVBoxLayout(self.container)
        content_layout.setContentsMargins(25, 20, 25, 20)

        # --- CABEÇALHO ---
        header_layout = QHBoxLayout()

        title = QLabel("Sobre")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #333; border: none; background: transparent;")

        # Botão X para fechar
        btn_close_x = QPushButton("×")
        btn_close_x.setFixedSize(30, 30)
        btn_close_x.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close_x.clicked.connect(self.accept)
        btn_close_x.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #999;
                font-size: 24px;
                font-weight: bold;
                border: none;
                padding-bottom: 3px;
            }
            QPushButton:hover {
                color: #ff5555;
            }
        """)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_close_x)

        content_layout.addLayout(header_layout)

        # --- MENSAGEM ---
        self.label = QLabel(mensagem)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Segoe UI", 11))
        self.label.setStyleSheet(
            "color: #555; border: none; background: transparent; margin-top: 5px; margin-bottom: 10px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.label.setOpenExternalLinks(True)

        content_layout.addWidget(self.label)
        content_layout.addStretch()

        # --- BOTÃO INFERIOR ---
        btn_ok = QPushButton("Entendido")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)
        btn_ok.setFixedSize(120, 35)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border-radius: 17px;
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #111;
                padding-top: 2px;
            }
        """)

        # Centralizar botão
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()

        content_layout.addLayout(btn_layout)

    # --- Lógica para arrastar a janela (necessário pois removemos a barra de título) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos and event.buttons() == Qt.MouseButton.LeftButton:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None
