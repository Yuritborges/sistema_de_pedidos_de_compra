# app/ui/style.py
# Cores, CSS e botões padrão do sistema.
# Importe daqui em todos os widgets.

from PySide6.QtWidgets import QPushButton, QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

# Paleta de cores
RED   = "#C0392B"
GRAY  = "#2C2C2C"
WHITE = "#FFFFFF"
BG    = "#F0EDED"
BDR   = "#D8CCCC"
BDR_F = "#C0392B"
TXT   = "#1A1A1A"
TXT_S = "#6B5555"
SEL   = "#FADBD8"
HOV   = "#FEF0EF"
GREEN = "#1E8449"
BLUE  = "#2980B9"
RO_BG = "#F5F0F0"

# CSS dos campos de texto
CSS_INPUT = f"""
    QLineEdit {{
        color:{TXT}; background:{WHITE};
        border:1.5px solid {BDR}; border-radius:5px;
        padding:4px 10px; font-size:12px; min-height:30px;
    }}
    QLineEdit:focus {{ border:1.5px solid {BDR_F}; background:#FFFBFB; }}
    QLineEdit:read-only {{ color:{TXT_S}; background:{RO_BG}; border:1.5px solid #E8DEDE; }}
"""

# CSS dos comboboxes
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

# CSS do campo de busca
CSS_BUSCA = f"""
    QLineEdit {{
        color:{TXT}; background:{WHITE};
        border:1.5px solid {BDR}; border-radius:6px;
        padding:4px 12px 4px 36px; font-size:12px; min-height:32px;
    }}
    QLineEdit:focus {{ border:1.5px solid {RED}; background:#FFFBFB; }}
"""

# CSS das tabelas
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

# Cor de destaque por empresa faturadora
CORES_EMPRESA = {
    "BRASUL":      RED,
    "JB":          "#A93226",
    "B&B":         GREEN,
    "INTERIORANA": "#784212",
    "INTERBRAS":   "#1A5276",
}


# Botão preenchido colorido
def btn_solid(texto, cor, h=34):
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


# Botão com borda (outline)
def btn_outline(texto, h=34):
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


# Botão de filtro que fica marcado ao clicar
def btn_filtro(rotulo):
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


# Card de resumo com título e valor
def make_card(titulo, valor, cor):
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


# Frame branco arredondado usado como container de tabelas
def card_container():
    frame = QFrame()
    frame.setStyleSheet(
        f"QFrame {{ background:{WHITE}; border-radius:12px; border:1px solid #EEE5E5; }}"
    )
    return frame
