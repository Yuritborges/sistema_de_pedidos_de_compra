# app/ui/main_window.py
# Janela principal do sistema com sidebar de navegação.

import os
import traceback

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QSplashScreen, QApplication,
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QPixmap, QIcon, QFont, QShortcut, QKeySequence, QColor, QPainter

from app.ui.widgets.formulario_pedido import PedidoWidget
from app.ui.widgets.obras_widget import ObrasWidget
from app.ui.widgets.cotacao_widget import CotacaoWidget
from app.ui.widgets.historico_widget import HistoricoWidget
from app.ui.widgets.pedidos_widget import PedidosWidget
from PySide6.QtGui import QIcon


# Nova aba de manutenção de cadastros
try:
    from app.ui.widgets.cadastros_widget import CadastrosWidget
except Exception as e:
    CadastrosWidget = None
    CADASTROS_IMPORT_ERROR = e
    CADASTROS_IMPORT_TRACEBACK = traceback.format_exc()
else:
    CADASTROS_IMPORT_ERROR = None
    CADASTROS_IMPORT_TRACEBACK = ""


_HERE = os.path.dirname(os.path.abspath(__file__))

# Cores da sidebar
S_BG = "#F0EDED"
S_ITEM = "#E8DEDE"
S_SEL = "#FDECEA"
S_EDGE = "#C0392B"
S_LINE = "#DCCECE"
S_TEXT = "#6B5555"
S_ATXT = "#C0392B"
C_BG = "#F0EDED"

# Ordem das abas para atalhos Ctrl+1..6
ORDEM_ABAS = ["pedido", "pedidos", "cotacao", "obras", "historico", "cadastros"]


def _icone_app_path():
    base = os.path.normpath(os.path.join(_HERE, "..", ".."))
    candidatos = [
        os.path.join(base, "assets", "logos", "logo_brasul.ico"),
        os.path.join(base, "assets", "iconebrasul2.ico"),
        os.path.join(base, "assets", "logo.ico"),
        os.path.join(base, "assets", "logos", "logo_brasul.png"),
        os.path.join(base, "assets", "logo_brasul.png"),
    ]
    return next((p for p in candidatos if os.path.exists(p)), "")


def criar_splash():
    # Cria a tela de splash enquanto o sistema carrega
    logo_path = os.path.normpath(
        os.path.join(_HERE, '..', '..', 'assets', 'logos', 'logo_brasul.png')
    )

    # Cria pixmap base da splash (500x280)
    pix = QPixmap(500, 280)
    pix.fill(QColor("#FFFFFF"))

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)

    # Fundo com gradiente lateral vermelho
    painter.fillRect(0, 0, 8, 280, QColor("#C0392B"))

    # Logo se existir
    if os.path.exists(logo_path):
        logo = QPixmap(logo_path).scaled(
            220, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (500 - logo.width()) // 2
        painter.drawPixmap(x, 60, logo)
        y_texto = 165
    else:
        fonte_nome = QFont("Arial", 28, QFont.Bold)
        painter.setFont(fonte_nome)
        painter.setPen(QColor("#C0392B"))
        painter.drawText(pix.rect(), Qt.AlignCenter, "BRASUL")
        y_texto = 180

    # Texto "Carregando..."
    fonte_sub = QFont("Arial", 11)
    painter.setFont(fonte_sub)
    painter.setPen(QColor("#6B5555"))
    painter.drawText(0, y_texto, 500, 30, Qt.AlignCenter, "Sistema de Pedidos")

    fonte_carr = QFont("Arial", 9)
    painter.setFont(fonte_carr)
    painter.setPen(QColor("#AAAAAA"))
    painter.drawText(0, y_texto + 32, 500, 24, Qt.AlignCenter, "Carregando...")

    # Borda suave embaixo
    painter.setPen(QColor("#E8DEDE"))
    painter.drawLine(20, 270, 480, 270)

    painter.end()

    splash = QSplashScreen(pix, Qt.WindowStaysOnTopHint)
    splash.setFont(QFont("Arial", 9))
    return splash


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        icon_path = _icone_app_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("Sistema de Pedidos — Brasul Construtora")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 820)
        self._build()
        self._registrar_atalhos()

        # Ícone da janela (mantém fallback único)
        icon_path = _icone_app_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

    def _build(self):
        root = QWidget()
        self.setCentralWidget(root)

        lay = QHBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._sidebar())

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background:{C_BG};")
        lay.addWidget(self._stack, 1)

        self._pages = {
            "pedido": PedidoWidget(),
            "pedidos": PedidosWidget(),
            "cotacao": CotacaoWidget(),
            "obras": ObrasWidget(),
            "historico": HistoricoWidget(),
            "cadastros": self._criar_pagina_cadastros(),
        }

        for p in self._pages.values():
            self._stack.addWidget(p)

        self._nav("pedido")

    def _criar_pagina_cadastros(self):
        if CadastrosWidget is not None:
            return CadastrosWidget()

        # Página de fallback para o programa abrir mesmo se o widget de cadastros tiver erro
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Erro ao carregar a aba Cadastros")
        title.setStyleSheet("font-size:18px; font-weight:bold; color:#C0392B;")

        msg = QLabel(
            "O sistema abriu, mas a aba Cadastros não pôde ser carregada.\n\n"
            "Verifique se o arquivo existe em:\n"
            "app/ui/widgets/cadastros_widget.py\n\n"
            f"Erro:\n{CADASTROS_IMPORT_ERROR}"
        )
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size:12px; color:#333;")

        lay.addWidget(title)
        lay.addWidget(msg)
        lay.addStretch()
        return page

    def _registrar_atalhos(self):
        # Ctrl+1 a Ctrl+6 navegam entre abas
        for i, key in enumerate(ORDEM_ABAS, start=1):
            atalho = QShortcut(QKeySequence(f"Ctrl+{i}"), self)
            atalho.activated.connect(lambda k=key: self._nav(k))

    def _sidebar(self):
        side = QFrame()
        side.setFixedWidth(220)
        side.setStyleSheet(f"QFrame{{background:{S_BG};border-right:1px solid {S_LINE};}}")

        vl = QVBoxLayout(side)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        # Área do logo
        top = QWidget()
        top.setFixedHeight(96)
        top.setStyleSheet("background:#FFFFFF; border-bottom:3px solid #C0392B;")

        tl = QVBoxLayout(top)
        tl.setContentsMargins(12, 10, 12, 10)
        tl.setAlignment(Qt.AlignCenter)

        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)

        logo_path = os.path.normpath(
            os.path.join(_HERE, '..', '..', 'assets', 'logos', 'logo_brasul.png')
        )

        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(190, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl.setPixmap(pix)
        else:
            lbl.setText("BRASUL\nCONSTRUTORA")
            lbl.setStyleSheet("color:#C0392B; font-size:16px; font-weight:bold;")

        tl.addWidget(lbl)
        vl.addWidget(top)

        # Label de seção
        sec = QLabel("NAVEGAÇÃO")
        sec.setStyleSheet(
            "color:#C0392B; font-size:9px; font-weight:bold;"
            "letter-spacing:2px; padding:16px 18px 6px; background:transparent;"
        )
        vl.addWidget(sec)

        # Botões de navegação
        self._btns = {}
        nav = [
            ("pedido", "Pedido de Compra", "●"),
            ("pedidos", "Pedidos Gerados", "📁"),
            ("cotacao", "Cotação", "◆"),
            ("obras", "Obras", "◉"),
            ("historico", "Histórico", "≡"),
            ("cadastros", "Cadastros", "⚙"),
        ]

        for i, (key, label, ico) in enumerate(nav, start=1):
            btn = QPushButton()
            btn.setCheckable(True)
            btn.setFixedHeight(50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(f"Ctrl+{i}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    color: {S_TEXT};
                    background: transparent;
                    border: none;
                    border-left: 4px solid transparent;
                    font-size: 13px;
                    padding-left: 18px;
                }}
                QPushButton:hover {{
                    color: #C0392B;
                    background: {S_ITEM};
                    border-left: 4px solid #E8A090;
                }}
                QPushButton:checked {{
                    color: {S_ATXT};
                    background: {S_SEL};
                    border-left: 4px solid {S_EDGE};
                    font-weight: bold;
                }}
            """)
            btn.setText(f"  {ico}   {label}")
            btn.clicked.connect(lambda _, k=key: self._nav(k))
            self._btns[key] = btn
            vl.addWidget(btn)

        # Divisória
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background:{S_LINE}; margin:12px 18px;")
        div.setFixedHeight(1)
        vl.addWidget(div)

        # Versão
        info = QLabel("Sistema de Cotação\n— v1.0")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet(
            "color:#BBAAAA; font-size:10px; padding:6px;"
            "background:transparent; line-height:1.6;"
        )
        vl.addWidget(info)

        vl.addStretch()

        rodape = QLabel("Brasul Construtora Ltda")
        rodape.setAlignment(Qt.AlignCenter)
        rodape.setStyleSheet(
            f"color:{S_TEXT}; font-size:10px; padding:12px 8px;"
            f"border-top:1px solid {S_LINE}; background:transparent;"
        )
        vl.addWidget(rodape)

        return side

    def _nav(self, key):
        if key not in self._pages:
            return

        for k, b in self._btns.items():
            b.setChecked(k == key)

        self._stack.setCurrentWidget(self._pages[key])

        # Recarrega dados ao trocar de aba
        widget = self._pages[key]
        if hasattr(widget, '_carregar'):
            widget._carregar()
        elif hasattr(widget, 'carregar_dados'):
            widget.carregar_dados()
        elif hasattr(widget, '_carregar_tudo'):
            widget._carregar_tudo()
