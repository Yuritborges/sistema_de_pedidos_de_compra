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

# Coluna "Ações" em Pedidos Gerados — uma cor por função (fácil de reconhecer à distância).
PEDIDO_ACAO_ABRIR = BLUE
PEDIDO_ACAO_EXPORTAR = "#16A085"
PEDIDO_ACAO_REIMPRIMIR = "#8E44AD"
PEDIDO_ACAO_EDITAR = "#E67E22"
PEDIDO_ACAO_PRAZO_OBRA = "#2874A6"   # azul — card de prazo / calendário
PEDIDO_ACAO_OK_NA_OBRA = "#25D366"   # verde WhatsApp — confirmação OK na obra
PEDIDO_ACAO_EXCLUIR = RED

# Pedidos Gerados — apenas duas cores: sem OK na obra / com OK na obra.
PEDIDOS_GERADOS_ROW_PENDENTE = "#FFEBEE"  # vermelho claro (falta confirmar OK na obra)
PEDIDOS_GERADOS_ROW_OK_OBRA = "#C8E6C9"  # verde claro (OK na obra confirmado)

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

# Popup do QCompleter (janela à parte — não herda QComboBox QAbstractItemView)
CSS_COMPLETER_POPUP = f"""
    QAbstractItemView {{
        color:{TXT};
        background:{WHITE};
        border:1.5px solid {BDR};
        font-size:12px;
        outline:none;
        selection-background-color:#DBEAFE;
        selection-color:#1E3A5F;
    }}
    QAbstractItemView::item {{
        color:{TXT};
        background:{WHITE};
        padding:6px 12px;
        min-height:28px;
    }}
    QAbstractItemView::item:hover {{
        background:#EFF6FF;
        color:{TXT};
    }}
    QAbstractItemView::item:selected {{
        background:#DBEAFE;
        color:#1E3A5F;
    }}
    QScrollBar:vertical {{
        background:{WHITE};
        width:10px;
        margin:2px;
    }}
    QScrollBar::handle:vertical {{
        background:#C5BABA;
        border-radius:4px;
        min-height:24px;
    }}
"""


def apply_completer_popup_style(completer) -> None:
    """Evita popup escuro (Fusion) com texto ilegível ao combinar QComboBox + QCompleter."""
    if completer is None:
        return
    pop = completer.popup()
    if pop is not None:
        pop.setStyleSheet(CSS_COMPLETER_POPUP)


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

# Tabela "Pedidos Gerados": não estilize QTableWidget::item (nem padding, nem borda) —
# no Windows isso costuma ignorar o BackgroundRole e a linha fica branca menos a coluna Ações.
CSS_TABLE_PEDIDOS_GERADOS = f"""
    QTableWidget#pedidos_gerados_tabela {{
        background:{WHITE}; border:none;
        font-size:12px; color:{TXT};
        outline:none; gridline-color:transparent;
    }}
    QTableWidget#pedidos_gerados_tabela QHeaderView {{ background:{WHITE}; }}
    QTableWidget#pedidos_gerados_tabela QHeaderView::section {{
        background:{WHITE}; color:{TXT_S}; font-size:10px;
        font-weight:bold; padding:10px 12px;
        border:none; border-bottom:2px solid #E8DEDE;
    }}
    QTableWidget#pedidos_gerados_tabela QScrollBar:vertical {{
        background:transparent; width:6px; border-radius:3px; margin:0;
    }}
    QTableWidget#pedidos_gerados_tabela QScrollBar::handle:vertical {{
        background:#D8CCCC; border-radius:3px; min-height:30px;
    }}
    QTableWidget#pedidos_gerados_tabela QScrollBar::add-line:vertical,
    QTableWidget#pedidos_gerados_tabela QScrollBar::sub-line:vertical {{ height:0; }}
"""

CSS_TABLE_SM = CSS_TABLE.replace("font-size:12px", "font-size:11px")

# Cor de destaque por empresa faturadora
CORES_EMPRESA = {
    "BRASUL":      RED,
    "B&B":         GREEN,
    "INTERIORANA": "#784212",
    "INTERBRAS":   "#1A5276",
}


# Botão preenchido colorido
def btn_solid(texto, cor, h=34, font_px=11, pad_x=16):
    b = QPushButton(texto)
    b.setFixedHeight(h)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background:{cor}; color:white; font-size:{font_px}px;
            font-weight:bold; border-radius:6px; border:none; padding:0 {pad_x}px;
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
