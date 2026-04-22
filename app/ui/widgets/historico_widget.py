# app/ui/widgets/historico_widget.py
# Aba de histórico com dashboard e filtros.
import os
from datetime import datetime, date
from collections import defaultdict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QGraphicsDropShadowEffect, QSplitter, QScrollArea,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from app.ui.style import (
    RED, GRAY, WHITE, BG, BDR, TXT, TXT_S, SEL, HOV, GREEN, BLUE,
    CSS_TABLE, CSS_BUSCA, CSS_COMBO, CORES_EMPRESA,
    btn_solid, btn_outline, btn_filtro, card_container,
)

# ── Matplotlib ────────────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.ticker as mticker
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

PURPLE = "#8E44AD"
ORANGE = "#E67E22"

MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


# ══════════════════════════════════════════════════════════════════════════════
# WIDGET PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class HistoricoWidget(QWidget):

    def __init__(self):
        super().__init__()
        self._todos       = []   # todos os pedidos do banco
        self._filtrados   = []   # pedidos após filtros
        self._ano_atual   = datetime.now().year
        self._build()
        self._carregar()

    # ══════════════════════════════════════════════════════════════════════════
    # CONSTRUÇÃO
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        self.setStyleSheet(f"background:{BG};")
        vl = QVBoxLayout(self)
        vl.setContentsMargins(24, 20, 24, 16)
        vl.setSpacing(16)

        # ── Cabeçalho ─────────────────────────────────────────────────────────
        hl_top = QHBoxLayout()
        tv = QVBoxLayout(); tv.setSpacing(2)
        titulo = QLabel("Histórico & Dashboard")
        titulo.setStyleSheet(
            f"font-size:20px; font-weight:bold; color:{GRAY}; background:transparent;")
        sub = QLabel("Análise executiva de pedidos e gastos")
        sub.setStyleSheet(f"font-size:11px; color:{TXT_S}; background:transparent;")
        tv.addWidget(titulo); tv.addWidget(sub)
        hl_top.addLayout(tv)
        hl_top.addStretch()
        btn_att = btn_solid("↻  Atualizar", "#95A5A6")
        btn_att.clicked.connect(self._carregar)
        hl_top.addWidget(btn_att)
        vl.addLayout(hl_top)

        # ── Filtros ───────────────────────────────────────────────────────────
        vl.addWidget(self._build_filtros())

        # ── Cards ─────────────────────────────────────────────────────────────
        vl.addLayout(self._build_cards())

        # ── Corpo: gráfico + tabela ───────────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background:#D8CCCC;
                width:5px;
                border-radius:2px;
            }
            QSplitter::handle:hover {
                background:#C0392B;
            }
        """)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_grafico())
        splitter.addWidget(self._build_tabela())
        splitter.setSizes([520, 600])
        vl.addWidget(splitter, 1)

    # ── Filtros ───────────────────────────────────────────────────────────────

    def _build_filtros(self) -> QWidget:
        box = QFrame()
        box.setStyleSheet(
            f"QFrame {{ background:{WHITE}; border-radius:10px;"
            f"border:1px solid #EEE5E5; }}")
        hl = QHBoxLayout(box)
        hl.setContentsMargins(16, 10, 16, 10)
        hl.setSpacing(14)

        def lbl(t):
            l = QLabel(t)
            l.setStyleSheet(
                f"font-size:10px; font-weight:700; color:{TXT_S};"
                f"background:transparent; border:none; letter-spacing:1px;")
            return l

        # Ano
        vl_ano = QVBoxLayout(); vl_ano.setSpacing(4)
        vl_ano.addWidget(lbl("ANO"))
        self._cb_ano = QComboBox()
        self._cb_ano.setMinimumWidth(80)
        self._cb_ano.setStyleSheet(CSS_COMBO)
        vl_ano.addWidget(self._cb_ano)
        hl.addLayout(vl_ano)

        _sep = lambda: self._vsep()

        # Empresa
        vl_emp = QVBoxLayout(); vl_emp.setSpacing(4)
        vl_emp.addWidget(lbl("EMPRESA"))
        self._cb_emp = QComboBox()
        self._cb_emp.setMinimumWidth(130)
        self._cb_emp.setStyleSheet(CSS_COMBO)
        self._cb_emp.addItem("Todas")
        for emp in ["BRASUL", "JB", "B&B", "INTERIORANA", "INTERBRAS"]:
            self._cb_emp.addItem(emp)
        vl_emp.addWidget(self._cb_emp)
        hl.addLayout(vl_emp)

        hl.addWidget(self._vsep())

        # Obra
        vl_obra = QVBoxLayout(); vl_obra.setSpacing(4)
        vl_obra.addWidget(lbl("OBRA"))
        self._cb_obra = QComboBox()
        self._cb_obra.setMinimumWidth(200)
        self._cb_obra.setStyleSheet(CSS_COMBO)
        self._cb_obra.addItem("Todas")
        vl_obra.addWidget(self._cb_obra)
        hl.addLayout(vl_obra)

        hl.addWidget(self._vsep())

        # Busca rápida
        vl_busca = QVBoxLayout(); vl_busca.setSpacing(4)
        vl_busca.addWidget(lbl("BUSCA"))
        self._e_busca = QLineEdit()
        self._e_busca.setPlaceholderText("Fornecedor ou nº pedido...")
        self._e_busca.setMinimumWidth(180)
        self._e_busca.setStyleSheet(CSS_BUSCA.replace("36px", "30px"))
        vl_busca.addWidget(self._e_busca)
        hl.addLayout(vl_busca)

        hl.addStretch()

        # Botão limpar
        btn_clear = btn_outline("✕  Limpar filtros")
        btn_clear.clicked.connect(self._limpar_filtros)
        hl.addWidget(btn_clear)

        # Conecta sinais
        self._cb_ano.currentTextChanged.connect(self._aplicar_filtros)
        self._cb_emp.currentTextChanged.connect(self._aplicar_filtros)
        self._cb_obra.currentTextChanged.connect(self._aplicar_filtros)
        self._e_busca.textChanged.connect(self._aplicar_filtros)

        return box

    # ── Cards ─────────────────────────────────────────────────────────────────

    def _build_cards(self) -> QHBoxLayout:
        hl = QHBoxLayout(); hl.setSpacing(14)

        self._card_pedidos,   self._lv_pedidos   = self._make_card("PEDIDOS",         "—", RED)
        self._card_valor,     self._lv_valor      = self._make_card("VALOR TOTAL",     "—", GREEN)
        self._card_obras,     self._lv_obras      = self._make_card("OBRAS ATIVAS",    "—", BLUE)
        self._card_fornec,    self._lv_fornec     = self._make_card("FORNECEDORES",    "—", ORANGE)
        self._card_ticket,    self._lv_ticket     = self._make_card("TICKET MÉDIO",    "—", PURPLE)

        for c in [self._card_pedidos, self._card_valor,
                  self._card_obras, self._card_fornec, self._card_ticket]:
            hl.addWidget(c)
        hl.addStretch()
        return hl

    def _make_card(self, titulo, valor, cor):
        card = QFrame()
        card.setFixedHeight(78)
        card.setMinimumWidth(155)
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
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(12); sombra.setOffset(0,2); sombra.setColor(QColor(0,0,0,15))
        card.setGraphicsEffect(sombra)
        vl = QVBoxLayout(card); vl.setContentsMargins(14,10,14,10); vl.setSpacing(3)
        lt = QLabel(titulo)
        lt.setStyleSheet(
            f"font-size:9px; font-weight:700; color:{TXT_S};"
            f"background:transparent; border:none; letter-spacing:1px;")
        lv = QLabel(str(valor))
        lv.setStyleSheet(
            f"font-size:20px; font-weight:bold; color:{cor};"
            f"background:transparent; border:none;")
        lv.setObjectName("card_val")
        vl.addWidget(lt); vl.addWidget(lv)
        return card, lv

    # ── Gráfico ───────────────────────────────────────────────────────────────

    def _build_grafico(self) -> QFrame:
        frame = card_container()
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(16); sombra.setOffset(0,2); sombra.setColor(QColor(0,0,0,18))
        frame.setGraphicsEffect(sombra)
        vl = QVBoxLayout(frame); vl.setContentsMargins(16, 14, 16, 10); vl.setSpacing(8)

        # Cabeçalho do gráfico
        hl_g = QHBoxLayout()
        lbl_g = QLabel("Gasto Mensal")
        lbl_g.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{GRAY}; background:transparent;")
        self._lbl_ano_graf = QLabel("")
        self._lbl_ano_graf.setStyleSheet(
            f"font-size:11px; color:{TXT_S}; background:transparent;")
        hl_g.addWidget(lbl_g); hl_g.addWidget(self._lbl_ano_graf); hl_g.addStretch()
        vl.addLayout(hl_g)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:#F0E8E8;"); sep.setFixedHeight(1)
        vl.addWidget(sep)

        if HAS_MPL:
            self._fig = Figure(figsize=(5, 3.2), dpi=96, facecolor=WHITE)
            self._ax  = self._fig.add_subplot(111)
            self._canvas = FigureCanvas(self._fig)
            self._canvas.setStyleSheet("background:transparent;")
            vl.addWidget(self._canvas, 1)
        else:
            lbl_no = QLabel("📦  Instale matplotlib:\npip install matplotlib")
            lbl_no.setAlignment(Qt.AlignCenter)
            lbl_no.setStyleSheet(f"color:{TXT_S}; font-size:12px; background:transparent;")
            vl.addWidget(lbl_no, 1)

        # Mini legenda de empresa
        self._lbl_legenda = QLabel("")
        self._lbl_legenda.setStyleSheet(
            f"font-size:10px; color:{TXT_S}; background:transparent;")
        self._lbl_legenda.setWordWrap(True)
        vl.addWidget(self._lbl_legenda)
        return frame

    # ── Tabela ────────────────────────────────────────────────────────────────

    def _build_tabela(self) -> QFrame:
        frame = card_container()
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(16); sombra.setOffset(0,2); sombra.setColor(QColor(0,0,0,18))
        frame.setGraphicsEffect(sombra)
        vl = QVBoxLayout(frame); vl.setContentsMargins(0, 0, 0, 0); vl.setSpacing(0)

        # Cabeçalho da tabela
        hl_t = QHBoxLayout(); hl_t.setContentsMargins(16,14,16,8)
        lbl_t = QLabel("Pedidos")
        lbl_t.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{GRAY}; background:transparent;")
        self._lbl_count = QLabel("")
        self._lbl_count.setStyleSheet(
            f"font-size:11px; color:{TXT_S}; background:transparent;")
        hl_t.addWidget(lbl_t); hl_t.addWidget(self._lbl_count); hl_t.addStretch()
        vl.addLayout(hl_t)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:#F0E8E8;"); sep.setFixedHeight(1)
        vl.addWidget(sep)

        self._tabela = QTableWidget(0, 6)
        self._tabela.setHorizontalHeaderLabels(
            ["Nº", "Data", "Obra", "Fornecedor", "Empresa", "Valor"])
        self._tabela.setStyleSheet(CSS_TABLE + """
            QScrollBar:horizontal {
                background:transparent; height:6px; border-radius:3px; margin:0;
            }
            QScrollBar::handle:horizontal {
                background:#D8CCCC; border-radius:3px; min-width:30px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width:0; }
        """)
        self._tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela.verticalHeader().setVisible(False)
        self._tabela.setShowGrid(False)
        self._tabela.setFrameShape(QFrame.NoFrame)
        hh = self._tabela.horizontalHeader(); hh.setHighlightSections(False)
        # Todas as colunas interativas — usuário pode arrastar para redimensionar
        for col in range(6):
            hh.setSectionResizeMode(col, QHeaderView.Interactive)
        self._tabela.setColumnWidth(0, 75)   # Nº
        self._tabela.setColumnWidth(1, 90)   # Data
        self._tabela.setColumnWidth(2, 200)  # Obra
        self._tabela.setColumnWidth(3, 190)  # Fornecedor
        self._tabela.setColumnWidth(4, 110)  # Empresa
        self._tabela.setColumnWidth(5, 110)  # Valor
        hh.setMinimumSectionSize(60)
        hh.setStretchLastSection(False)
        self._tabela.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._tabela.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        vl.addWidget(self._tabela, 1)
        return frame

    # ══════════════════════════════════════════════════════════════════════════
    # DADOS
    # ══════════════════════════════════════════════════════════════════════════

    def _carregar(self):
                # Carrega todos os pedidos do banco.
        self._todos = []
        try:
            from app.data.database import get_connection
            with get_connection() as conn:
                rows = conn.execute("""
                    SELECT numero, data_pedido, obra_nome, fornecedor_nome,
                           empresa_faturadora, valor_total
                    FROM pedidos
                    ORDER BY CAST(numero AS INTEGER) DESC
                """).fetchall()
                for row in rows:
                    self._todos.append(dict(row))
        except Exception as e:
            print(f"[HistoricoWidget] {e}")

        self._atualizar_combos()
        self._aplicar_filtros()

    def _atualizar_combos(self):
                # Preenche os combos de Ano e Obra com os dados reais do banco.
        anos = sorted({
            self._extrair_ano(p["data_pedido"])
            for p in self._todos
            if self._extrair_ano(p["data_pedido"]) is not None
        }, reverse=True)

        obras = sorted({
            str(p["obra_nome"] or "").strip()
            for p in self._todos
            if p["obra_nome"]
        })

        # Ano
        self._cb_ano.blockSignals(True)
        ano_sel = self._cb_ano.currentText()
        self._cb_ano.clear()
        self._cb_ano.addItem("Todos os anos")
        for a in anos:
            self._cb_ano.addItem(str(a))
        # Seleciona o ano atual por padrão
        idx = self._cb_ano.findText(str(datetime.now().year))
        self._cb_ano.setCurrentIndex(idx if idx >= 0 else 0)
        self._cb_ano.blockSignals(False)

        # Obra
        self._cb_obra.blockSignals(True)
        obra_sel = self._cb_obra.currentText()
        self._cb_obra.clear()
        self._cb_obra.addItem("Todas")
        for o in obras:
            self._cb_obra.addItem(o)
        idx2 = self._cb_obra.findText(obra_sel)
        self._cb_obra.setCurrentIndex(idx2 if idx2 >= 0 else 0)
        self._cb_obra.blockSignals(False)

    # ══════════════════════════════════════════════════════════════════════════
    # FILTROS
    # ══════════════════════════════════════════════════════════════════════════

    def _aplicar_filtros(self):
        ano_str  = self._cb_ano.currentText()
        emp_str  = self._cb_emp.currentText()
        obra_str = self._cb_obra.currentText()
        termo    = self._e_busca.text().strip().lower()

        resultado = self._todos

        if ano_str and ano_str != "Todos os anos":
            try:
                ano = int(ano_str)
                resultado = [
                    p for p in resultado
                    if self._extrair_ano(p["data_pedido"]) == ano
                ]
            except ValueError:
                pass

        if emp_str and emp_str != "Todas":
            resultado = [
                p for p in resultado
                if (p.get("empresa_faturadora") or "").upper() == emp_str.upper()
            ]

        if obra_str and obra_str != "Todas":
            resultado = [
                p for p in resultado
                if (p.get("obra_nome") or "").strip() == obra_str
            ]

        if termo:
            resultado = [
                p for p in resultado
                if termo in str(p.get("fornecedor_nome") or "").lower()
                or termo in str(p.get("numero") or "").lower()
                or termo in str(p.get("obra_nome") or "").lower()
            ]

        self._filtrados = resultado
        self._atualizar_cards()
        self._atualizar_grafico()
        self._preencher_tabela()

    def _limpar_filtros(self):
        self._cb_ano.blockSignals(True)
        idx = self._cb_ano.findText(str(datetime.now().year))
        self._cb_ano.setCurrentIndex(idx if idx >= 0 else 0)
        self._cb_ano.blockSignals(False)

        self._cb_emp.setCurrentIndex(0)
        self._cb_obra.setCurrentIndex(0)
        self._e_busca.clear()
        self._aplicar_filtros()

    # ══════════════════════════════════════════════════════════════════════════
    # CARDS
    # ══════════════════════════════════════════════════════════════════════════

    def _atualizar_cards(self):
        pedidos = self._filtrados
        total_n = len(pedidos)
        total_v = sum(self._val(p) for p in pedidos)
        obras   = len({str(p.get("obra_nome") or "").strip()
                       for p in pedidos if p.get("obra_nome")})
        fornec  = len({str(p.get("fornecedor_nome") or "").strip()
                       for p in pedidos if p.get("fornecedor_nome")})
        ticket  = (total_v / total_n) if total_n > 0 else 0.0

        self._lv_pedidos.setText(str(total_n))
        self._lv_valor.setText(f"R$ {self._fmt(total_v)}")
        self._lv_obras.setText(str(obras))
        self._lv_fornec.setText(str(fornec))
        self._lv_ticket.setText(f"R$ {self._fmt(ticket)}")

    # ══════════════════════════════════════════════════════════════════════════
    # GRÁFICO
    # ══════════════════════════════════════════════════════════════════════════

    def _atualizar_grafico(self):
        if not HAS_MPL:
            return

        ano_str = self._cb_ano.currentText()
        emp_str = self._cb_emp.currentText()

        try:
            ano_ref = int(ano_str)
        except (ValueError, TypeError):
            ano_ref = None

        self._lbl_ano_graf.setText(ano_str if ano_str != "Todos os anos" else "")

        # Agrupa valor por mês
        gastos = defaultdict(float)
        for p in self._filtrados:
            mes = self._extrair_mes(p["data_pedido"])
            if mes:
                gastos[mes] += self._val(p)

        meses   = list(range(1, 13))
        valores = [gastos.get(m, 0.0) for m in meses]
        labels  = MESES_PT

        # Cor das barras — destaca mês atual se ano atual
        hoje = datetime.now()
        cores_barras = []
        for m in meses:
            if ano_ref == hoje.year and m == hoje.month:
                cores_barras.append("#C0392B")   # vermelho — mês atual
            elif gastos.get(m, 0) > 0:
                cores_barras.append("#2980B9")   # azul — com dados
            else:
                cores_barras.append("#E8DEDE")   # cinza — sem dados

        self._ax.clear()
        self._fig.patch.set_facecolor(WHITE)
        self._ax.set_facecolor("#FAFAFA")

        bars = self._ax.bar(labels, valores, color=cores_barras,
                            width=0.6, zorder=3, edgecolor="none")

        # Rótulos sobre as barras com valor
        max_val = max(valores) if any(v > 0 for v in valores) else 1
        for bar, val in zip(bars, valores):
            if val > 0:
                self._ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max_val * 0.02,
                    self._fmt_curto(val),
                    ha="center", va="bottom",
                    fontsize=7, color=GRAY, fontweight="bold"
                )

        # Estética
        self._ax.set_ylim(0, max_val * 1.18 if max_val > 0 else 1)
        self._ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: self._fmt_curto(x))
        )
        self._ax.tick_params(axis="x", labelsize=8, colors=TXT_S)
        self._ax.tick_params(axis="y", labelsize=7, colors=TXT_S)
        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.spines["left"].set_color("#E8DEDE")
        self._ax.spines["bottom"].set_color("#E8DEDE")
        self._ax.grid(axis="y", color="#F0E8E8", linewidth=0.8, zorder=0)
        self._fig.tight_layout(pad=1.2)
        self._canvas.draw()

        # Legenda textual
        total_ano = sum(valores)
        self._lbl_legenda.setText(
            f"Total no período: R$ {self._fmt(total_ano)}"
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TABELA
    # ══════════════════════════════════════════════════════════════════════════

    def _preencher_tabela(self):
        self._tabela.setRowCount(0)

        # Exibe no máximo 200 linhas para performance
        pedidos = self._filtrados[:200]

        for pedido in pedidos:
            r = self._tabela.rowCount()
            self._tabela.insertRow(r)
            self._tabela.setRowHeight(r, 44)
            bg = WHITE if r % 2 == 0 else "#FBF7F7"

            def _it(txt, align=Qt.AlignVCenter | Qt.AlignLeft,
                    bold=False, cor=None):
                it = QTableWidgetItem(str(txt))
                it.setTextAlignment(align)
                it.setBackground(QColor(bg))
                if bold:
                    f = QFont(); f.setBold(True); it.setFont(f)
                if cor:
                    it.setForeground(QColor(cor))
                return it

            num  = str(pedido.get("numero") or "—")
            data = str(pedido.get("data_pedido") or "—")
            obra = str(pedido.get("obra_nome") or "—")
            forn = str(pedido.get("fornecedor_nome") or "—")
            emp  = (pedido.get("empresa_faturadora") or "—").upper()
            val  = self._val(pedido)
            cor_emp = CORES_EMPRESA.get(emp, TXT_S)

            self._tabela.setItem(r, 0, _it(
                f"#{num}", Qt.AlignVCenter | Qt.AlignCenter, bold=True, cor=RED))
            self._tabela.setItem(r, 1, _it(
                data, Qt.AlignVCenter | Qt.AlignCenter, cor=TXT_S))
            self._tabela.setItem(r, 2, _it(obra, bold=True))
            self._tabela.setItem(r, 3, _it(forn, cor=TXT_S))
            self._tabela.setItem(r, 4, _it(
                emp, Qt.AlignVCenter | Qt.AlignCenter, bold=True, cor=cor_emp))
            self._tabela.setItem(r, 5, _it(
                f"R$ {self._fmt(val)}",
                Qt.AlignVCenter | Qt.AlignRight, bold=True, cor=GRAY))

        total = len(self._filtrados)
        exib  = min(total, 200)
        sufixo = f" (exibindo {exib})" if total > 200 else ""
        self._lbl_count.setText(f"{total} pedido{'s' if total != 1 else ''}{sufixo}")

        if total == 0:
            self._tabela.setRowCount(1)
            self._tabela.setSpan(0, 0, 1, 6)
            it = QTableWidgetItem("Nenhum pedido encontrado para os filtros selecionados.")
            it.setTextAlignment(Qt.AlignCenter)
            it.setForeground(QColor(TXT_S))
            self._tabela.setItem(0, 0, it)

    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _vsep():
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("background:#E8DEDE; border:none;")
        sep.setFixedWidth(1)
        sep.setFixedHeight(36)
        return sep

    @staticmethod
    def _extrair_ano(data_str) -> int | None:
        if not data_str:
            return None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(str(data_str).strip(), fmt).year
            except ValueError:
                pass
        # Tenta extrair os 4 dígitos do ano
        s = str(data_str).strip()
        for part in s.replace("/", "-").split("-"):
            if len(part) == 4 and part.isdigit():
                return int(part)
        return None

    @staticmethod
    def _extrair_mes(data_str) -> int | None:
        if not data_str:
            return None
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(str(data_str).strip(), fmt).month
            except ValueError:
                pass
        return None

    @staticmethod
    def _val(p) -> float:
        try:
            return float(p.get("valor_total") or 0)
        except Exception:
            return 0.0

    @staticmethod
    def _fmt(v) -> str:
        try:
            return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "0,00"

    @staticmethod
    def _fmt_curto(v) -> str:
                # Formata valores grandes de forma compacta: 1.2k, 45k, 1.2M
        try:
            v = float(v)
            if v >= 1_000_000:
                return f"{v/1_000_000:.1f}M"
            if v >= 1_000:
                return f"{v/1_000:.0f}k"
            return f"{v:.0f}"
        except Exception:
            return "0"

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._carregar)
