# app/ui/main_window.py
# Janela principal do sistema com sidebar de navegação.

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QFont, QShortcut, QKeySequence

from app.ui.widgets.formulario_pedido import PedidoWidget
from app.ui.widgets.obras_widget      import ObrasWidget
from app.ui.widgets.cotacao_widget    import CotacaoWidget
from app.ui.widgets.historico_widget  import HistoricoWidget
from app.ui.widgets.pedidos_widget    import PedidosWidget

_HERE = os.path.dirname(os.path.abspath(__file__))

# Cores da sidebar
S_BG   = "#F0EDED"
S_ITEM = "#E8DEDE"
S_SEL  = "#FDECEA"
S_EDGE = "#C0392B"
S_LINE = "#DCCECE"
S_TEXT = "#6B5555"
S_ATXT = "#C0392B"
C_BG   = "#F0EDED"

# Ordem das abas — usada pelos atalhos Ctrl+1..5
ORDEM_ABAS = ["pedido", "pedidos", "cotacao", "obras", "historico"]


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Pedidos — Brasul Construtora")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 820)
        self._build()
        self._registrar_atalhos()

        # Ícone da janela
        ico = os.path.normpath(os.path.join(_HERE, '..', '..', 'assets', 'iconebrasul2.ico'))
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

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
            "pedido":    PedidoWidget(),
            "pedidos":   PedidosWidget(),
            "cotacao":   CotacaoWidget(),
            "obras":     ObrasWidget(),
            "historico": HistoricoWidget(),
        }
        for p in self._pages.values():
            self._stack.addWidget(p)

        self._nav("pedido")

    def _registrar_atalhos(self):
        # Ctrl+1 a Ctrl+5 navegam entre as abas
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

        # Botões de navegação com dica do atalho
        self._btns = {}
        nav = [
            ("pedido",    "Pedido de Compra", "●"),
            ("pedidos",   "Pedidos Gerados",  "📁"),
            ("cotacao",   "Cotação",          "◆"),
            ("obras",     "Obras",            "◉"),
            ("historico", "Histórico",        "≡"),
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
        for k, b in self._btns.items():
            b.setChecked(k == key)
        self._stack.setCurrentWidget(self._pages[key])

        # Se a aba tem método de atualização, chama ao entrar
        widget = self._pages[key]
        if hasattr(widget, '_carregar'):
            widget._carregar()
        elif hasattr(widget, 'carregar_dados'):
            widget.carregar_dados()
