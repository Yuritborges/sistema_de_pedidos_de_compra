
"""
app/ui/widgets/cotacao_widget.py  — v6 MANUAL + NEGOCIAÇÃO + SALVAR/CARREGAR
=============================================================================
Cotação 100% manual — sem importação de PDF.
Novidades:
  - Coluna Unidade com dropdown clicável (UNID, UN, KG, GL, LT, M2, M3, PCT...)
  - Tab/Enter navega entre colunas editáveis
  - Delete/Backspace apaga linha selecionada
  - Destaque verde (melhor preço) e vermelho (pior preço) por linha
  - Dashboard com vencedor, comparativo e botões de gerar pedido
  - Card de negociação com economia potencial e novo total possível
  - Copiar texto de negociação
  - Salvar/Carregar cotação em JSON
"""

import os, json
from datetime import datetime
from urllib.parse import quote

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QGraphicsDropShadowEffect, QPushButton,
    QSplitter, QScrollArea, QMessageBox,
    QAbstractItemView, QStyledItemDelegate, QApplication,
    QFileDialog,
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QFont, QBrush, QDesktopServices

from app.ui.style import (
    RED, GRAY, WHITE, BG, BDR, TXT, TXT_S, SEL, HOV, GREEN, BLUE,
    CSS_INPUT, CSS_COMBO, CORES_EMPRESA,
    btn_solid, btn_outline, card_container,
)

_ASSETS   = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets'))
_OBR_JSON = os.path.join(_ASSETS, 'obras.json')
_COT_DIR  = os.path.join(_ASSETS, 'cotacoes_salvas')

# Cores por fornecedor
COR_F = ["#1A5276", "#1E8449", "#784212"]

# Cores de destaque na tabela
COR_MELHOR   = QColor("#D5F5E3")
COR_MELHOR_FG= QColor("#1A7A3C")
COR_PIOR_BG  = QColor("#FDECEA")
COR_PIOR_FG  = QColor("#922B21")
COR_NEUTRO   = QColor("#FDFEFE")
COR_VAZIO    = QColor("#F4F6F7")

# Regras de negociação
NEGOCIACAO_DIF_MIN = 2.00      # diferença mínima unitária em R$
NEGOCIACAO_PCT_MIN = 5.0       # diferença mínima percentual

# ── Unidades disponíveis no dropdown ──────────────────────────────────────────
UNIDADES = [
    "UNID.", "UN", "PC", "PCT",
    "KG", "G",
    "GL",   # galão
    "LT",   # lata
    "L",    # litro
    "ML",
    "MT",   # metro linear
    "M2",   # metro quadrado
    "M3",   # metro cúbico
    "RL",   # rolo
    "BR",   # barra
    "CX",   # caixa
    "SC",   # saco
    "BD",   # balde
    "VB",   # verba
    "JG",   # jogo
    "CT",   # conjunto
    "PR",   # par
    "HR",   # hora
]

CSS_TABLE = f"""
    QTableWidget {{
        background:{WHITE}; border:none; font-size:12px; color:#1A1A1A;
        selection-background-color:#FADBD8; selection-color:#2C2C2C;
        outline:none; gridline-color:#E5E5E5;
    }}
    QTableWidget::item {{ padding:2px 8px; border-bottom:1px solid #ECECEC; color:#1A1A1A; }}
    QTableWidget::item:hover    {{ background:#EBF5FB; }}
    QTableWidget::item:selected {{ background:#FADBD8; color:#2C2C2C; }}
    QHeaderView::section {{
        background:#2C2C2C; color:#FFFFFF; font-size:10px; font-weight:bold;
        padding:8px 6px; border:none; border-right:1px solid #444;
        border-bottom:2px solid #C0392B;
    }}
    QScrollBar:vertical   {{ background:transparent; width:6px;  border-radius:3px; }}
    QScrollBar:horizontal {{ background:transparent; height:6px; border-radius:3px; }}
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
        background:#C0C0C0; border-radius:3px; min-height:20px; min-width:20px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width:0; height:0; }}
"""

CSS_EDIT = f"""
    QLineEdit {{
        color:#1A1A1A; background:{WHITE};
        border:1.5px solid #C0392B; border-radius:3px;
        padding:2px 6px; font-size:12px;
    }}
"""

CSS_COMBO_UNID = f"""
    QComboBox {{
        color:{TXT}; background:{WHITE};
        border:1px solid {BDR}; border-radius:3px;
        padding:1px 4px; font-size:11px; min-height:28px;
    }}
    QComboBox:focus {{ border:1.5px solid #C0392B; }}
    QComboBox::drop-down {{ border:none; width:16px; background:transparent; }}
    QComboBox::down-arrow {{
        width:8px; height:8px;
        border-left:4px solid transparent; border-right:4px solid transparent;
        border-top:4px solid {TXT_S}; margin-right:4px;
    }}
    QComboBox QAbstractItemView {{
        color:{TXT}; background:{WHITE}; border:1.5px solid {BDR};
        selection-background-color:{SEL}; selection-color:#2C2C2C;
        font-size:11px; outline:none;
    }}
    QComboBox QAbstractItemView::item {{
        color:{TXT}; background:{WHITE};
        padding:4px 8px; min-height:24px;
    }}
    QComboBox QAbstractItemView::item:hover,
    QComboBox QAbstractItemView::item:selected {{
        background:{SEL}; color:#2C2C2C;
    }}
"""


class NavDelegate(QStyledItemDelegate):
    """
    Editor customizado:
    - Colunas de texto: QLineEdit com CSS vermelho
    - Coluna 3 (Unidade): QComboBox com lista de unidades
    - Tab/Enter avança para próxima coluna editável
    """

    COLS_EDIT = [1, 2, 3, 4, 6, 8]

    def __init__(self, tabela, cb_nova_linha, parent=None):
        super().__init__(parent)
        self._t  = tabela
        self._nl = cb_nova_linha

    def createEditor(self, parent, option, index):
        col = index.column()

        if col == 3:
            cb = QComboBox(parent)
            cb.setStyleSheet(CSS_COMBO_UNID)
            for u in UNIDADES:
                cb.addItem(u)
            return cb

        e = QLineEdit(parent)
        e.setStyleSheet(CSS_EDIT)
        if col == 1:
            e.textChanged.connect(
                lambda txt, w=e: (
                    w.blockSignals(True),
                    w.setText(txt.upper()),
                    w.blockSignals(False)
                ) if txt != txt.upper() else None
            )
        return e

    def setEditorData(self, editor, index):
        val = index.data(Qt.EditRole) or ""
        if isinstance(editor, QComboBox):
            idx = editor.findText(str(val).upper())
            editor.setCurrentIndex(idx if idx >= 0 else 0)
        else:
            editor.setText(str(val))

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.EditRole)
        else:
            model.setData(index, editor.text(), Qt.EditRole)

    def eventFilter(self, editor, event):
        if event.type() == event.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key_Tab, Qt.Key_Return, Qt.Key_Enter):
                idx = self._t.currentIndex()
                row, col = idx.row(), idx.column()
                self.commitData.emit(editor)
                self.closeEditor.emit(editor, QStyledItemDelegate.NoHint)
                if col in self.COLS_EDIT:
                    ni = self.COLS_EDIT.index(col) + 1
                    if ni < len(self.COLS_EDIT):
                        nc = self.COLS_EDIT[ni]
                        QTimer.singleShot(0, lambda r=row, c=nc: (
                            self._t.setCurrentCell(r, c),
                            self._t.edit(self._t.model().index(r, c))
                        ))
                    else:
                        if row + 1 >= self._t.rowCount():
                            QTimer.singleShot(0, self._nl)
                        else:
                            QTimer.singleShot(0, lambda r=row+1: (
                                self._t.setCurrentCell(r, 1),
                                self._t.edit(self._t.model().index(r, 1))
                            ))
                return True
        return super().eventFilter(editor, event)


class ItemCotacao:
    def __init__(self, desc="", qtd=1.0, unid="UNID."):
        self.descricao  = desc
        self.quantidade = float(qtd) if qtd else 1.0
        self.unidade    = unid
        self.precos     = [None, None, None]

    def subtotal(self, i):
        try:
            p = float(self.precos[i])
            return round(p * self.quantidade, 2) if p > 0 else None
        except (TypeError, ValueError):
            return None

    def melhor_idx(self):
        subs = [(i, self.subtotal(i)) for i in range(3) if self.subtotal(i) is not None]
        return min(subs, key=lambda x: x[1])[0] if subs else None

    def melhor_sub(self):
        i = self.melhor_idx()
        return self.subtotal(i) if i is not None else None


class ResultadoFornecedor:
    def __init__(self, nome, idx):
        self.nome = nome; self.idx = idx
        self.itens_cotados = 0; self.itens_baratos = 0
        self.total_itens = 0; self.subtotal_val = 0.0
        self.frete = 0.0; self.desconto = 0.0

    @property
    def total_final(self):
        return max(0.0, self.subtotal_val + self.frete - self.desconto)

    def status(self, n):
        if self.itens_cotados == n: return "✓ Completo"
        if self.itens_cotados > 0:  return f"Parcial ({self.itens_cotados}/{n})"
        return "Sem cotação"


def _mk_vdiv():
    f = QFrame(); f.setFrameShape(QFrame.VLine)
    f.setStyleSheet("background:#EDD;border:none;")
    f.setFixedWidth(1); f.setFixedHeight(44)
    return f


class CotacaoWidget(QWidget):

    def __init__(self):
        super().__init__()
        self._itens: list[ItemCotacao] = []
        self._fretes    = [0.0, 0.0, 0.0]
        self._descontos = [0.0, 0.0, 0.0]
        self._obras     = {}
        self._bloqueio  = False
        self._arquivo_cotacao_atual = ""
        self._itens_negociacao = []
        os.makedirs(_COT_DIR, exist_ok=True)
        self._build()
        self._carregar_obras()
        self._itens.append(ItemCotacao())
        self._inserir_linha(0, self._itens[0])
        self._atualizar_contador()

    # ══════════════════════════════════════════════════════════════════════════
    # BUILD
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        self.setStyleSheet(f"background:{BG};")
        vl = QVBoxLayout(self); vl.setContentsMargins(24,20,24,16); vl.setSpacing(14)

        hl = QHBoxLayout()
        tv = QVBoxLayout(); tv.setSpacing(2)
        t = QLabel("Cotação Comparativa")
        t.setStyleSheet(f"font-size:20px;font-weight:bold;color:{GRAY};background:transparent;")
        s = QLabel("Compare fornecedores item a item e gere o pedido do vencedor")
        s.setStyleSheet(f"font-size:11px;color:#555;background:transparent;")
        tv.addWidget(t); tv.addWidget(s)
        hl.addLayout(tv); hl.addStretch()

        bc = btn_outline("📂  Carregar")
        bc.clicked.connect(self._carregar_cotacao_json)
        hs = btn_outline("💾  Salvar")
        hs.clicked.connect(self._salvar_cotacao_json)
        bn = btn_outline("🗑  Nova cotação")
        bn.clicked.connect(self._nova_cotacao)

        hl.addWidget(bc)
        hl.addWidget(hs)
        hl.addWidget(bn)

        vl.addLayout(hl)
        vl.addWidget(self._build_cab())

        sp = QSplitter(Qt.Horizontal)
        sp.setStyleSheet("QSplitter::handle{background:#C0C0C0;width:5px;}QSplitter::handle:hover{background:#C0392B;}")
        sp.setHandleWidth(6); sp.setChildrenCollapsible(False)
        sp.addWidget(self._build_tabela())
        sp.addWidget(self._build_dashboard())
        sp.setSizes([760, 440])
        vl.addWidget(sp, 1)

    def _build_cab(self):
        box = QFrame()
        box.setStyleSheet(f"QFrame{{background:{WHITE};border-radius:10px;border:1px solid #DDD;}}")
        hl = QHBoxLayout(box); hl.setContentsMargins(16,12,16,12); hl.setSpacing(14)

        def grp(lbl_txt, widget):
            vl2 = QVBoxLayout(); vl2.setSpacing(4)
            l = QLabel(lbl_txt.upper())
            l.setStyleSheet("font-size:9px;font-weight:700;color:#444;background:transparent;letter-spacing:1px;")
            vl2.addWidget(l); vl2.addWidget(widget)
            return vl2

        self._cb_obra = QComboBox()
        self._cb_obra.setMinimumWidth(220)
        self._cb_obra.setEditable(True)
        self._cb_obra.setInsertPolicy(QComboBox.NoInsert)
        self._cb_obra.setStyleSheet(CSS_COMBO)
        self._cb_obra.lineEdit().setPlaceholderText("Digite para buscar...")
        from PySide6.QtWidgets import QCompleter
        self._cb_obra.completer().setCompletionMode(
            QCompleter.PopupCompletion if hasattr(QCompleter, 'PopupCompletion') else 0)
        popup = self._cb_obra.completer().popup()
        popup.setStyleSheet(f"""
            QListView {{
                background:#FFFFFF; color:#1A1A1A;
                border:1.5px solid #D8CCCC; border-radius:5px;
                font-size:12px; outline:none;
            }}
            QListView::item {{
                background:#FFFFFF; color:#1A1A1A;
                padding:5px 10px; min-height:26px;
            }}
            QListView::item:hover, QListView::item:selected {{
                background:#FADBD8; color:#2C2C2C;
            }}
        """)
        self._cb_obra.currentTextChanged.connect(self._on_obra)
        hl.addLayout(grp("Obra", self._cb_obra))

        self._cb_emp = QComboBox()
        self._cb_emp.setMinimumWidth(130)
        self._cb_emp.setStyleSheet(CSS_COMBO)
        for e in ["BRASUL","JB","B&B","INTERIORANA","INTERBRAS"]:
            self._cb_emp.addItem(e)
        hl.addLayout(grp("Empresa faturadora", self._cb_emp))
        hl.addWidget(self._vsep())

        self._e_forn = []
        for i in range(3):
            cor = COR_F[i]
            vf = QVBoxLayout(); vf.setSpacing(4)
            lf = QLabel(f"FORNECEDOR {i+1}")
            lf.setStyleSheet(f"font-size:9px;font-weight:700;color:{cor};background:transparent;letter-spacing:1px;")
            vf.addWidget(lf)
            e = QLineEdit()
            e.setPlaceholderText(f"Nome F{i+1}")
            e.setMinimumWidth(140)
            e.setStyleSheet(CSS_INPUT)
            e.textChanged.connect(lambda txt, idx=i: self._on_forn(idx, txt))
            self._e_forn.append(e)
            vf.addWidget(e)
            hl.addLayout(vf)

        hl.addWidget(self._vsep())

        self._e_frete = []
        for i in range(3):
            e = QLineEdit("0,00")
            e.setMaximumWidth(80)
            e.setStyleSheet(CSS_INPUT)
            e.textChanged.connect(lambda t, idx=i: self._on_frete(idx, t))
            self._e_frete.append(e)
            hl.addLayout(grp(f"Frete F{i+1}", e))

        hl.addWidget(self._vsep())

        self._e_desc = []
        for i in range(3):
            e = QLineEdit("0,00")
            e.setMaximumWidth(80)
            e.setStyleSheet(CSS_INPUT)
            e.textChanged.connect(lambda t, idx=i: self._on_desc(idx, t))
            self._e_desc.append(e)
            hl.addLayout(grp(f"Desc. F{i+1}", e))

        hl.addStretch()
        return box

    def _build_tabela(self):
        frame = card_container()
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(14); sh.setOffset(0,2); sh.setColor(QColor(0,0,0,15))
        frame.setGraphicsEffect(sh)
        vl = QVBoxLayout(frame); vl.setContentsMargins(0,0,0,0); vl.setSpacing(0)

        hl = QHBoxLayout(); hl.setContentsMargins(14,10,14,8); hl.setSpacing(10)
        lbl = QLabel("Itens da Cotação")
        lbl.setStyleSheet(f"font-size:13px;font-weight:bold;color:{GRAY};background:transparent;")
        self._lbl_n = QLabel("0 itens")
        self._lbl_n.setStyleSheet("font-size:11px;color:#555;background:transparent;")
        hl.addWidget(lbl); hl.addWidget(self._lbl_n); hl.addStretch()

        b1 = btn_solid("＋  Adicionar", GREEN, h=30)
        b1.setToolTip("Adicionar novo item (ou Enter na última coluna)")
        b1.clicked.connect(self._adicionar_item)

        b2 = btn_solid("🗑  Apagar selecionado", "#C0392B", h=30)
        b2.setToolTip("Remove a linha selecionada (ou tecla Delete)")
        b2.clicked.connect(self._apagar_selecionado)

        b3 = btn_solid("✕  Limpar tudo", "#7F8C8D", h=30)
        b3.setToolTip("Remove todos os itens")
        b3.clicked.connect(self._limpar_tudo)

        b4 = btn_solid("⚡  Calcular", "#2C3E50", h=30)
        b4.setToolTip("Recalcula comparativos")
        b4.clicked.connect(self._calcular)

        for b in [b1, b2, b3, b4]: hl.addWidget(b)
        vl.addLayout(hl)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#E0E0E0;"); sep.setFixedHeight(1)
        vl.addWidget(sep)

        self._tbl = QTableWidget(0, 12)
        self._tbl.setHorizontalHeaderLabels([
            "#", "Descrição do Material", "Qtd", "Unid",
            "Preço F1", "Sub F1", "Preço F2", "Sub F2", "Preço F3", "Sub F3",
            "✓ Melhor", "Fornecedor"
        ])
        self._tbl.setStyleSheet(CSS_TABLE)
        self._tbl.setSelectionBehavior(QTableWidget.SelectRows)
        self._tbl.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setShowGrid(True)
        self._tbl.setFrameShape(QFrame.NoFrame)
        self._tbl.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._tbl.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        self._delegate = NavDelegate(self._tbl, self._adicionar_item, self._tbl)
        self._tbl.setItemDelegate(self._delegate)

        hh = self._tbl.horizontalHeader()
        hh.setHighlightSections(False)
        hh.setMinimumSectionSize(40)
        hh.setStretchLastSection(False)
        hh.setSectionResizeMode(QHeaderView.Interactive)
        for col, w in enumerate([28, 220, 55, 70, 85, 85, 85, 85, 85, 85, 90, 110]):
            self._tbl.setColumnWidth(col, w)

        self._tbl.keyPressEvent = self._key_press
        self._tbl.itemChanged.connect(self._on_changed)
        vl.addWidget(self._tbl, 1)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background:#E0E0E0;"); sep2.setFixedHeight(1)
        vl.addWidget(sep2)

        hl2 = QHBoxLayout(); hl2.setContentsMargins(14,8,14,10); hl2.setSpacing(24)
        self._lbl_tot = [QLabel(f"F{i+1}: —") for i in range(3)]
        self._lbl_melhor = QLabel("✓ Melhor item a item: —")
        self._lbl_melhor.setStyleSheet(f"font-size:11px;font-weight:bold;color:{GREEN};background:transparent;")
        for i, lb in enumerate(self._lbl_tot):
            lb.setStyleSheet(f"font-size:11px;font-weight:600;color:{COR_F[i]};background:transparent;")
            hl2.addWidget(lb)
        hl2.addWidget(self._lbl_melhor); hl2.addStretch()
        vl.addLayout(hl2)
        return frame

    def _build_dashboard(self):
        frame = card_container()
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(14); sh.setOffset(0,2); sh.setColor(QColor(0,0,0,15))
        frame.setGraphicsEffect(sh)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background:transparent;")
        inner = QWidget(); inner.setStyleSheet(f"background:{WHITE};")
        vl = QVBoxLayout(inner); vl.setContentsMargins(16,16,16,16); vl.setSpacing(10)

        lbl_tit = QLabel("Resultado da Análise")
        lbl_tit.setStyleSheet(
            f"font-size:15px;font-weight:bold;color:{GRAY};background:transparent;")
        vl.addWidget(lbl_tit)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#EEEEEE;"); sep.setFixedHeight(1)
        vl.addWidget(sep)

        self._frame_ven = QFrame()
        self._frame_ven.setStyleSheet(
            f"QFrame{{background:#FEF9F9;border-radius:12px;"
            f"border-left:5px solid {RED};"
            f"border-top:1px solid #EEE8E8;border-right:1px solid #EEE8E8;border-bottom:1px solid #EEE8E8;}}"
        )
        vv = QVBoxLayout(self._frame_ven); vv.setContentsMargins(16,14,16,14); vv.setSpacing(6)

        hl_badge = QHBoxLayout(); hl_badge.setSpacing(8)
        badge = QLabel("🏆  VENCEDOR")
        badge.setStyleSheet(
            "font-size:9px;font-weight:800;color:#922B21;"
            "background:#FADBD8;border-radius:4px;padding:3px 8px;"
            "letter-spacing:1.5px;border:none;")
        hl_badge.addWidget(badge); hl_badge.addStretch()
        vv.addLayout(hl_badge)

        self._lbl_ven = QLabel("—")
        self._lbl_ven.setStyleSheet(
            f"font-size:26px;font-weight:bold;color:{RED};background:transparent;")
        vv.addWidget(self._lbl_ven)

        self._lbl_mot = QLabel("Preencha os preços e clique em ⚡ Calcular")
        self._lbl_mot.setStyleSheet(
            "font-size:11px;color:#666;background:transparent;")
        self._lbl_mot.setWordWrap(True)
        vv.addWidget(self._lbl_mot)

        sep_v = QFrame(); sep_v.setFrameShape(QFrame.HLine)
        sep_v.setStyleSheet("background:#EDD;border:none;"); sep_v.setFixedHeight(1)
        vv.addWidget(sep_v)

        hl_stats = QHBoxLayout(); hl_stats.setSpacing(0)

        def mini_stat(obj_lbl, obj_val, icone, label, cor_val):
            w = QWidget()
            w.setStyleSheet("background:transparent;border:none;")
            vls = QVBoxLayout(w); vls.setContentsMargins(8,4,8,4); vls.setSpacing(1)
            l1 = QLabel(f"{icone}  {label}")
            l1.setStyleSheet("font-size:9px;color:#888;background:transparent;font-weight:600;")
            l1.setObjectName(obj_lbl)
            l2 = QLabel("—")
            l2.setStyleSheet(f"font-size:17px;font-weight:bold;color:{cor_val};background:transparent;")
            l2.setObjectName(obj_val)
            vls.addWidget(l1); vls.addWidget(l2)
            return w

        self._frame_ven.ms_total  = mini_stat("v_lbl_total",  "v_val_total",  "💰", "TOTAL FINAL",   RED)
        self._frame_ven.ms_baratos= mini_stat("v_lbl_bar",    "v_val_bar",    "✅", "ITENS + BARATOS", GREEN)
        self._frame_ven.ms_econ   = mini_stat("v_lbl_econ",   "v_val_econ",   "📉", "ECONOMIA vs 2º",  "#1A5276")

        hl_stats.addWidget(self._frame_ven.ms_total)
        hl_stats.addWidget(_mk_vdiv())
        hl_stats.addWidget(self._frame_ven.ms_baratos)
        hl_stats.addWidget(_mk_vdiv())
        hl_stats.addWidget(self._frame_ven.ms_econ)
        hl_stats.addStretch()
        vv.addLayout(hl_stats)
        vl.addWidget(self._frame_ven)

        lc = QLabel("COMPARATIVO DE FORNECEDORES")
        lc.setStyleSheet(
            "font-size:9px;font-weight:800;color:#888;"
            "background:transparent;letter-spacing:1.5px;")
        vl.addWidget(lc)

        self._cards = [self._make_card(i) for i in range(3)]
        for c in self._cards: vl.addWidget(c)

        self._lbl_obs = QLabel("")
        self._lbl_obs.setStyleSheet(
            "font-size:10px;color:#7D6608;"
            "background:#FEFDE7;border-radius:6px;"
            "padding:8px 10px;border:1px solid #F9E79F;")
        self._lbl_obs.setWordWrap(True)
        self._lbl_obs.setVisible(False)
        vl.addWidget(self._lbl_obs)

        self._frame_neg = QFrame()
        self._frame_neg.setStyleSheet(
            "QFrame{background:#F8FBFF;border-radius:10px;border:1px solid #D6EAF8;}"
        )
        vn = QVBoxLayout(self._frame_neg)
        vn.setContentsMargins(14,12,14,12)
        vn.setSpacing(6)

        self._lbl_neg_titulo = QLabel("Itens para Negociação")
        self._lbl_neg_titulo.setStyleSheet(
            "font-size:13px;font-weight:bold;color:#1A5276;background:transparent;"
        )
        vn.addWidget(self._lbl_neg_titulo)

        self._lbl_neg_resumo = QLabel("Nenhuma análise de negociação disponível.")
        self._lbl_neg_resumo.setWordWrap(True)
        self._lbl_neg_resumo.setStyleSheet(
            "font-size:11px;color:#555;background:transparent;"
        )
        vn.addWidget(self._lbl_neg_resumo)

        self._lbl_neg_stats = QLabel("0 itens • Economia potencial: R$ 0,00")
        self._lbl_neg_stats.setStyleSheet(
            "font-size:12px;font-weight:700;color:#1A5276;background:transparent;"
        )
        vn.addWidget(self._lbl_neg_stats)

        self._lbl_neg_novo_total = QLabel("Novo total possível: R$ 0,00")
        self._lbl_neg_novo_total.setStyleSheet(
            "font-size:11px;font-weight:600;color:#117A65;background:transparent;"
        )
        vn.addWidget(self._lbl_neg_novo_total)

        hb_neg = QHBoxLayout(); hb_neg.setSpacing(8)

        self._btn_negociar = btn_solid("🤝  NEGOCIAR", "#1A5276", h=36)
        self._btn_negociar.setEnabled(False)
        self._btn_negociar.clicked.connect(self._negociar)
        hb_neg.addWidget(self._btn_negociar)

        self._btn_copiar_neg = btn_outline("📋  Copiar texto")
        self._btn_copiar_neg.setEnabled(False)
        self._btn_copiar_neg.clicked.connect(self._copiar_negociacao)
        hb_neg.addWidget(self._btn_copiar_neg)

        self._btn_whats = btn_outline("🟢  WhatsApp")
        self._btn_whats.setEnabled(False)
        self._btn_whats.clicked.connect(self._abrir_whatsapp_negociacao)
        hb_neg.addWidget(self._btn_whats)

        vn.addLayout(hb_neg)

        self._frame_neg.setVisible(False)
        vl.addWidget(self._frame_neg)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background:#EEEEEE;"); sep2.setFixedHeight(1)
        vl.addWidget(sep2)

        self._btn_ven = btn_solid("📋  Gerar Pedido do Vencedor", RED, h=44)
        self._btn_ven.setEnabled(False)
        self._btn_ven.clicked.connect(self._gerar_pedido)
        vl.addWidget(self._btn_ven)

        self._btn_ii = btn_solid("🔀  Gerar Pedido Item a Item", GREEN, h=40)
        self._btn_ii.setEnabled(False)
        self._btn_ii.clicked.connect(self._gerar_item_item)
        vl.addWidget(self._btn_ii)

        vl.addStretch()
        scroll.setWidget(inner)
        ol = QVBoxLayout(frame); ol.setContentsMargins(0,0,0,0); ol.addWidget(scroll)
        return frame

    def _make_card(self, i):
        c = QFrame()
        c.setStyleSheet(
            "QFrame{background:#F8F8F8;border-radius:10px;border:1px solid #E0E0E0;}")
        vl = QVBoxLayout(c); vl.setContentsMargins(14,12,14,12); vl.setSpacing(6)

        ht = QHBoxLayout(); ht.setSpacing(8)
        ln = QLabel(f"Fornecedor {i+1}")
        ln.setStyleSheet(
            f"font-size:13px;font-weight:bold;color:{COR_F[i]};background:transparent;")
        ln.setObjectName(f"cn_{i}")
        ls = QLabel("—")
        ls.setStyleSheet(
            "font-size:10px;font-weight:600;color:#888;"
            "background:#EEEEEE;border-radius:4px;padding:2px 7px;border:none;")
        ls.setObjectName(f"cs_{i}")
        ht.addWidget(ln); ht.addStretch(); ht.addWidget(ls)
        vl.addLayout(ht)

        hm = QHBoxLayout(); hm.setSpacing(0)
        for key, cor, obj, icone in [
            ("ITENS",    BLUE,  f"ci_{i}", "📦"),
            ("+ BARATOS",GREEN, f"cb_{i}", "✅"),
            ("TOTAL",    RED,   f"ct_{i}", "💰"),
        ]:
            vm = QVBoxLayout(); vm.setSpacing(1); vm.setContentsMargins(0,0,12,0)
            lt2 = QLabel(f"{icone}  {key}")
            lt2.setStyleSheet(
                "font-size:9px;font-weight:700;color:#888;"
                "background:transparent;letter-spacing:0.5px;")
            lv = QLabel("—")
            lv.setStyleSheet(
                f"font-size:16px;font-weight:bold;color:{cor};background:transparent;")
            lv.setObjectName(obj)
            vm.addWidget(lt2); vm.addWidget(lv)
            hm.addLayout(vm)
        hm.addStretch()
        vl.addLayout(hm)
        return c

    # ══════════════════════════════════════════════════════════════════════════
    # DADOS
    # ══════════════════════════════════════════════════════════════════════════

    def _carregar_obras(self):
        try:
            with open(_OBR_JSON, encoding='utf-8') as f:
                self._obras = json.load(f)
        except Exception:
            self._obras = {}
        self._cb_obra.blockSignals(True); self._cb_obra.clear()
        self._cb_obra.addItem("— Selecione a obra —")
        for n in sorted(self._obras):
            self._cb_obra.addItem(n)
        self._cb_obra.blockSignals(False)

    def _on_obra(self, nome):
        fat = self._obras.get(nome, {}).get("faturamento", "")
        if fat:
            idx = self._cb_emp.findText(fat)
            if idx >= 0: self._cb_emp.setCurrentIndex(idx)

    # ══════════════════════════════════════════════════════════════════════════
    # TABELA — inserção e gestão
    # ══════════════════════════════════════════════════════════════════════════

    def _inserir_linha(self, row: int, item: ItemCotacao):
        nomes  = [e.text().strip() or f"F{i+1}" for i, e in enumerate(self._e_forn)]
        melhor = item.melhor_idx()

        subs_validos = [(fi, item.subtotal(fi)) for fi in range(3)
                        if item.subtotal(fi) is not None]
        pior_fi = max(subs_validos, key=lambda x: x[1])[0] if len(subs_validos) > 1 else -1

        self._tbl.insertRow(row)
        self._tbl.setRowHeight(row, 34)

        def ro(txt, align=Qt.AlignCenter, cor="#666"):
            it = QTableWidgetItem(str(txt)); it.setTextAlignment(align)
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            it.setForeground(QBrush(QColor(cor))); return it

        def ed(txt, align=Qt.AlignVCenter|Qt.AlignLeft, cor="#1A1A1A"):
            it = QTableWidgetItem(str(txt)); it.setTextAlignment(align)
            it.setFlags(it.flags() | Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            it.setForeground(QBrush(QColor(cor))); return it

        self._tbl.setItem(row, 0, ro(str(row+1)))
        self._tbl.setItem(row, 1, ed(item.descricao))
        self._tbl.setItem(row, 2, ed(self._fn(item.quantidade), Qt.AlignCenter))
        self._tbl.setItem(row, 3, ed(item.unidade, Qt.AlignCenter, "#555"))

        for fi in range(3):
            cp, cs = 4+fi*2, 5+fi*2
            preco = item.precos[fi]; sub = item.subtotal(fi)
            bst  = (melhor == fi) and sub is not None
            pior = (pior_fi == fi) and sub is not None and len(subs_validos) > 1

            if preco is None:
                bgp = COR_VAZIO; fg_preco = "#AAAAAA"
            elif bst:
                bgp = COR_MELHOR; fg_preco = "#1A7A3C"
            elif pior:
                bgp = COR_PIOR_BG; fg_preco = COR_PIOR_FG.name()
            else:
                bgp = COR_NEUTRO; fg_preco = "#1A1A1A"

            ip = ed(self._fb(preco) if preco is not None else "",
                    Qt.AlignRight|Qt.AlignVCenter, fg_preco)
            ip.setBackground(QBrush(bgp))
            if bst: ff=QFont(); ff.setBold(True); ip.setFont(ff)
            self._tbl.setItem(row, cp, ip)

            fg_sub = "#1A7A3C" if bst else (COR_PIOR_FG.name() if pior else "#555")
            bg_sub = COR_MELHOR if bst else (COR_PIOR_BG if pior else COR_VAZIO)
            is2 = ro(self._fb(sub) if sub is not None else "—",
                     Qt.AlignRight|Qt.AlignVCenter, fg_sub)
            is2.setBackground(QBrush(bg_sub))
            if bst: ff=QFont(); ff.setBold(True); is2.setFont(ff)
            self._tbl.setItem(row, cs, is2)

        ms = item.melhor_sub()
        im = ro(self._fb(ms) if ms else "—", Qt.AlignRight|Qt.AlignVCenter,
                "#1A7A3C" if ms else "#999")
        im.setBackground(QBrush(COR_MELHOR if ms else COR_VAZIO))
        if ms: ff=QFont(); ff.setBold(True); im.setFont(ff)
        self._tbl.setItem(row, 10, im)

        vn = nomes[melhor] if melhor is not None else "—"
        iv = ro(vn, Qt.AlignCenter, "#1A7A3C" if melhor is not None else "#999")
        if melhor is not None: ff=QFont(); ff.setBold(True); iv.setFont(ff)
        self._tbl.setItem(row, 11, iv)

    def _renumerar(self):
        self._bloqueio = True
        self._tbl.blockSignals(True)
        for r in range(self._tbl.rowCount()):
            it = self._tbl.item(r, 0)
            if it: it.setText(str(r+1))
        self._tbl.blockSignals(False)
        self._bloqueio = False

    def _rebuild(self):
        self._bloqueio = True
        self._tbl.blockSignals(True)
        self._tbl.setRowCount(0)
        for r, item in enumerate(self._itens):
            self._inserir_linha(r, item)
        self._tbl.blockSignals(False)
        self._bloqueio = False

    def _atualizar_contador(self):
        n = len(self._itens)
        self._lbl_n.setText(f"{n} item{'ns' if n!=1 else ''}")

    # ══════════════════════════════════════════════════════════════════════════
    # AÇÕES DA TABELA
    # ══════════════════════════════════════════════════════════════════════════

    def _adicionar_item(self):
        self._tbl.blockSignals(True)
        item = ItemCotacao()
        self._itens.append(item)
        row = len(self._itens) - 1
        self._inserir_linha(row, item)
        self._tbl.blockSignals(False)
        self._atualizar_contador()
        QTimer.singleShot(0, lambda: (
            self._tbl.setCurrentCell(row, 1),
            self._tbl.edit(self._tbl.model().index(row, 1))
        ))

    def _apagar_selecionado(self):
        rows = sorted(set(i.row() for i in self._tbl.selectedItems()), reverse=True)
        if not rows: return
        self._tbl.blockSignals(True)
        for r in rows:
            if 0 <= r < len(self._itens):
                self._itens.pop(r)
                self._tbl.removeRow(r)
        self._tbl.blockSignals(False)
        self._renumerar(); self._atualizar_contador(); self._atualizar_dashboard()
        if not self._itens:
            self._adicionar_item()

    def _limpar_tudo(self):
        if QMessageBox.question(self, "Limpar tudo",
                "Remover todos os itens?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self._tbl.blockSignals(True)
        self._itens.clear(); self._tbl.setRowCount(0)
        self._tbl.blockSignals(False)
        self._atualizar_contador(); self._atualizar_dashboard()
        self._adicionar_item()

    def _key_press(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if not self._tbl.state() == QAbstractItemView.EditingState:
                self._apagar_selecionado(); return
        QTableWidget.keyPressEvent(self._tbl, event)

    def _on_changed(self, cell):
        if self._bloqueio: return
        row = cell.row(); col = cell.column()
        if row >= len(self._itens): return
        item = self._itens[row]
        txt  = cell.text().strip()

        if col == 1:
            item.descricao = txt.upper()
        elif col == 2:
            item.quantidade = float(txt.replace(",",".")) if txt else 1.0
        elif col == 3:
            item.unidade = txt.upper() or "UNID."
        elif col in (4, 6, 8):
            fi = (col - 4) // 2
            item.precos[fi] = self._pn(txt)
            self._atualizar_linha(row)
            self._atualizar_totais()
            return

        self._atualizar_totais()

    def _atualizar_linha(self, row: int):
        if row >= len(self._itens): return
        item   = self._itens[row]
        nomes  = [e.text().strip() or f"F{i+1}" for i, e in enumerate(self._e_forn)]
        melhor = item.melhor_idx()
        subs_v = [(fi, item.subtotal(fi)) for fi in range(3) if item.subtotal(fi) is not None]
        pior_fi = max(subs_v, key=lambda x: x[1])[0] if len(subs_v) > 1 else -1

        self._bloqueio = True
        self._tbl.blockSignals(True)

        for fi in range(3):
            cp, cs = 4+fi*2, 5+fi*2
            sub  = item.subtotal(fi)
            bst  = (melhor == fi) and sub is not None
            pior = (pior_fi == fi) and sub is not None and len(subs_v) > 1

            if item.precos[fi] is None:
                fg_preco = "#AAAAAA"; bgp = COR_VAZIO
            elif bst:
                fg_preco = "#1A7A3C"; bgp = COR_MELHOR
            elif pior:
                fg_preco = COR_PIOR_FG.name(); bgp = COR_PIOR_BG
            else:
                fg_preco = "#1A1A1A"; bgp = COR_NEUTRO

            ip = self._tbl.item(row, cp)
            if ip:
                ip.setForeground(QBrush(QColor(fg_preco)))
                ip.setBackground(QBrush(bgp))
                ff = QFont(); ff.setBold(bst); ip.setFont(ff)

            fg_sub = "#1A7A3C" if bst else (COR_PIOR_FG.name() if pior else "#555")
            bg_sub = COR_MELHOR if bst else (COR_PIOR_BG if pior else COR_VAZIO)
            is2 = self._tbl.item(row, cs)
            if is2:
                is2.setText(self._fb(sub) if sub is not None else "—")
                is2.setForeground(QBrush(QColor(fg_sub)))
                is2.setBackground(QBrush(bg_sub))
                ff = QFont(); ff.setBold(bst); is2.setFont(ff)

        ms = item.melhor_sub()
        im = self._tbl.item(row, 10)
        if im:
            im.setText(self._fb(ms) if ms else "—")
            im.setBackground(QBrush(COR_MELHOR if ms else COR_VAZIO))
            im.setForeground(QBrush(QColor("#1A7A3C" if ms else "#999999")))
            ff = QFont(); ff.setBold(bool(ms)); im.setFont(ff)

        iv = self._tbl.item(row, 11)
        if iv:
            vn = nomes[melhor] if melhor is not None else "—"
            iv.setText(vn)
            iv.setForeground(QBrush(QColor("#1A7A3C" if melhor is not None else "#999999")))
            ff = QFont(); ff.setBold(melhor is not None); iv.setFont(ff)

        self._tbl.blockSignals(False)
        self._bloqueio = False
        self._atualizar_totais()

    def _on_forn(self, i, txt):
        n = txt.strip().upper() or f"F{i+1}"
        self._tbl.setHorizontalHeaderItem(4+i*2, QTableWidgetItem(f"Preço {n[:10]}"))
        self._tbl.setHorizontalHeaderItem(5+i*2, QTableWidgetItem(f"Sub {n[:10]}"))
        self._atualizar_dashboard()

    def _on_frete(self, i, t): self._fretes[i] = self._pn(t) or 0.0; self._atualizar_dashboard()
    def _on_desc(self, i, t):  self._descontos[i] = self._pn(t) or 0.0; self._atualizar_dashboard()

    # ══════════════════════════════════════════════════════════════════════════
    # CÁLCULO
    # ══════════════════════════════════════════════════════════════════════════

    def _calcular(self): self._rebuild(); self._atualizar_dashboard()

    def _atualizar_totais(self):
        nomes = [e.text().strip() or f"F{i+1}" for i, e in enumerate(self._e_forn)]
        for fi in range(3):
            tot = sum((it.subtotal(fi) or 0) for it in self._itens) + self._fretes[fi] - self._descontos[fi]
            self._lbl_tot[fi].setText(f"{nomes[fi]}: R$ {self._f(tot)}")
        mt = sum((it.melhor_sub() or 0) for it in self._itens)
        self._lbl_melhor.setText(f"✓ Melhor item a item: R$ {self._f(mt)}")

    def _calcular_res(self):
        res = []
        for fi in range(3):
            nome = self._e_forn[fi].text().strip() or f"Fornecedor {fi+1}"
            r = ResultadoFornecedor(nome, fi)
            r.total_itens = len(self._itens)
            r.frete = self._fretes[fi]; r.desconto = self._descontos[fi]
            for it in self._itens:
                sub = it.subtotal(fi)
                if sub is not None: r.itens_cotados += 1; r.subtotal_val += sub
                if it.melhor_idx() == fi: r.itens_baratos += 1
            res.append(r)
        return res

    def _vencedor(self, res):
        n = len(self._itens)
        val = [r for r in res if r.itens_cotados > 0]
        if not val: return None, "Preencha os preços e clique em Calcular", ""
        comp = [r for r in val if r.itens_cotados == n]
        if comp:
            v = min(comp, key=lambda r: (r.total_final, -r.itens_baratos))
            return v, f"Cobertura total ({n}/{n}) — Total R$ {self._f(v.total_final)}", ""
        mc = max(r.itens_cotados for r in val)
        top = [r for r in val if r.itens_cotados == mc]
        v = min(top, key=lambda r: (r.total_final, -r.itens_baratos))
        return v, f"Maior cobertura ({mc}/{n})", "⚠️  Nenhum fornecedor cotou todos os itens. Negocie os itens faltantes."

    def _atualizar_dashboard(self):
        res = self._calcular_res()
        v, mot, obs = self._vencedor(res)
        n = len(self._itens)

        if v is None:
            self._lbl_ven.setText("—")
            self._lbl_mot.setText(mot)
            self._btn_ven.setEnabled(False); self._btn_ii.setEnabled(False)
            self._resetar_negociacao()
            return

        self._venc_idx = v.idx; self._resultados = res
        cor = CORES_EMPRESA.get(v.nome.upper(), RED)

        self._lbl_ven.setText(v.nome.upper())
        self._lbl_ven.setStyleSheet(
            f"font-size:26px;font-weight:bold;color:{cor};background:transparent;")

        outros = [r for r in res if r.idx != v.idx and r.itens_cotados > 0]
        partes_mot = []

        if v.itens_cotados == n:
            partes_mot.append(f"Cotou todos os {n} itens")
        else:
            partes_mot.append(f"Cotou {v.itens_cotados} de {n} itens (maior cobertura)")

        if outros:
            seg = min(outros, key=lambda r: r.total_final if r.itens_cotados > 0 else 99999)
            if seg.total_final > 0 and v.total_final > 0:
                dif = seg.total_final - v.total_final
                pct = dif / seg.total_final * 100
                if dif > 0:
                    partes_mot.append(
                        f"{pct:.1f}% mais barato que {seg.nome} "
                        f"(economia de R$ {self._f(dif)})")
                elif dif < 0:
                    partes_mot.append(
                        f"Venceu por maior cobertura — "
                        f"R$ {self._f(abs(dif))} mais caro que {seg.nome}")

        if v.itens_baratos > 0:
            partes_mot.append(
                f"Melhor preço em {v.itens_baratos} item{'ns' if v.itens_baratos!=1 else ''}")

        if v.frete > 0:
            partes_mot.append(f"Frete incluso: R$ {self._f(v.frete)}")
        if v.desconto > 0:
            partes_mot.append(f"Desconto: R$ {self._f(v.desconto)}")

        self._lbl_mot.setText("  •  ".join(partes_mot))

        bg_ven = "#F0FFF4" if cor == GREEN else "#FEF9F9"
        self._frame_ven.setStyleSheet(
            f"QFrame{{background:{bg_ven};border-radius:12px;"
            f"border-left:5px solid {cor};"
            f"border-top:1px solid #E8E8E8;border-right:1px solid #E8E8E8;"
            f"border-bottom:1px solid #E8E8E8;}}"
        )

        lv_total = self._frame_ven.ms_total.findChild(QLabel, "v_val_total")
        if lv_total: lv_total.setText(f"R$ {self._f(v.total_final)}")
        lv_bar = self._frame_ven.ms_baratos.findChild(QLabel, "v_val_bar")
        if lv_bar: lv_bar.setText(f"{v.itens_baratos}/{n}")

        lv_econ = self._frame_ven.ms_econ.findChild(QLabel, "v_val_econ")
        if lv_econ:
            if outros:
                seg = min(outros, key=lambda r: r.total_final if r.total_final > 0 else 99999)
                dif = seg.total_final - v.total_final
                lv_econ.setText(f"R$ {self._f(abs(dif))}" if dif != 0 else "—")
                lv_econ.setStyleSheet(
                    f"font-size:17px;font-weight:bold;"
                    f"color:{'#1A5276' if dif >= 0 else '#C0392B'};"
                    f"background:transparent;")
            else:
                lv_econ.setText("—")

        for fi, r in enumerate(res):
            c = self._cards[fi]
            destaque = (fi == v.idx)

            lb_nome = c.findChild(QLabel, f"cn_{fi}")
            if lb_nome:
                lb_nome.setText(r.nome)
                lb_nome.setStyleSheet(
                    f"font-size:13px;font-weight:bold;"
                    f"color:{COR_F[fi] if not destaque else cor};"
                    f"background:transparent;")

            lb_status = c.findChild(QLabel, f"cs_{fi}")
            if lb_status:
                st = r.status(n)
                bg_st = "#D5F5E3" if "Completo" in st else ("#FEF9E7" if "Parcial" in st else "#F4F6F7")
                cor_st = "#1A7A3C" if "Completo" in st else ("#7D6608" if "Parcial" in st else "#888")
                lb_status.setText(st)
                lb_status.setStyleSheet(
                    f"font-size:10px;font-weight:600;color:{cor_st};"
                    f"background:{bg_st};border-radius:4px;padding:2px 7px;border:none;")

            for obj, val in [
                (f"ci_{fi}", f"{r.itens_cotados}/{n}"),
                (f"cb_{fi}", str(r.itens_baratos)),
                (f"ct_{fi}", f"R$ {self._f(r.total_final)}"),
            ]:
                lb = c.findChild(QLabel, obj)
                if lb: lb.setText(val)

            if destaque:
                c.setStyleSheet(
                    f"QFrame{{background:#F0FFF4;border-radius:10px;"
                    f"border:2px solid {cor};}}")
            else:
                c.setStyleSheet(
                    "QFrame{background:#F8F8F8;border-radius:10px;"
                    "border:1px solid #E0E0E0;}")

        self._lbl_obs.setText(obs); self._lbl_obs.setVisible(bool(obs))
        self._btn_ven.setEnabled(True); self._btn_ii.setEnabled(True)
        self._atualizar_totais()
        self._atualizar_negociacao()

    # ══════════════════════════════════════════════════════════════════════════
    # NEGOCIAÇÃO
    # ══════════════════════════════════════════════════════════════════════════

    def _resetar_negociacao(self):
        if hasattr(self, '_frame_neg'):
            self._frame_neg.setVisible(False)
        self._itens_negociacao = []
        if hasattr(self, '_btn_negociar'):
            self._btn_negociar.setEnabled(False)
        if hasattr(self, '_btn_copiar_neg'):
            self._btn_copiar_neg.setEnabled(False)
        if hasattr(self, '_btn_whats'):
            self._btn_whats.setEnabled(False)
        if hasattr(self, '_lbl_neg_titulo'):
            self._lbl_neg_titulo.setText("Itens para Negociação")
        if hasattr(self, '_lbl_neg_resumo'):
            self._lbl_neg_resumo.setText("Nenhuma análise de negociação disponível.")
        if hasattr(self, '_lbl_neg_stats'):
            self._lbl_neg_stats.setText("0 itens • Economia potencial: R$ 0,00")
        if hasattr(self, '_lbl_neg_novo_total'):
            self._lbl_neg_novo_total.setText("Novo total possível: R$ 0,00")

    def _coletar_itens_negociacao(self):
        if not hasattr(self, '_venc_idx'):
            return []

        itens_neg = []
        fi_venc = self._venc_idx
        nomes = [e.text().strip() or f"Fornecedor {i+1}" for i, e in enumerate(self._e_forn)]

        for it in self._itens:
            melhor_idx = it.melhor_idx()
            if melhor_idx is None or melhor_idx == fi_venc:
                continue

            preco_vencedor = it.precos[fi_venc]
            preco_melhor = it.precos[melhor_idx]

            if preco_vencedor is None or preco_melhor is None:
                continue

            try:
                qtd = float(it.quantidade or 0)
                diff_unit = float(preco_vencedor) - float(preco_melhor)
                diff_total = diff_unit * qtd
                pct = (diff_unit / float(preco_vencedor) * 100.0) if float(preco_vencedor) > 0 else 0.0
            except Exception:
                continue

            if diff_total <= 0:
                continue

            if diff_unit < NEGOCIACAO_DIF_MIN and pct < NEGOCIACAO_PCT_MIN:
                continue

            itens_neg.append({
                "descricao": it.descricao,
                "quantidade": it.quantidade,
                "unidade": it.unidade,
                "fornecedor_vencedor": nomes[fi_venc],
                "preco_vencedor": preco_vencedor,
                "fornecedor_melhor": nomes[melhor_idx],
                "preco_melhor": preco_melhor,
                "diferenca_unitaria": diff_unit,
                "diferenca_total": diff_total,
                "percentual": pct,
            })

        return itens_neg

    def _atualizar_negociacao(self):
        if not hasattr(self, '_frame_neg'):
            return

        if not hasattr(self, '_venc_idx'):
            self._resetar_negociacao()
            return

        itens = self._coletar_itens_negociacao()
        self._itens_negociacao = itens

        if not itens:
            self._frame_neg.setVisible(True)
            self._lbl_neg_titulo.setText("Itens para Negociação")
            self._lbl_neg_resumo.setText("Nenhum item relevante encontrado para negociar com o fornecedor vencedor.")
            self._lbl_neg_stats.setText("0 itens • Economia potencial: R$ 0,00")
            self._lbl_neg_novo_total.setText("Novo total possível: R$ 0,00")
            self._btn_negociar.setEnabled(False)
            self._btn_copiar_neg.setEnabled(False)
            self._btn_whats.setEnabled(False)
            return

        economia = sum(x["diferenca_total"] for x in itens)
        qtd_itens = len(itens)
        vencedor = self._e_forn[self._venc_idx].text().strip() or f"Fornecedor {self._venc_idx+1}"
        total_vencedor = self._resultados[self._venc_idx].total_final if hasattr(self, "_resultados") else 0.0
        novo_total = max(0.0, total_vencedor - economia)

        self._frame_neg.setVisible(True)
        self._lbl_neg_titulo.setText(f"Itens para Negociação — {vencedor.upper()}")
        self._lbl_neg_resumo.setText(
            f"Foram encontrados {qtd_itens} item(ns) onde outro fornecedor apresentou preço melhor."
        )
        self._lbl_neg_stats.setText(
            f"{qtd_itens} item(ns) • Economia potencial: R$ {self._f(economia)}"
        )
        self._lbl_neg_novo_total.setText(
            f"Novo total possível: R$ {self._f(novo_total)}"
        )
        self._btn_negociar.setEnabled(True)
        self._btn_copiar_neg.setEnabled(True)
        self._btn_whats.setEnabled(True)

    def _gerar_texto_negociacao(self, itens):
        if not itens:
            return "Nenhum item encontrado para negociação."

        obra = self._cb_obra.currentText().strip()
        obra = "" if obra.startswith("—") else obra
        vencedor = itens[0]["fornecedor_vencedor"]
        economia_total = sum(item["diferenca_total"] for item in itens)
        total_atual = self._resultados[self._venc_idx].total_final if hasattr(self, '_resultados') and hasattr(self, '_venc_idx') else 0.0
        novo_total = max(0.0, total_atual - economia_total)

        linhas = []
        linhas.append("Prezado,")
        linhas.append("")
        linhas.append(
            "Na análise comparativa da cotação{} identificamos alguns itens em que há ofertas mais competitivas no mercado.".format(
                f" da obra {obra}," if obra else ","
            )
        )
        linhas.append("")
        linhas.append(f"Segue abaixo para revisão de preços com {vencedor}:")
        linhas.append("")

        for item in itens:
            linhas.append(
                f"- {item['descricao']} | Qtd: {self._fn(item['quantidade'])} {item['unidade']} | "
                f"Atual: R$ {self._f(item['preco_vencedor'])} | "
                f"Concorrente ({item['fornecedor_melhor']}): R$ {self._f(item['preco_melhor'])} | "
                f"Dif.: R$ {self._f(item['diferenca_total'])}"
            )

        linhas.append("")
        linhas.append(f"Economia potencial total: R$ {self._f(economia_total)}")
        linhas.append(f"Novo total possível: R$ {self._f(novo_total)}")
        linhas.append("")
        linhas.append("Consegue revisar esses valores para avançarmos?")

        return "\n".join(linhas)

    def _copiar_negociacao(self):
        itens = getattr(self, "_itens_negociacao", None) or self._coletar_itens_negociacao()

        if not itens:
            QMessageBox.information(self, "Negociação", "Nenhum item encontrado para negociação.")
            return

        texto = self._gerar_texto_negociacao(itens)
        QApplication.clipboard().setText(texto)
        QMessageBox.information(
            self,
            "Texto copiado",
            "✅ Texto de negociação copiado para a área de transferência."
        )

    def _abrir_whatsapp_negociacao(self):
        itens = getattr(self, "_itens_negociacao", None) or self._coletar_itens_negociacao()
        if not itens:
            QMessageBox.information(self, "Negociação", "Nenhum item encontrado para negociação.")
            return
        texto = self._gerar_texto_negociacao(itens)
        url = QUrl(f"https://wa.me/?text={quote(texto)}")
        if not QDesktopServices.openUrl(url):
            QMessageBox.warning(self, "WhatsApp", "Não foi possível abrir o WhatsApp Web.")

    def _mostrar_previa_negociacao(self, itens):
        """Diálogo de prévia com tabela rolável — substitui o QMessageBox."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QDialogButtonBox, QScrollArea
        if not itens:
            QMessageBox.information(self, "Negociação", "Não há itens para negociação.")
            return

        economia_total = sum(x["diferenca_total"] for x in itens)
        vencedor = itens[0]["fornecedor_vencedor"] if itens else "—"
        total_atual = self._resultados[self._venc_idx].total_final if hasattr(self, "_resultados") else 0.0
        novo_total  = max(0.0, total_atual - economia_total)

        dlg = QDialog(self)
        dlg.setWindowTitle("Prévia de Negociação")
        dlg.setMinimumSize(780, 480)
        dlg.setStyleSheet(f"background:{WHITE}; color:{TXT};")
        vl = QVBoxLayout(dlg); vl.setContentsMargins(16,14,16,14); vl.setSpacing(10)

        # Cabeçalho
        lbl_tit = QLabel(f"Itens para negociar com <b>{vencedor.upper()}</b>")
        lbl_tit.setStyleSheet(f"font-size:14px;font-weight:bold;color:{GRAY};background:transparent;")
        vl.addWidget(lbl_tit)

        # Tabela dos itens
        tbl = QTableWidget(len(itens), 7)
        tbl.setHorizontalHeaderLabels([
            "Descrição", "Qtd", "Unid",
            f"Preço {vencedor[:12]}", "Melhor concorrente", "Dif. unit.", "Dif. total"
        ])
        tbl.setStyleSheet(CSS_TABLE)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectRows)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(True)
        tbl.setFrameShape(QFrame.NoFrame)
        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for c, w in enumerate([0, 50, 50, 100, 140, 85, 85], start=0):
            if c > 0: tbl.setColumnWidth(c, w)

        for r, item in enumerate(itens):
            tbl.setRowHeight(r, 32)
            bg = WHITE if r % 2 == 0 else "#F8F8F8"

            def cell(txt, align=Qt.AlignVCenter|Qt.AlignLeft, cor="#1A1A1A", bold=False):
                it2 = QTableWidgetItem(str(txt))
                it2.setTextAlignment(align)
                it2.setFlags(it2.flags() & ~Qt.ItemIsEditable)
                it2.setForeground(QBrush(QColor(cor)))
                it2.setBackground(QBrush(QColor(bg)))
                if bold: ff=QFont(); ff.setBold(True); it2.setFont(ff)
                return it2

            tbl.setItem(r, 0, cell(item["descricao"][:55], bold=True))
            tbl.setItem(r, 1, cell(self._fn(item["quantidade"]), Qt.AlignCenter|Qt.AlignVCenter))
            tbl.setItem(r, 2, cell(item["unidade"], Qt.AlignCenter|Qt.AlignVCenter, "#555"))
            tbl.setItem(r, 3, cell(f"R$ {self._f(item['preco_vencedor'])}", Qt.AlignRight|Qt.AlignVCenter, "#C0392B"))
            tbl.setItem(r, 4, cell(
                f"{item['fornecedor_melhor'][:14]}: R$ {self._f(item['preco_melhor'])}",
                Qt.AlignRight|Qt.AlignVCenter, "#1A7A3C"))
            tbl.setItem(r, 5, cell(f"R$ {self._f(item['diferenca_unitaria'])}", Qt.AlignRight|Qt.AlignVCenter, "#1A5276"))
            tbl.setItem(r, 6, cell(f"R$ {self._f(item['diferenca_total'])}", Qt.AlignRight|Qt.AlignVCenter, "#1A5276", bold=True))

        vl.addWidget(tbl, 1)

        # Rodapé com totais
        rod = QFrame()
        rod.setStyleSheet("QFrame{background:#F0F8FF;border-radius:8px;border:1px solid #D6EAF8;}")
        hl_rod = QHBoxLayout(rod); hl_rod.setContentsMargins(14,10,14,10); hl_rod.setSpacing(30)

        def stat(label, valor, cor="#1A1A1A"):
            vls = QVBoxLayout(); vls.setSpacing(2)
            l1 = QLabel(label)
            l1.setStyleSheet("font-size:9px;font-weight:700;color:#888;background:transparent;letter-spacing:1px;")
            l2 = QLabel(valor)
            l2.setStyleSheet(f"font-size:16px;font-weight:bold;color:{cor};background:transparent;")
            vls.addWidget(l1); vls.addWidget(l2)
            return vls

        hl_rod.addLayout(stat("ITENS PARA NEGOCIAR", str(len(itens)), "#1A5276"))
        hl_rod.addLayout(stat("ECONOMIA POTENCIAL", f"R$ {self._f(economia_total)}", GREEN))
        hl_rod.addLayout(stat("TOTAL ATUAL", f"R$ {self._f(total_atual)}", "#C0392B"))
        hl_rod.addLayout(stat("NOVO TOTAL POSSÍVEL", f"R$ {self._f(novo_total)}", "#1A7A3C"))
        hl_rod.addStretch()
        vl.addWidget(rod)

        # Botões
        hl_btn = QHBoxLayout(); hl_btn.setSpacing(8)
        btn_copiar = btn_solid("📋  Copiar texto", "#1A5276", h=36)
        btn_copiar.clicked.connect(lambda: (
            QApplication.clipboard().setText(self._gerar_texto_negociacao(itens)),
            QMessageBox.information(dlg, "Copiado", "✅ Texto copiado para a área de transferência.")
        ))
        btn_whats = btn_solid("🟢  WhatsApp", "#25D366", h=36)
        btn_whats.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl(f"https://wa.me/?text={quote(self._gerar_texto_negociacao(itens))}")))
        btn_fechar = btn_outline("Fechar")
        btn_fechar.clicked.connect(dlg.accept)
        hl_btn.addWidget(btn_copiar)
        hl_btn.addWidget(btn_whats)
        hl_btn.addStretch()
        hl_btn.addWidget(btn_fechar)
        vl.addLayout(hl_btn)

        dlg.exec()

    def _negociar(self):
        itens = self._itens_negociacao or self._coletar_itens_negociacao()
        if not itens:
            QMessageBox.information(self, "Negociação", "Nenhum item encontrado para negociação.")
            return
        self._mostrar_previa_negociacao(itens)

    # ══════════════════════════════════════════════════════════════════════════
    # SALVAR / CARREGAR
    # ══════════════════════════════════════════════════════════════════════════

    def _nome_padrao_cotacao(self):
        obra = self._cb_obra.currentText().strip()
        obra = "SEM_OBRA" if not obra or obra.startswith("—") else obra.upper()
        obra = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in obra).strip().replace(" ", "_")
        data = datetime.now().strftime("%Y%m%d_%H%M")
        return f"cotacao_{obra}_{data}.json"

    def _serializar_cotacao(self):
        return {
            "versao": 1,
            "arquivo_origem": self._arquivo_cotacao_atual,
            "obra": self._cb_obra.currentText(),
            "empresa_faturadora": self._cb_emp.currentText(),
            "fornecedores": [e.text().strip() for e in self._e_forn],
            "fretes": self._fretes[:],
            "descontos": self._descontos[:],
            "itens": [
                {
                    "descricao": it.descricao,
                    "quantidade": it.quantidade,
                    "unidade": it.unidade,
                    "precos": it.precos[:],
                }
                for it in self._itens
                if it.descricao.strip() or any(p is not None for p in it.precos)
            ],
        }

    def _aplicar_cotacao(self, dados: dict):
        self._bloqueio = True
        self._tbl.blockSignals(True)

        obra = dados.get("obra", "")
        idx_obra = self._cb_obra.findText(obra)
        if idx_obra >= 0:
            self._cb_obra.setCurrentIndex(idx_obra)
        else:
            self._cb_obra.setEditText(obra)

        emp = dados.get("empresa_faturadora", "")
        idx_emp = self._cb_emp.findText(emp)
        if idx_emp >= 0:
            self._cb_emp.setCurrentIndex(idx_emp)

        for i, nome in enumerate(dados.get("fornecedores", ["", "", ""])):
            if i < len(self._e_forn):
                self._e_forn[i].setText(nome or "")

        fretes = dados.get("fretes", [0.0, 0.0, 0.0])
        descontos = dados.get("descontos", [0.0, 0.0, 0.0])
        self._fretes = [float(v or 0.0) for v in fretes[:3]] + [0.0] * (3 - len(fretes[:3]))
        self._descontos = [float(v or 0.0) for v in descontos[:3]] + [0.0] * (3 - len(descontos[:3]))

        for i in range(3):
            self._e_frete[i].setText(self._f(self._fretes[i]))
            self._e_desc[i].setText(self._f(self._descontos[i]))

        self._itens = []
        for reg in dados.get("itens", []):
            item = ItemCotacao(
                desc=reg.get("descricao", ""),
                qtd=reg.get("quantidade", 1.0),
                unid=reg.get("unidade", "UNID."),
            )
            precos = reg.get("precos", [None, None, None])
            item.precos = (precos[:3] + [None, None, None])[:3]
            self._itens.append(item)

        if not self._itens:
            self._itens = [ItemCotacao()]

        self._tbl.setRowCount(0)
        for r, item in enumerate(self._itens):
            self._inserir_linha(r, item)

        self._tbl.blockSignals(False)
        self._bloqueio = False
        self._atualizar_contador()
        self._atualizar_dashboard()

    def _salvar_cotacao_json(self):
        dados = self._serializar_cotacao()
        if not dados["itens"]:
            QMessageBox.information(self, "Salvar cotação", "Não há itens para salvar.")
            return

        arquivo_padrao = self._arquivo_cotacao_atual or os.path.join(_COT_DIR, self._nome_padrao_cotacao())
        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar cotação",
            arquivo_padrao,
            "Arquivos JSON (*.json)"
        )
        if not caminho:
            return

        if not caminho.lower().endswith(".json"):
            caminho += ".json"

        try:
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            self._arquivo_cotacao_atual = caminho
            QMessageBox.information(self, "Cotação salva", f"✅ Cotação salva com sucesso.\n\n{caminho}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", f"Não foi possível salvar a cotação.\n\n{e}")

    def _carregar_cotacao_json(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Carregar cotação",
            self._arquivo_cotacao_atual or _COT_DIR,
            "Arquivos JSON (*.json)"
        )
        if not caminho:
            return

        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            self._arquivo_cotacao_atual = caminho
            self._aplicar_cotacao(dados)
            QMessageBox.information(self, "Cotação carregada", f"✅ Cotação carregada com sucesso.\n\n{caminho}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao carregar", f"Não foi possível carregar a cotação.\n\n{e}")

    # ══════════════════════════════════════════════════════════════════════════
    # GERAR PEDIDO
    # ══════════════════════════════════════════════════════════════════════════

    def _gerar_pedido(self):
        if not hasattr(self, '_venc_idx'): return
        fi = self._venc_idx
        nome = self._e_forn[fi].text().strip()
        if not nome:
            QMessageBox.warning(self, "Atenção", "Preencha o nome do fornecedor vencedor.")
            return
        itens = [
            {"descricao": it.descricao, "quantidade": it.quantidade, "unidade": it.unidade,
             "valor_unitario": it.precos[fi], "valor_total": it.subtotal(fi)}
            for it in self._itens if it.subtotal(fi) is not None
        ]
        if not itens:
            QMessageBox.warning(self, "Atenção", f"'{nome}' não tem preços preenchidos.")
            return
        self._abrir_form(nome, itens)

    def _gerar_item_item(self):
        if not hasattr(self, '_resultados'): return
        grupos = {}
        for it in self._itens:
            mi = it.melhor_idx()
            if mi is not None: grupos.setdefault(mi, []).append(it)
        if not grupos:
            QMessageBox.warning(self, "Atenção", "Nenhum item com preço preenchido.")
            return
        nomes = [e.text().strip() or f"Fornecedor {i+1}" for i, e in enumerate(self._e_forn)]
        for fi, its in grupos.items():
            itens = [
                {"descricao": it.descricao, "quantidade": it.quantidade, "unidade": it.unidade,
                 "valor_unitario": it.precos[fi], "valor_total": it.subtotal(fi)}
                for it in its if it.subtotal(fi) is not None
            ]
            if itens: self._abrir_form(nomes[fi], itens)

    def _abrir_form(self, fornecedor, itens):
        obra = self._cb_obra.currentText()
        obra = "" if obra.startswith("—") else obra
        emp  = self._cb_emp.currentText()
        try:
            mw = self.window()
            if hasattr(mw, '_pages') and 'pedido' in mw._pages:
                pw = mw._pages['pedido']
                if hasattr(pw, 'preencher_da_cotacao'):
                    pw.preencher_da_cotacao(fornecedor=fornecedor, obra=obra, empresa=emp, itens=itens)
                    if hasattr(mw, '_nav'): mw._nav('pedido')
                    QMessageBox.information(self, "Formulário preenchido!",
                        f"✅  Pedido para <b>{fornecedor}</b> pré-preenchido.<br>"
                        f"Revise na aba <b>Pedido de Compra</b>.")
                    return
        except Exception as e:
            print(f"[Cotação] {e}")
        QMessageBox.information(self, "Pronto",
            f"Fornecedor: {fornecedor}\nObra: {obra or '—'}\nItens: {len(itens)}\n\nVá para Pedido de Compra.")

    # ══════════════════════════════════════════════════════════════════════════
    # NOVA COTAÇÃO
    # ══════════════════════════════════════════════════════════════════════════

    def _nova_cotacao(self):
        if QMessageBox.question(self, "Nova cotação", "Deseja limpar todos os dados?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self._arquivo_cotacao_atual = ""
        self._itens = []
        for e in self._e_forn: e.clear()
        for e in self._e_frete: e.setText("0,00")
        for e in self._e_desc:  e.setText("0,00")
        self._fretes = [0.0, 0.0, 0.0]; self._descontos = [0.0, 0.0, 0.0]
        self._lbl_ven.setText("—")
        self._lbl_mot.setText("Preencha os preços e clique em Calcular")
        self._btn_ven.setEnabled(False); self._btn_ii.setEnabled(False)
        self._resetar_negociacao()
        self._tbl.setRowCount(0)
        self._adicionar_item()

    def preencher_da_cotacao(self, fornecedor="", obra="", empresa="", itens=None):
        pass

    @staticmethod
    def _vsep():
        s = QFrame(); s.setFrameShape(QFrame.VLine)
        s.setStyleSheet("background:#CCC;border:none;")
        s.setFixedWidth(1); s.setFixedHeight(38)
        return s

    @staticmethod
    def _pn(txt):
        if txt is None or txt == "": return None
        try:
            return float(str(txt).replace("R$","").replace(" ","").replace(".","").replace(",","."))
        except: return None

    @staticmethod
    def _f(v):
        try: return f"{float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
        except: return "0,00"

    @staticmethod
    def _fb(v):
        try: return f"{float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
        except: return ""

    @staticmethod
    def _fn(v):
        try:
            f = float(v)
            return str(int(f)) if f == int(f) else f"{f:.3f}".rstrip("0").rstrip(".")
        except: return "1"

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self._carregar_obras)
