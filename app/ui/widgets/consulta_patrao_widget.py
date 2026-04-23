# app/ui/widgets/consulta_patrao_widget.py
# Painel de consulta gerencial - versão executiva
# Lê somente o banco consolidado da rede: cotacao_rede.db

import os
import sqlite3
from datetime import datetime
from collections import defaultdict

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QPixmap, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QComboBox, QPushButton, QMessageBox,
    QGridLayout, QAbstractItemView, QGraphicsDropShadowEffect,
    QCompleter, QSplitter, QProgressBar
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QComboBox, QPushButton, QMessageBox,
    QGridLayout, QAbstractItemView, QGraphicsDropShadowEffect,
    QCompleter, QSplitter, QProgressBar, QScrollArea
)

REDE_DB = r"Z:\0 OBRAS\brasul_pedidos\cotacao_rede.db"

ASSETS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets")
)
LOGOS_DIR = os.path.join(ASSETS_DIR, "logos")

LOGO_PATHS = [
    os.path.join(LOGOS_DIR, "logo_brasul.png"),
    os.path.join(LOGOS_DIR, "brasul.png"),
    os.path.join(ASSETS_DIR, "logo_brasul.png"),
]

MESES_PT = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
            "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


class ConsultaPatraoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._dados = []
        self._filtrados = []
        self._build()
        self.recarregar()

    def _build(self):
        self.setStyleSheet("""
            QWidget {
                background: #f3f5f8;
                color: #1f2937;
                font-size: 12px;
                font-family: Segoe UI;
            }
            QFrame#headerCard {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffffff,
                    stop:1 #fff7f5
                );
                border: 1px solid #eadfdd;
                border-radius: 22px;
            }
            QFrame#sectionCard {
                background: #ffffff;
                border: 1px solid #e7eaee;
                border-radius: 18px;
            }
            QFrame#summaryCard, QFrame#miniPanel {
                background: #ffffff;
                border: 1px solid #e7eaee;
                border-radius: 16px;
            }
            QLabel#pageTitle {
                font-size: 30px;
                font-weight: 800;
                color: #192434;
            }
            QLabel#pageSubtitle {
                font-size: 12px;
                color: #6b7280;
            }
            QLabel#badgeOnlyRead {
                background: #fdecea;
                color: #c0392b;
                border-radius: 10px;
                padding: 7px 12px;
                font-size: 11px;
                font-weight: 800;
            }
            QLabel#sectionTitle, QLabel#miniTitle {
                font-size: 13px;
                font-weight: 800;
                color: #374151;
            }
            QLabel#fieldLabel {
                font-size: 11px;
                font-weight: 700;
                color: #6b7280;
            }
            QLabel#summaryTitle {
                font-size: 11px;
                color: #6b7280;
                font-weight: 700;
            }
            QLabel#summaryValue {
                font-size: 26px;
                font-weight: 800;
                color: #111827;
            }
            QLabel#summaryHint {
                font-size: 11px;
                color: #c0392b;
                font-weight: 700;
            }
            QLabel#miniMuted {
                font-size: 11px;
                color: #6b7280;
            }
            QLineEdit, QComboBox {
                background: #ffffff;
                border: 1px solid #d7dde5;
                border-radius: 10px;
                padding: 8px 10px;
                min-height: 38px;
                color: #1f2937;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1.5px solid #c0392b;
                background: #fffefe;
            }
            QComboBox::drop-down {
                border: none;
                width: 26px;
                background: transparent;
            }
            QComboBox QAbstractItemView {
                background: #ffffff;
                border: 1px solid #d7dde5;
                border-radius: 8px;
                selection-background-color: #fdecea;
                selection-color: #1f2937;
                outline: none;
                padding: 4px;
            }
            QPushButton {
                background: #c0392b;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 14px;
                min-height: 38px;
                font-weight: 800;
            }
            QPushButton:hover {
                background: #a93226;
            }
            QPushButton#secondaryButton {
                background: #ffffff;
                color: #1f2937;
                border: 1px solid #d7dde5;
            }
            QPushButton#secondaryButton:hover {
                background: #f3f4f6;
            }
            QPushButton#pdfButton {
                background: #ffffff;
                color: #1f2937;
                border: 1px solid #d7dde5;
                border-radius: 8px;
                padding: 4px 10px;
                min-height: 30px;
                font-weight: 700;
            }
            QPushButton#pdfButton:hover {
                background: #fff5f4;
                border: 1px solid #c0392b;
                color: #c0392b;
            }
            QPushButton#pdfButtonDisabled {
                background: #eef2f6;
                color: #8a96a3;
                border: 1px solid #d7dde5;
                border-radius: 8px;
                padding: 4px 10px;
                min-height: 30px;
                font-weight: 700;
            }
            QTableWidget {
                background: #ffffff;
                border: 1px solid #e7eaee;
                border-radius: 14px;
                gridline-color: #edf1f4;
                alternate-background-color: #fafbfc;
                selection-background-color: #fdecea;
                selection-color: #1f2937;
            }
            QHeaderView::section {
                background: #1f2f46;
                color: #ffffff;
                border: none;
                padding: 11px 8px;
                font-size: 11px;
                font-weight: 800;
            }
            QProgressBar {
                background: #eef2f6;
                border: 1px solid #d7dde5;
                border-radius: 7px;
                text-align: center;
                min-height: 18px;
                color: #1f2937;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background: #c0392b;
                border-radius: 6px;
            }
            QScrollBar:vertical {
                background: #eef2f6;
                width: 14px;
                margin: 3px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: #9fb0c2;
                border: 1px solid #8899ab;
                border-radius: 7px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8599ad;
            }
            QScrollBar:horizontal {
                background: #eef2f6;
                height: 14px;
                margin: 3px;
                border-radius: 7px;
            }
            QScrollBar::handle:horizontal {
                background: #9fb0c2;
                border: 1px solid #8899ab;
                border-radius: 7px;
                min-width: 40px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #8599ad;
            }
            QScrollBar::add-line, QScrollBar::sub-line,
            QScrollBar::up-arrow, QScrollBar::down-arrow,
            QScrollBar::left-arrow, QScrollBar::right-arrow {
                width: 0px;
                height: 0px;
                background: transparent;
                border: none;
            }
            QSplitter::handle {
                background: #e6ebf0;
                width: 8px;
                border-radius: 4px;
            }
            QSplitter::handle:hover {
                background: #cfd7e0;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        root.addWidget(self._build_header())
        root.addWidget(self._build_filters())
        root.addLayout(self._build_summary())
        root.addWidget(self._build_main_panel(), 1)

    def _build_header(self):
        card = QFrame()
        card.setObjectName("headerCard")
        self._apply_shadow(card)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        logo_wrap = QFrame()
        logo_wrap.setStyleSheet("QFrame { background: #ffffff; border: 1px solid #ececec; border-radius: 14px; }")
        logo_wrap.setFixedSize(120, 76)

        lw = QVBoxLayout(logo_wrap)
        lw.setContentsMargins(10, 10, 10, 10)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignCenter)

        pix = self._load_logo()
        if pix:
            logo_label.setPixmap(pix.scaled(96, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("BRASUL")
            logo_label.setStyleSheet("background: #c0392b; color: white; border-radius: 10px; font-size: 22px; font-weight: 800;")

        lw.addWidget(logo_label)
        layout.addWidget(logo_wrap)

        text_box = QVBoxLayout()
        text_box.setSpacing(4)

        lbl_title = QLabel("Brasul Consulta Gerencial")
        lbl_title.setObjectName("pageTitle")

        lbl_subtitle = QLabel("Painel executivo para acompanhamento de pedidos, obras, fornecedores e itens")
        lbl_subtitle.setObjectName("pageSubtitle")

        lbl_badge = QLabel("Somente leitura")
        lbl_badge.setObjectName("badgeOnlyRead")
        lbl_badge.setFixedWidth(140)
        lbl_badge.setAlignment(Qt.AlignCenter)

        text_box.addWidget(lbl_title)
        text_box.addWidget(lbl_subtitle)
        text_box.addWidget(lbl_badge)

        layout.addLayout(text_box)
        layout.addStretch()

        self.btn_recarregar = QPushButton("↻ Recarregar")
        self.btn_recarregar.clicked.connect(self.recarregar)
        layout.addWidget(self.btn_recarregar)

        return card

    def _build_filters(self):
        card = QFrame()
        card.setObjectName("sectionCard")
        self._apply_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        title = QLabel("Filtros de Consulta")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        self.cb_comprador = QComboBox()
        self.cb_comprador.addItems(["TODOS", "IURY", "THAMYRES", "SEM COMPRADOR"])

        self.cb_empresa = QComboBox()
        self.cb_empresa.addItems(["TODAS", "BRASUL", "JB", "B&B", "INTERIORANA", "INTERBRAS"])

        self.cb_obra = QComboBox()
        self.cb_obra.setEditable(True)
        self.cb_obra.setInsertPolicy(QComboBox.NoInsert)

        self.cb_fornecedor = QComboBox()
        self.cb_fornecedor.setEditable(True)
        self.cb_fornecedor.setInsertPolicy(QComboBox.NoInsert)

        for cb in (self.cb_obra, self.cb_fornecedor):
            comp = QCompleter()
            comp.setCaseSensitivity(Qt.CaseInsensitive)
            comp.setFilterMode(Qt.MatchContains)
            cb.setCompleter(comp)

        self.ed_item = QLineEdit()
        self.ed_item.setPlaceholderText("Descrição do item / material...")

        self.ed_numero = QLineEdit()
        self.ed_numero.setPlaceholderText("Número do pedido...")

        self.ed_data_ini = QLineEdit()
        self.ed_data_ini.setPlaceholderText("Data inicial (dd/mm/aaaa)")

        self.ed_data_fim = QLineEdit()
        self.ed_data_fim.setPlaceholderText("Data final (dd/mm/aaaa)")

        grid.addWidget(self._field("Comprador", self.cb_comprador), 0, 0)
        grid.addWidget(self._field("Empresa", self.cb_empresa), 0, 1)
        grid.addWidget(self._field("Obra", self.cb_obra), 0, 2)
        grid.addWidget(self._field("Fornecedor", self.cb_fornecedor), 0, 3)
        grid.addWidget(self._field("Pedido", self.ed_numero), 1, 0)
        grid.addWidget(self._field("Data Inicial", self.ed_data_ini), 1, 1)
        grid.addWidget(self._field("Data Final", self.ed_data_fim), 1, 2)
        grid.addWidget(self._field("Item / Material", self.ed_item), 1, 3)

        layout.addLayout(grid)

        btns = QHBoxLayout()
        btns.addStretch()

        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.clicked.connect(self.aplicar_filtros)

        btn_limpar = QPushButton("Limpar")
        btn_limpar.setObjectName("secondaryButton")
        btn_limpar.clicked.connect(self.limpar_filtros)

        btns.addWidget(btn_filtrar)
        btns.addWidget(btn_limpar)
        layout.addLayout(btns)
        return card

    def _build_summary(self):
        row = QHBoxLayout()
        row.setSpacing(12)
        self.card_total_pedidos = self._summary_card("Pedidos", "0", "Total encontrado")
        self.card_total_valor = self._summary_card("Valor Total", "R$ 0,00", "Valor consolidado")
        self.card_total_obras = self._summary_card("Obras", "0", "Obras distintas")
        self.card_total_forn = self._summary_card("Fornecedores", "0", "Fornecedores distintos")
        row.addWidget(self.card_total_pedidos)
        row.addWidget(self.card_total_valor)
        row.addWidget(self.card_total_obras)
        row.addWidget(self.card_total_forn)
        return row

    def _build_main_panel(self):
        card = QFrame()
        card.setObjectName("sectionCard")
        self._apply_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("Pedidos Consolidados")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)
        splitter.setOpaqueResize(True)

        table_panel = self._build_table_panel()
        side_panel = self._build_side_panel()

        table_panel.setMinimumWidth(900)
        side_panel.setMinimumWidth(360)
        side_panel.setMaximumWidth(460)

        splitter.addWidget(table_panel)
        splitter.addWidget(side_panel)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([1200, 380])

        layout.addWidget(splitter, 1)
        return card

    def _build_table_panel(self):
        panel = QFrame()
        panel.setObjectName("miniPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tbl = QTableWidget(0, 10)
        self.tbl.setHorizontalHeaderLabels([
            "Pedido", "Comprador", "Data", "Empresa", "Fornecedor",
            "Obra", "Cond. Pgto", "Forma", "Valor Total", "PDF"
        ])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(True)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tbl.horizontalHeader().setStretchLastSection(False)
        self.tbl.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tbl.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.tbl.setWordWrap(False)
        self.tbl.setColumnWidth(0, 80)
        self.tbl.setColumnWidth(1, 100)
        self.tbl.setColumnWidth(2, 90)
        self.tbl.setColumnWidth(3, 90)
        self.tbl.setColumnWidth(4, 180)
        self.tbl.setColumnWidth(5, 300)
        self.tbl.setColumnWidth(6, 90)
        self.tbl.setColumnWidth(7, 90)
        self.tbl.setColumnWidth(8, 120)
        self.tbl.setColumnWidth(9, 95)
        layout.addWidget(self.tbl)
        return panel

    def _build_side_panel(self):
        outer = QFrame()
        outer.setObjectName("miniPanel")

        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self.box_top_obras = self._mini_panel("Top 5 Obras por Valor")
        self.top_obras_layout = self.box_top_obras.layout()

        self.box_empresas = self._mini_panel("Gastos por Empresa")
        self.empresas_layout = self.box_empresas.layout()

        self.box_mensal = self._mini_panel("Evolução Mensal de Pedidos")
        self.mensal_layout = self.box_mensal.layout()

        layout.addWidget(self.box_top_obras)
        layout.addWidget(self.box_empresas)
        layout.addWidget(self.box_mensal)
        layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        return outer

    def _mini_panel(self, title_text):
        card = QFrame()
        card.setObjectName("miniPanel")
        card.setMinimumHeight(190)
        v = QVBoxLayout(card)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)
        title = QLabel(title_text)
        title.setObjectName("miniTitle")
        v.addWidget(title)
        return card

    def _field(self, label_text, widget):
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)
        layout.addWidget(widget)
        return wrapper

    def _summary_card(self, title, value, hint):
        card = QFrame()
        card.setObjectName("summaryCard")
        card.setMinimumHeight(96)
        self._apply_shadow(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("summaryTitle")
        lbl_value = QLabel(value)
        lbl_value.setObjectName("summaryValue")
        lbl_hint = QLabel(hint)
        lbl_hint.setObjectName("summaryHint")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        layout.addWidget(lbl_hint)
        layout.addStretch()

        card._valor_label = lbl_value
        return card

    def _apply_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 18))
        widget.setGraphicsEffect(shadow)

    def _load_logo(self):
        for path in LOGO_PATHS:
            if os.path.exists(path):
                return QPixmap(path)
        return None

    def recarregar(self):
        try:
            self._dados = self._ler_banco()
            self._filtrados = list(self._dados)
            self._popular_filtros_combo()
            self._preencher_tabela()
            self._atualizar_cards()
            self._atualizar_painel_lateral()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao recarregar dados.\n\n{e}")

    def _ler_banco(self):
        resultados = []
        if not os.path.exists(REDE_DB):
            QMessageBox.critical(self, "Erro", f"Banco não encontrado:\n\n{REDE_DB}")
            return resultados

        conn = sqlite3.connect(REDE_DB)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute("""
                SELECT
                    p.numero,
                    p.data_pedido,
                    p.obra_nome,
                    p.fornecedor_nome,
                    p.empresa_faturadora,
                    p.condicao_pagamento,
                    p.forma_pagamento,
                    p.valor_total,
                    p.caminho_pdf,
                    p.comprador,
                    COALESCE(GROUP_CONCAT(i.descricao, ' | '), '') AS itens_texto
                FROM pedidos p
                LEFT JOIN itens_pedido i ON i.pedido_id = p.id
                GROUP BY
                    p.id, p.numero, p.data_pedido, p.obra_nome, p.fornecedor_nome,
                    p.empresa_faturadora, p.condicao_pagamento, p.forma_pagamento,
                    p.valor_total, p.caminho_pdf, p.comprador
                ORDER BY p.emitido_em DESC, p.id DESC
            """).fetchall()

            for row in rows:
                item = dict(row)
                item["origem"] = (item.get("comprador") or "").strip().upper()
                item["pdf_rede"] = item.get("caminho_pdf") or ""
                resultados.append(item)
        finally:
            conn.close()

        resultados.sort(key=self._chave_ordenacao, reverse=True)
        return resultados

    def _chave_ordenacao(self, item):
        texto = item.get("data_pedido") or ""
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(texto, fmt)
            except Exception:
                pass
        return datetime.min

    def _popular_filtros_combo(self):
        obras = sorted({(i.get("obra_nome") or "").strip() for i in self._dados if (i.get("obra_nome") or "").strip()})
        fornecedores = sorted({(i.get("fornecedor_nome") or "").strip() for i in self._dados if (i.get("fornecedor_nome") or "").strip()})

        self.cb_obra.blockSignals(True)
        self.cb_fornecedor.blockSignals(True)

        self.cb_obra.clear()
        self.cb_fornecedor.clear()
        self.cb_obra.addItem("TODAS")
        self.cb_fornecedor.addItem("TODOS")
        self.cb_obra.addItems(obras)
        self.cb_fornecedor.addItems(fornecedores)

        if self.cb_obra.completer():
            self.cb_obra.completer().setModel(self.cb_obra.model())
        if self.cb_fornecedor.completer():
            self.cb_fornecedor.completer().setModel(self.cb_fornecedor.model())

        self.cb_obra.blockSignals(False)
        self.cb_fornecedor.blockSignals(False)
        self.cb_obra.setCurrentIndex(0)
        self.cb_fornecedor.setCurrentIndex(0)

    def aplicar_filtros(self):
        comprador = self.cb_comprador.currentText().strip().upper()
        empresa = self.cb_empresa.currentText().strip().upper()
        obra = self.cb_obra.currentText().strip().upper()
        fornecedor = self.cb_fornecedor.currentText().strip().upper()
        numero = self.ed_numero.text().strip().upper()
        item_busca = self.ed_item.text().strip().upper()
        data_ini = self.ed_data_ini.text().strip()
        data_fim = self.ed_data_fim.text().strip()

        dados = []
        for item in self._dados:
            comp_item = (item.get("comprador") or item.get("origem") or "").strip().upper() or "SEM COMPRADOR"

            if comprador != "TODOS" and comp_item != comprador:
                continue
            if empresa != "TODAS" and (item.get("empresa_faturadora") or "").upper() != empresa:
                continue
            if obra and obra != "TODAS" and obra not in (item.get("obra_nome") or "").upper():
                continue
            if fornecedor and fornecedor != "TODOS" and fornecedor not in (item.get("fornecedor_nome") or "").upper():
                continue
            if numero and numero not in str(item.get("numero") or "").upper():
                continue
            if item_busca and item_busca not in (item.get("itens_texto") or "").upper():
                continue
            if not self._data_no_intervalo(item.get("data_pedido", ""), data_ini, data_fim):
                continue
            dados.append(item)

        self._filtrados = dados
        self._preencher_tabela()
        self._atualizar_cards()
        self._atualizar_painel_lateral()

    def limpar_filtros(self):
        self.cb_comprador.setCurrentIndex(0)
        self.cb_empresa.setCurrentIndex(0)
        self.cb_obra.setCurrentIndex(0)
        self.cb_fornecedor.setCurrentIndex(0)
        self.cb_obra.setEditText("TODAS")
        self.cb_fornecedor.setEditText("TODOS")
        self.ed_numero.clear()
        self.ed_item.clear()
        self.ed_data_ini.clear()
        self.ed_data_fim.clear()
        self._filtrados = list(self._dados)
        self._preencher_tabela()
        self._atualizar_cards()
        self._atualizar_painel_lateral()

    def _data_no_intervalo(self, data_texto, data_ini, data_fim):
        if not data_texto:
            return True
        data_base = None
        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                data_base = datetime.strptime(data_texto, fmt)
                break
            except Exception:
                pass
        if data_base is None:
            return True
        if data_ini:
            try:
                d_ini = datetime.strptime(data_ini, "%d/%m/%Y")
                if data_base < d_ini:
                    return False
            except Exception:
                pass
        if data_fim:
            try:
                d_fim = datetime.strptime(data_fim, "%d/%m/%Y")
                if data_base > d_fim:
                    return False
            except Exception:
                pass
        return True

    def _preencher_tabela(self):
        self.tbl.setRowCount(0)
        for row_idx, item in enumerate(self._filtrados):
            self.tbl.insertRow(row_idx)
            self.tbl.setRowHeight(row_idx, 42)

            comprador = str(item.get("comprador") or item.get("origem") or "").strip() or "SEM COMPRADOR"

            self._set_item(row_idx, 0, str(item.get("numero") or ""))
            self._set_item(row_idx, 1, comprador)
            self._set_item(row_idx, 2, str(item.get("data_pedido") or ""))
            self._set_item(row_idx, 3, str(item.get("empresa_faturadora") or ""))
            self._set_item(row_idx, 4, str(item.get("fornecedor_nome") or ""))
            self._set_item(row_idx, 5, str(item.get("obra_nome") or ""))
            self._set_item(row_idx, 6, str(item.get("condicao_pagamento") or ""))
            self._set_item(row_idx, 7, str(item.get("forma_pagamento") or ""))
            self._set_item(row_idx, 8, self._fmt_moeda(item.get("valor_total")))

            path = item.get("pdf_rede", "") or ""
            if path and os.path.exists(path):
                btn_pdf = QPushButton("Abrir")
                btn_pdf.setObjectName("pdfButton")
                btn_pdf.clicked.connect(lambda _, p=path: self._abrir_pdf(p))
            else:
                btn_pdf = QPushButton("Sem PDF")
                btn_pdf.setObjectName("pdfButtonDisabled")
                btn_pdf.setEnabled(False)

            self.tbl.setCellWidget(row_idx, 9, btn_pdf)

    def _set_item(self, row, col, texto):
        it = QTableWidgetItem(texto)
        if col in (0, 1, 2, 3, 6, 7, 8):
            it.setTextAlignment(Qt.AlignCenter)
        if col == 8:
            it.setForeground(QColor("#0b6e3d"))
            f = QFont()
            f.setBold(True)
            it.setFont(f)
        self.tbl.setItem(row, col, it)

    def _atualizar_cards(self):
        total_pedidos = len(self._filtrados)
        total_valor = sum(float(i.get("valor_total") or 0) for i in self._filtrados)
        total_obras = len(set((i.get("obra_nome") or "").strip() for i in self._filtrados if (i.get("obra_nome") or "").strip()))
        total_forn = len(set((i.get("fornecedor_nome") or "").strip() for i in self._filtrados if (i.get("fornecedor_nome") or "").strip()))
        self.card_total_pedidos._valor_label.setText(str(total_pedidos))
        self.card_total_valor._valor_label.setText(self._fmt_moeda(total_valor))
        self.card_total_obras._valor_label.setText(str(total_obras))
        self.card_total_forn._valor_label.setText(str(total_forn))

    def _atualizar_painel_lateral(self):
        self._clear_layout_keep_title(self.top_obras_layout)
        self._clear_layout_keep_title(self.empresas_layout)
        self._clear_layout_keep_title(self.mensal_layout)

        obras = defaultdict(float)
        for item in self._filtrados:
            obra = (item.get("obra_nome") or "SEM OBRA").strip() or "SEM OBRA"
            obras[obra] += float(item.get("valor_total") or 0)

        top_obras = sorted(obras.items(), key=lambda x: x[1], reverse=True)[:5]
        max_obra = max([v for _, v in top_obras], default=0)
        if not top_obras:
            self.top_obras_layout.addWidget(self._label_muted("Sem dados para exibir."))
        else:
            for nome, valor in top_obras:
                self.top_obras_layout.addWidget(self._bar_row(nome, valor, max_obra, moeda=True))

        empresas = defaultdict(float)
        for item in self._filtrados:
            emp = (item.get("empresa_faturadora") or "SEM EMPRESA").strip() or "SEM EMPRESA"
            empresas[emp] += float(item.get("valor_total") or 0)

        emp_sorted = sorted(empresas.items(), key=lambda x: x[1], reverse=True)
        max_emp = max([v for _, v in emp_sorted], default=0)
        if not emp_sorted:
            self.empresas_layout.addWidget(self._label_muted("Sem dados para exibir."))
        else:
            for nome, valor in emp_sorted:
                self.empresas_layout.addWidget(self._bar_row(nome, valor, max_emp, moeda=True))

        mensal = {m: 0 for m in range(1, 13)}
        for item in self._filtrados:
            texto = item.get("data_pedido") or ""
            dt = None
            for fmt in ("%d/%m/%Y", "%d/%m/%y"):
                try:
                    dt = datetime.strptime(texto, fmt)
                    break
                except Exception:
                    pass
            if dt:
                mensal[dt.month] += 1

        max_mes = max(mensal.values()) if mensal else 0
        if max_mes == 0:
            self.mensal_layout.addWidget(self._label_muted("Sem dados para exibir."))
        else:
            for mes in range(1, 13):
                self.mensal_layout.addWidget(self._bar_row(MESES_PT[mes - 1], mensal[mes], max_mes, moeda=False, inteiro=True))

    def _bar_row(self, nome, valor, maximo, moeda=False, inteiro=False):
        w = QWidget()
        h = QVBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)

        topo = QHBoxLayout()
        topo.setContentsMargins(0, 0, 0, 0)

        lbl_nome = QLabel(nome)
        lbl_nome.setObjectName("miniMuted")
        lbl_nome.setWordWrap(True)

        lbl_valor = QLabel(self._fmt_moeda(valor) if moeda else (str(int(valor)) if inteiro else str(valor)))
        lbl_valor.setStyleSheet("font-size:11px; font-weight:700; color:#1f2937;")

        topo.addWidget(lbl_nome, 1)
        topo.addWidget(lbl_valor)

        bar = QProgressBar()
        bar.setRange(0, 100)
        pct = int((valor / maximo) * 100) if maximo > 0 else 0
        bar.setValue(pct)
        bar.setTextVisible(False)

        h.addLayout(topo)
        h.addWidget(bar)
        return w

    def _label_muted(self, texto):
        lbl = QLabel(texto)
        lbl.setObjectName("miniMuted")
        return lbl

    def _clear_layout_keep_title(self, layout):
        while layout.count() > 1:
            item = layout.takeAt(1)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_nested(item.layout())

    def _clear_nested(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_nested(item.layout())

    def _abrir_pdf(self, caminho_pdf):
        if not caminho_pdf:
            QMessageBox.warning(self, "PDF não encontrado", "Não foi possível localizar o PDF informado no banco.")
            return
        if not os.path.exists(caminho_pdf):
            QMessageBox.warning(self, "PDF não encontrado", f"Arquivo não localizado:\n\n{caminho_pdf}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(caminho_pdf))

    def _fmt_moeda(self, valor):
        try:
            return f"R$ {float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "R$ 0,00"
