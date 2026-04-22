"""
app/ui/style.py
===============
Paleta de cores, CSS e componentes visuais centralizados.
Importe daqui em todos os widgets — nunca duplique CSS.
"""

from PySide6.QtWidgets import QPushButton, QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

# ── Paleta ────────────────────────────────────────────────────────────────────
RED    = "#C0392B"
GRAY   = "#2C2C2C"
WHITE  = "#FFFFFF"
BG     = "#F0EDED"
BDR    = "#D8CCCC"
BDR_F  = "#C0392B"
TXT    = "#1A1A1A"
TXT_S  = "#6B5555"
SEL    = "#FADBD8"
HOV    = "#FEF0EF"
GREEN  = "#1E8449"
BLUE   = "#2980B9"
RO_BG  = "#F5F0F0"

# ── CSS reutilizáveis ─────────────────────────────────────────────────────────
CSS_INPUT = f"""
    QLineEdit {{
        color:{TXT}; background:{WHITE};
        border:1.5px solid {BDR}; border-radius:5px;
        padding:4px 10px; font-size:12px; min-height:30px;
    }}
    QLineEdit:focus {{ border:1.5px solid {BDR_F}; background:#FFFBFB; }}
    QLineEdit:read-only {{ color:{TXT_S}; background:{RO_BG}; border:1.5px solid #E8DEDE; }}
"""

CSS_COMBO = f"""
    QComboBox {{
        color:{TXT}; background:{WHITE};
        border:1.5px solid {BDR}; border-radius:5px;
        padding:4px 10px; font-size:12px; min-height:30px;
    }}
    QComboBox:focus {{ border:1.5px solid {BDR_F}; }}
    QComboBox::drop-down {{ border:none; width:22px; background:transparent; }}
    QComboBox::down-arrow {{
        width:10px; height:10px;
        border-left:5px solid transparent; border-right:5px solid transparent;
        border-top:5px solid {TXT_S}; margin-right:6px;
    }}
    QComboBox QAbstractItemView {{
        color:{TXT}; background:{WHITE}; border:1.5px solid {BDR};
        selection-background-color:{SEL}; selection-color:{GRAY};
        font-size:12px; outline:none;
    }}
    QComboBox QAbstractItemView::item {{
        color:{TXT}; background:{WHITE};
        padding:4px 10px; min-height:26px;
    }}
    QComboBox QAbstractItemView::item:hover,
    QComboBox QAbstractItemView::item:selected {{
        background:{SEL}; color:{GRAY};
    }}
"""

CSS_BUSCA = f"""
    QLineEdit {{
        color:{TXT}; background:{WHITE};
        border:1.5px solid {BDR}; border-radius:6px;
        padding:4px 12px 4px 36px; font-size:12px; min-height:32px;
    }}
    QLineEdit:focus {{ border:1.5px solid {RED}; background:#FFFBFB; }}
"""

CSS_TABLE = f"""
    QTableWidget {{
        background:{WHITE}; border:none;
        font-size:12px; color:{TXT};
        selection-background-color:{SEL}; selection-color:{GRAY};
        outline:none; gridline-color:transparent;
    }}
    QTableWidget::item {{
        padding:0px 12px;
        border-bottom:1px solid #F0E8E8;
    }}
    QTableWidget::item:hover    {{ background:{HOV}; }}
    QTableWidget::item:selected {{ background:{SEL}; color:{GRAY}; }}
    QHeaderView {{ background:{WHITE}; }}
    QHeaderView::section {{
        background:{WHITE}; color:{TXT_S}; font-size:10px;
        font-weight:bold; padding:10px 12px;
        border:none; border-bottom:2px solid #E8DEDE;
    }}
    QScrollBar:vertical {{
        background:transparent; width:6px; border-radius:3px; margin:0;
    }}
    QScrollBar::handle:vertical {{
        background:#D8CCCC; border-radius:3px; min-height:30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
"""

CSS_TABLE_SM = CSS_TABLE.replace("font-size:12px", "font-size:11px")

# Cores por empresa faturadora
CORES_EMPRESA = {
    "BRASUL":      RED,
    "JB":          "#A93226",
    "B&B":         GREEN,
    "INTERIORANA": "#784212",
    "INTERBRAS":   "#1A5276",
}


# ── Componentes helper ────────────────────────────────────────────────────────

def btn_solid(texto: str, cor: str, h: int = 34) -> QPushButton:
    """Botão sólido colorido padrão Brasul."""
    b = QPushButton(texto)
    b.setFixedHeight(h)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background:{cor}; color:white; font-size:11px;
            font-weight:bold; border-radius:6px; border:none; padding:0 16px;
        }}
        QPushButton:hover   {{ background:{cor}DD; }}
        QPushButton:pressed {{ background:{cor}AA; }}
    """)
    return b


def btn_outline(texto: str, h: int = 34) -> QPushButton:
    """Botão outline (borda) padrão Brasul."""
    b = QPushButton(texto)
    b.setFixedHeight(h)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background:transparent; color:{TXT_S}; font-size:11px;
            font-weight:600; border-radius:6px;
            border:1.5px solid {BDR}; padding:0 14px;
        }}
        QPushButton:hover   {{ background:{HOV}; color:{RED}; border-color:{RED}; }}
        QPushButton:pressed {{ background:{SEL}; }}
    """)
    return b


def btn_filtro(rotulo: str) -> QPushButton:
    """Botão de filtro rápido checkable."""
    b = QPushButton(rotulo)
    b.setFixedHeight(34)
    b.setCheckable(True)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background:{WHITE}; color:{TXT_S}; font-size:11px;
            font-weight:600; border-radius:6px;
            border:1.5px solid {BDR}; padding:0 14px;
        }}
        QPushButton:hover   {{ background:{HOV}; color:{RED}; border-color:{RED}; }}
        QPushButton:checked {{
            background:{RED}; color:white;
            border:1.5px solid {RED}; font-weight:bold;
        }}
    """)
    return b


def make_card(titulo: str, valor: str, cor: str):
    """Card de resumo. Retorna (QFrame, QLabel_valor)."""
    card = QFrame()
    card.setFixedHeight(72)
    card.setMinimumWidth(170)
    card.setMaximumWidth(210)
    card.setStyleSheet(f"""
        QFrame {{
            background:{WHITE}; border-radius:10px;
            border-left:4px solid {cor};
            border-top:1px solid #EEE5E5;
            border-right:1px solid #EEE5E5;
            border-bottom:1px solid #EEE5E5;
        }}
    """)
    vl = QVBoxLayout(card)
    vl.setContentsMargins(14, 10, 14, 10)
    vl.setSpacing(3)
    lt = QLabel(titulo.upper())
    lt.setStyleSheet(
        f"font-size:9px; font-weight:700; color:{TXT_S}; "
        f"background:transparent; border:none; letter-spacing:1px;"
    )
    lv = QLabel(str(valor))
    lv.setStyleSheet(
        f"font-size:22px; font-weight:bold; color:{cor}; "
        f"background:transparent; border:none;"
    )
    lv.setObjectName("card_val")
    vl.addWidget(lt)
    vl.addWidget(lv)
    return card, lv


def card_container() -> QFrame:
    """Frame branco com borda suave e sombra — container padrão de tabelas."""
    frame = QFrame()
    frame.setStyleSheet(
        f"QFrame {{ background:{WHITE}; border-radius:12px; border:1px solid #EEE5E5; }}"
    )
    return frame
