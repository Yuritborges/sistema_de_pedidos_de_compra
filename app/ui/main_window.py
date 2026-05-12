# app/ui/main_window.py
# Janela principal do sistema com sidebar de navegação.

import os
import traceback
import time
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QSplashScreen, QApplication,
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QPixmap, QIcon, QFont, QShortcut, QKeySequence, QColor, QPainter

from app.ui.widgets.formulario_pedido import PedidoWidget


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
ORDEM_ABAS = ["pedido", "pedidos", "cotacao", "ferramentas", "locacoes", "cadastros"]


def _icone_app_path():
    base = os.path.normpath(os.path.join(_HERE, "..", ".."))
    candidatos = [
        os.path.join(base, "assets", "iconebrasul2.ico"),
        os.path.join(base, "assets", "logos", "logo_brasul.ico"),
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
        inicio = time.perf_counter()
        marcacoes = []

        def marcar(etapa):
            marcacoes.append((etapa, time.perf_counter() - inicio))

        root = QWidget()
        self.setCentralWidget(root)
        marcar("root-central-widget")

        lay = QHBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._sidebar())
        marcar("sidebar-pronta")

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background:{C_BG};")
        lay.addWidget(self._stack, 1)
        marcar("stack-pronto")

        self._page_factories = {
            "pedido": self._criar_pagina_pedido,
            "pedidos": self._criar_pagina_pedidos,
            "cotacao": self._criar_pagina_cotacao,
            "ferramentas": self._criar_pagina_ferramentas,
            "locacoes": self._criar_pagina_locacoes,
            "cadastros": self._criar_pagina_cadastros,
        }
        # Lazy load: páginas são criadas apenas quando abertas.
        self._pages = {k: None for k in self._page_factories}
        marcar("factories-configuradas")

        self._nav("pedido")
        marcar("navegacao-inicial")
        self._registrar_log_startup(marcacoes)

    def _criar_pagina_pedido(self):
        return PedidoWidget()

    def _criar_pagina_pedidos(self):
        from app.ui.widgets.pedidos_widget import PedidosWidget
        return PedidosWidget()

    def _criar_pagina_cotacao(self):
        from app.ui.widgets.cotacao_widget import CotacaoWidget
        return CotacaoWidget()

    def _criar_pagina_ferramentas(self):
        from app.ui.widgets.ferramentas_widget import FerramentasWidget
        return FerramentasWidget()

    def _criar_pagina_locacoes(self):
        from app.ui.widgets.locacoes_widget import LocacoesWidget
        return LocacoesWidget()

    def _registrar_log_startup(self, marcacoes):
        try:
            base = os.path.normpath(os.path.join(_HERE, "..", "..", ".."))
            log_path = os.path.join(base, "startup_v2.log")
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            linhas = [f"[MainWindow] {agora}"]
            anterior = 0.0
            for etapa, acumulado in marcacoes:
                delta = acumulado - anterior
                linhas.append(f"{etapa:24s} +{delta:7.3f}s  total={acumulado:7.3f}s")
                anterior = acumulado
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("\n".join(linhas) + "\n")
        except Exception:
            pass

    def _criar_pagina_cadastros(self):
        try:
            from app.ui.widgets.cadastros_widget import CadastrosWidget
            return CadastrosWidget()
        except Exception as e:
            erro_cadastros = e

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
            f"Erro:\n{erro_cadastros}"
        )
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size:12px; color:#333;")

        lay.addWidget(title)
        lay.addWidget(msg)
        lay.addStretch()
        return page

    def _registrar_atalhos(self):
        # Ctrl+1 a Ctrl+6 navegam entre as abas (ORDEM_ABAS)
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
            ("ferramentas", "Ferramentas", "🧰"),
            ("locacoes", "Locações", "🏗"),
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

        widget = self.obter_pagina(key)
        if widget is None:
            return
        self._stack.setCurrentWidget(widget)

        # Recarrega dados ao trocar de aba
        if hasattr(widget, '_carregar'):
            widget._carregar()
        elif hasattr(widget, 'carregar_dados'):
            widget.carregar_dados()
        elif hasattr(widget, '_carregar_tudo'):
            widget._carregar_tudo()

    def obter_pagina(self, key):
        if key not in self._pages:
            return None
        pagina = self._pages.get(key)
        if pagina is None:
            try:
                pagina = self._page_factories[key]()
                self._pages[key] = pagina
                self._stack.addWidget(pagina)
            except Exception:
                traceback.print_exc()
                return None
        return pagina
