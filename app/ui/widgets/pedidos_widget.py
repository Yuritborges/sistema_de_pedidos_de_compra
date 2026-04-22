# app/ui/widgets/pedidos_widget.py
# Aba de pedidos gerados com filtros e impressão.
import os, sys, subprocess, shutil, tempfile
from datetime import datetime, date, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QLineEdit, QFrame, QGraphicsDropShadowEffect,
    QDialog, QDialogButtonBox, QDateEdit, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QFont

# ── Estilo centralizado ───────────────────────────────────────────────────────
from app.ui.style import (
    RED, GRAY, WHITE, BG, BDR, TXT, TXT_S, SEL, HOV, GREEN, BLUE,
    CSS_BUSCA, CSS_TABLE, CORES_EMPRESA,
    btn_solid, btn_outline, btn_filtro, make_card, card_container,
)

try:
    from config import PEDIDOS_DIR
except ImportError:
    PEDIDOS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'pedidos_gerados')


class PedidosWidget(QWidget):

    def __init__(self):
        super().__init__()
        self._todos         = []
        self._filtro_ativo  = None
        self._data_inicio   = None
        self._data_fim      = None
        self._build()
        self._set_filtro_data("todos")  # inicia com Todos marcado
        self._carregar()

    # ══════════════════════════════════════════════════════════════════════════
    # CONSTRUÇÃO DA INTERFACE
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        self.setStyleSheet(f"background:{BG};")
        vl = QVBoxLayout(self)
        vl.setContentsMargins(24, 20, 24, 20)
        vl.setSpacing(16)

        # ── Cabeçalho ─────────────────────────────────────────────────────────────
        hl_topo = QHBoxLayout()
        hl_topo.setSpacing(14)

        # Logo Brasul
        _HERE_W = os.path.dirname(os.path.abspath(__file__))
        _LOGO_PATH = os.path.normpath(
            os.path.join(_HERE_W, '..', '..', '..', 'assets', 'logos', 'logo_brasul.png')
        )
        from PySide6.QtGui import QPixmap
        lbl_logo = QLabel()
        lbl_logo.setFixedHeight(48)
        lbl_logo.setStyleSheet("background:transparent;")
        if os.path.exists(_LOGO_PATH):
            pix = QPixmap(_LOGO_PATH).scaled(120, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
        else:
            lbl_logo.setText("BRASUL")
            lbl_logo.setStyleSheet(f"font-size:15px; font-weight:bold; color:{RED}; background:transparent;")
        hl_topo.addWidget(lbl_logo)

        sep_logo = QFrame()
        sep_logo.setFrameShape(QFrame.VLine)
        sep_logo.setStyleSheet(f"background:{BDR}; margin:6px 0;")
        sep_logo.setFixedWidth(1)
        hl_topo.addWidget(sep_logo)

        tv = QVBoxLayout(); tv.setSpacing(2)
        titulo = QLabel("Pedidos Gerados")
        titulo.setStyleSheet(f"font-size:20px; font-weight:bold; color:{GRAY}; background:transparent;")
        sub = QLabel("Histórico de PDFs gerados pelo sistema")
        sub.setStyleSheet(f"font-size:11px; color:{TXT_S}; background:transparent;")
        tv.addWidget(titulo); tv.addWidget(sub)
        hl_topo.addLayout(tv)
        hl_topo.addStretch()

        # ── Botões de impressão (DESTAQUE) ────────────────────────────────────
        btn_impr_hoje = btn_solid("🖨  Imprimir Hoje", RED)
        btn_impr_hoje.setToolTip("Gera e abre para impressão a Relação de Pedidos de hoje")
        btn_impr_hoje.clicked.connect(self._imprimir_hoje)
        hl_topo.addWidget(btn_impr_hoje)

        btn_impr_data = btn_solid("📅  Imprimir por Data", "#8E44AD")
        btn_impr_data.setToolTip("Escolhe uma data e imprime a Relação de Pedidos")
        btn_impr_data.clicked.connect(self._imprimir_por_data)
        hl_topo.addWidget(btn_impr_data)

        # Separador visual
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"background:{BDR}; margin:4px 4px;")
        sep.setFixedWidth(1)
        hl_topo.addWidget(sep)

        btn_pasta = btn_outline("📂  Abrir Pasta")
        btn_pasta.setToolTip("Abre a pasta pedidos_gerados/ no Explorer")
        btn_pasta.clicked.connect(self._abrir_pasta_gerados)
        hl_topo.addWidget(btn_pasta)

        btn_att = btn_solid("↻  Atualizar", "#95A5A6")
        btn_att.clicked.connect(self._carregar)
        hl_topo.addWidget(btn_att)
        vl.addLayout(hl_topo)

        # ── Cards resumo ───────────────────────────────────────────────────────
        cards_row = QHBoxLayout(); cards_row.setSpacing(14)
        self._card_total, self._lv_total = make_card("TOTAL DE PEDIDOS", "—", RED)
        self._card_hoje,  self._lv_hoje  = make_card("GERADOS HOJE",     "—", BLUE)
        self._card_valor, self._lv_valor = make_card("VALOR HOJE",       "—", GREEN)
        cards_row.addWidget(self._card_total)
        cards_row.addWidget(self._card_hoje)
        cards_row.addWidget(self._card_valor)
        cards_row.addStretch()
        vl.addLayout(cards_row)

        # ── Barra busca + filtros ──────────────────────────────────────────────
        hl_busca = QHBoxLayout(); hl_busca.setSpacing(10)

        busca_wrap = QWidget()
        busca_wrap.setFixedHeight(36)
        busca_wrap.setMaximumWidth(380)
        bwl = QHBoxLayout(busca_wrap)
        bwl.setContentsMargins(0, 0, 0, 0)
        bwl.setSpacing(0)
        self.e_busca = QLineEdit()
        self.e_busca.setPlaceholderText("Buscar por nº, obra ou fornecedor...")
        self.e_busca.setStyleSheet(CSS_BUSCA)
        self.e_busca.textChanged.connect(self._aplicar_filtros)
        bwl.addWidget(self.e_busca)
        ico = QLabel("🔍")
        ico.setStyleSheet("background:transparent; font-size:13px; border:none;")
        ico.setFixedWidth(28); ico.setParent(busca_wrap); ico.move(8, 9); ico.raise_()
        hl_busca.addWidget(busca_wrap)

        # Botões de filtro rápido
        self._btn_filtros = {}
        for chave, rotulo in [("hoje","Hoje"), ("semana","Esta semana"),
                               ("mes","Este mês"), ("todos","Todos")]:
            b = btn_filtro(rotulo)
            b.clicked.connect(lambda _, k=chave: self._set_filtro_data(k))
            hl_busca.addWidget(b)
            self._btn_filtros[chave] = b

        btn_periodo = btn_outline("📅  Período")
        btn_periodo.clicked.connect(self._filtro_periodo_custom)
        hl_busca.addWidget(btn_periodo)

        hl_busca.addStretch()
        self._lbl_cont = QLabel("")
        self._lbl_cont.setStyleSheet(f"font-size:11px; color:{TXT_S}; background:transparent;")
        hl_busca.addWidget(self._lbl_cont)
        vl.addLayout(hl_busca)

        # Label de período ativo
        self._lbl_filtro_ativo = QLabel("")
        self._lbl_filtro_ativo.setVisible(False)
        self._lbl_filtro_ativo.setStyleSheet(
            f"font-size:11px; color:{RED}; padding:4px 12px; background:transparent;")
        vl.addWidget(self._lbl_filtro_ativo)

        # ── Tabela ─────────────────────────────────────────────────────────────
        container = card_container()
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(16); sombra.setOffset(0, 2); sombra.setColor(QColor(0,0,0,18))
        container.setGraphicsEffect(sombra)
        cvl = QVBoxLayout(container); cvl.setContentsMargins(0,0,0,0)

        self.tabela = QTableWidget(0, 6)
        self.tabela.setHorizontalHeaderLabels(["Nº", "Data", "Obra", "Fornecedor", "Empresa", "Ações"])
        self.tabela.setStyleSheet(CSS_TABLE)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setShowGrid(False)
        self.tabela.setFrameShape(QFrame.NoFrame)
        hh = self.tabela.horizontalHeader(); hh.setHighlightSections(False)
        hh.setSectionResizeMode(0, QHeaderView.Fixed);  self.tabela.setColumnWidth(0, 70)
        hh.setSectionResizeMode(1, QHeaderView.Fixed);  self.tabela.setColumnWidth(1, 95)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.Fixed);  self.tabela.setColumnWidth(4, 115)
        hh.setSectionResizeMode(5, QHeaderView.Fixed);  self.tabela.setColumnWidth(5, 195)
        cvl.addWidget(self.tabela)
        vl.addWidget(container, 1)

        rodape = QLabel(f"📌  {PEDIDOS_DIR}")
        rodape.setStyleSheet(f"font-size:10px; color:{TXT_S}; background:transparent;")
        rodape.setWordWrap(True)
        vl.addWidget(rodape)

    # ══════════════════════════════════════════════════════════════════════════
    # DADOS
    # ══════════════════════════════════════════════════════════════════════════

    def _carregar(self):
        self._todos = []
        os.makedirs(PEDIDOS_DIR, exist_ok=True)

        db_dados = {}
        try:
            from app.data.database import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT numero, fornecedor_nome, valor_total, obra_nome, "
                    "empresa_faturadora, condicao_pagamento, forma_pagamento "
                    "FROM pedidos"
                ).fetchall()
                for row in rows:
                    db_dados[str(row["numero"])] = {
                        "fornecedor":         row["fornecedor_nome"] or "—",
                        "valor":              row["valor_total"] or 0.0,
                        "obra_db":            row["obra_nome"] or "",
                        "empresa_faturadora": row["empresa_faturadora"] or "—",
                        "condicao_pagamento": row["condicao_pagamento"] or "—",
                        "forma_pagamento":    row["forma_pagamento"] or "—",
                    }
        except Exception as e:
            print(f"[PedidosWidget] Aviso ao consultar banco: {e}")

        for nome in sorted(
                os.listdir(PEDIDOS_DIR),
                key=lambda n: os.path.getmtime(os.path.join(PEDIDOS_DIR, n)),
                reverse=True
        ):
            if not nome.lower().endswith(".pdf"):
                continue
            caminho = os.path.join(PEDIDOS_DIR, nome)
            try:
                stat = os.stat(caminho)
                data_mod = datetime.fromtimestamp(stat.st_mtime)
            except OSError:
                continue
            empresa, numero, obra = self._parse_nome(nome)
            extra = db_dados.get(numero, {})
            fornecedor = extra.get("fornecedor", "—")
            obra_db    = extra.get("obra_db", "")
            if obra_db:
                obra = obra_db
            if extra.get("empresa_faturadora") and extra["empresa_faturadora"] != "—":
                empresa = extra["empresa_faturadora"]

            self._todos.append({
                "nome":               nome,
                "caminho":            caminho,
                "numero":             numero,
                "obra":               obra,
                "fornecedor":         fornecedor,
                "empresa":            empresa,
                "data":               data_mod,
                "valor_total":        extra.get("valor", 0.0),
                "empresa_faturadora": extra.get("empresa_faturadora", empresa),
                "condicao_pagamento": extra.get("condicao_pagamento", "—"),
                "forma_pagamento":    extra.get("forma_pagamento", "—"),
                "obra_nome":          obra,
                "fornecedor_nome":    fornecedor,
            })

        # Respeita o filtro ativo ao recarregar
        self._aplicar_filtros()
        self._atualizar_cards()

    def _parse_nome(self, nome):
        base   = nome.replace(".pdf", "").replace(".PDF", "")
        partes = base.split("-")
        numero = partes[1] if len(partes) > 1 else "—"
        empresa = "—"; obra = "—"
        for emp in ["INTERBRAS", "INTERIORANA", "BRASUL", "B&B", "JB"]:
            if emp in base.upper():
                empresa = emp
                idx  = base.upper().find(emp)
                rest = base[idx+len(emp):].lstrip("-_")
                obra = rest.replace("_", " ").strip() or "—"
                break
        return empresa, numero, obra

    # ══════════════════════════════════════════════════════════════════════════
    # FILTROS
    # ══════════════════════════════════════════════════════════════════════════

    def _set_filtro_data(self, chave):
        self._filtro_ativo = None if chave == "todos" else chave
        self._data_inicio  = None
        self._data_fim     = None
        for k, b in self._btn_filtros.items():
            b.setChecked(k == chave)
        self._lbl_filtro_ativo.setVisible(False)
        self._aplicar_filtros()

    def _filtro_periodo_custom(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Filtrar por período")
        dlg.setMinimumWidth(320)
        dlg.setStyleSheet(f"background:{WHITE}; color:{TXT};")
        vl = QVBoxLayout(dlg); vl.setSpacing(12); vl.setContentsMargins(20,20,20,20)
        hoje = QDate.currentDate()

        hl1 = QHBoxLayout()
        lbl_de = QLabel("De:"); lbl_de.setStyleSheet(f"font-size:12px; color:{TXT}; min-width:30px;")
        de = QDateEdit(hoje.addDays(-30)); de.setCalendarPopup(True); de.setDisplayFormat("dd/MM/yyyy")
        de.setStyleSheet(f"QDateEdit {{ border:1.5px solid {BDR}; border-radius:5px; padding:4px 8px; font-size:12px; min-height:30px; background:{WHITE}; color:{TXT}; }}")
        hl1.addWidget(lbl_de); hl1.addWidget(de)

        hl2 = QHBoxLayout()
        lbl_ate = QLabel("Até:"); lbl_ate.setStyleSheet(lbl_de.styleSheet())
        ate = QDateEdit(hoje); ate.setCalendarPopup(True); ate.setDisplayFormat("dd/MM/yyyy")
        ate.setStyleSheet(de.styleSheet())
        hl2.addWidget(lbl_ate); hl2.addWidget(ate)

        vl.addLayout(hl1); vl.addLayout(hl2)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        bb.button(QDialogButtonBox.Ok).setStyleSheet(
            f"background:{RED}; color:white; font-weight:bold; padding:6px 20px; border-radius:5px; border:none;")
        vl.addWidget(bb)

        if dlg.exec() != QDialog.Accepted:
            return

        self._filtro_ativo = "custom"
        self._data_inicio  = de.date().toPython()
        self._data_fim     = ate.date().toPython()
        for b in self._btn_filtros.values(): b.setChecked(False)

        label = (f"Período: {self._data_inicio.strftime('%d/%m/%Y')} "
                 f"→ {self._data_fim.strftime('%d/%m/%Y')}")
        self._lbl_filtro_ativo.setText(f"📅  {label}")
        self._lbl_filtro_ativo.setVisible(True)
        self._aplicar_filtros()

    def _aplicar_filtros(self):
        termo = self.e_busca.text().strip().lower()
        hoje  = datetime.now().date()
        resultado = self._todos

        if termo:
            resultado = [r for r in resultado if
                         termo in r["nome"].lower() or
                         termo in r["numero"].lower() or
                         termo in r["obra"].lower() or
                         termo in r.get("fornecedor", "").lower()]

        if self._filtro_ativo == "hoje":
            resultado = [r for r in resultado if r["data"].date() == hoje]
        elif self._filtro_ativo == "semana":
            inicio = hoje - timedelta(days=hoje.weekday())
            resultado = [r for r in resultado if r["data"].date() >= inicio]
        elif self._filtro_ativo == "mes":
            resultado = [r for r in resultado if
                         r["data"].year == hoje.year and r["data"].month == hoje.month]
        elif self._filtro_ativo == "custom" and self._data_inicio and self._data_fim:
            resultado = [r for r in resultado if
                         self._data_inicio <= r["data"].date() <= self._data_fim]

        self._preencher_tabela(resultado)

    # ══════════════════════════════════════════════════════════════════════════
    # CARDS
    # ══════════════════════════════════════════════════════════════════════════

    def _atualizar_cards(self):
        total = len(self._todos)
        hoje  = datetime.now().date()
        hoje_list  = [r for r in self._todos if r["data"].date() == hoje]
        hoje_n     = len(hoje_list)
        hoje_valor = sum(float(r.get("valor_total") or 0) for r in hoje_list)

        self._lv_total.setText(str(total))
        self._lv_hoje.setText(str(hoje_n))
        self._lv_valor.setText(self._fmt(hoje_valor))

    # ══════════════════════════════════════════════════════════════════════════
    # TABELA
    # ══════════════════════════════════════════════════════════════════════════

    def _preencher_tabela(self, registros):
        self.tabela.setRowCount(0)

        for dados in registros:
            r = self.tabela.rowCount()
            self.tabela.insertRow(r)
            self.tabela.setRowHeight(r, 48)
            bg = WHITE if r % 2 == 0 else "#FBF7F7"

            def _it(txt, align=Qt.AlignVCenter|Qt.AlignLeft, bold=False, cor=None):
                it = QTableWidgetItem(str(txt)); it.setTextAlignment(align)
                it.setBackground(QColor(bg))
                if bold: f = QFont(); f.setBold(True); it.setFont(f)
                if cor:  it.setForeground(QColor(cor))
                return it

            self.tabela.setItem(r, 0, _it(f"#{dados['numero']}", Qt.AlignVCenter|Qt.AlignCenter, bold=True, cor=RED))
            self.tabela.setItem(r, 1, _it(dados["data"].strftime("%d/%m/%Y"), Qt.AlignVCenter|Qt.AlignCenter, cor=TXT_S))
            self.tabela.setItem(r, 2, _it(dados["obra"], bold=True))
            self.tabela.setItem(r, 3, _it(dados.get("fornecedor", "—"), cor=TXT_S))
            cor_e = CORES_EMPRESA.get(dados["empresa"], TXT_S)
            self.tabela.setItem(r, 4, _it(dados["empresa"], Qt.AlignVCenter|Qt.AlignCenter, bold=True, cor=cor_e))

            cell = QWidget(); cell.setStyleSheet(f"background:{bg};")
            hl = QHBoxLayout(cell); hl.setContentsMargins(8,6,8,6); hl.setSpacing(8)
            ba = btn_solid("📄 Abrir", BLUE, h=30)
            p  = dados["caminho"]
            ba.clicked.connect(lambda _, x=p: self._abrir_pdf(x))
            be = btn_solid("💾 Exportar", GREEN, h=30)
            n  = dados["nome"]
            be.clicked.connect(lambda _, x=p, y=n: self._exportar(x, y))
            hl.addWidget(ba); hl.addWidget(be)
            self.tabela.setCellWidget(r, 5, cell)

        total = len(registros)
        self._lbl_cont.setText(f"{total} pedido{'s' if total!=1 else ''}")

        if total == 0:
            self.tabela.setRowCount(1); self.tabela.setSpan(0, 0, 1, 6)
            it = QTableWidgetItem("Nenhum pedido encontrado. Gere um pedido na aba 'Pedido de Compra'.")
            it.setTextAlignment(Qt.AlignCenter); it.setForeground(QColor(TXT_S))
            self.tabela.setItem(0, 0, it)

    # ══════════════════════════════════════════════════════════════════════════
    # IMPRESSÃO — RELAÇÃO DE PEDIDOS
    # ══════════════════════════════════════════════════════════════════════════

    def _imprimir_hoje(self):
                # Gera e abre para impressão a Relação de Pedidos de hoje.
        hoje = datetime.now().date()
        self._gerar_e_imprimir_relacao(hoje)

    def _imprimir_por_data(self):
                # Abre seletor de data e imprime a Relação de Pedidos do dia escolhido.
        dlg = QDialog(self)
        dlg.setWindowTitle("Selecionar data para impressão")
        dlg.setMinimumWidth(300)
        dlg.setStyleSheet(f"background:{WHITE}; color:{TXT};")
        vl = QVBoxLayout(dlg); vl.setSpacing(14); vl.setContentsMargins(24,24,24,24)

        lbl = QLabel("Selecione a data dos pedidos:")
        lbl.setStyleSheet(f"font-size:13px; color:{TXT}; background:transparent;")
        vl.addWidget(lbl)

        date_edit = QDateEdit(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("dd/MM/yyyy")
        date_edit.setStyleSheet(f"""
            QDateEdit {{
                border:1.5px solid {BDR}; border-radius:6px;
                padding:6px 10px; font-size:13px; min-height:34px;
                background:{WHITE}; color:{TXT};
            }}
        """)
        vl.addWidget(date_edit)

        # Info
        lbl_info = QLabel("O relatório incluirá todos os pedidos\ncriados nessa data.")
        lbl_info.setStyleSheet(f"font-size:11px; color:{TXT_S}; background:transparent;")
        vl.addWidget(lbl_info)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("🖨  Imprimir")
        bb.button(QDialogButtonBox.Ok).setStyleSheet(
            f"background:{RED}; color:white; font-weight:bold; "
            f"padding:6px 20px; border-radius:5px; border:none;")
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        vl.addWidget(bb)

        if dlg.exec() != QDialog.Accepted:
            return

        data_sel = date_edit.date().toPython()
        self._gerar_e_imprimir_relacao(data_sel)

    def _gerar_e_imprimir_relacao(self, data_ref: date):
                # Filtra pedidos pela data, pede comprador, confirma e gera PDF.
        # ── 1. Filtra pedidos do dia ──────────────────────────────────────────
        pedidos_dia = [p for p in self._todos if p["data"].date() == data_ref]

        if not pedidos_dia:
            QMessageBox.information(
                self, "Sem pedidos",
                f"Nenhum pedido encontrado para {data_ref.strftime('%d/%m/%Y')}.\n\n"
                f"Verifique se os pedidos foram gerados nesta data."
            )
            return

        # ── 2. Selecionar comprador ───────────────────────────────────────────
        from app.ui.dialogs.selecionar_comprador_dialog import SelecionarCompradorDialog
        data_fmt = data_ref.strftime('%d/%m/%Y')
        dlg_comp = SelecionarCompradorDialog(
            parent=self,
            titulo_relatorio=f"Relação de Pedidos — {data_fmt}"
        )
        if dlg_comp.exec() != QDialog.Accepted:
            return
        comprador = dlg_comp.comprador_selecionado or "—"

        # ── 3. Confirmar impressão (Sim / Não) ────────────────────────────────
        total_val = sum(float(p.get("valor_total") or 0) for p in pedidos_dia)

        dlg_conf = QDialog(self)
        dlg_conf.setWindowTitle("Confirmar impressão")
        dlg_conf.setMinimumWidth(340)
        dlg_conf.setStyleSheet(f"background:{WHITE}; color:{TXT};")
        vl_c = QVBoxLayout(dlg_conf)
        vl_c.setContentsMargins(24, 20, 24, 20)
        vl_c.setSpacing(12)

        lbl_conf_titulo = QLabel(f"<b>Relação de Pedidos — {data_fmt}</b>")
        lbl_conf_titulo.setStyleSheet(f"font-size:13px; color:{GRAY}; background:transparent;")
        vl_c.addWidget(lbl_conf_titulo)

        lbl_conf_info = QLabel(
            f"📋  {len(pedidos_dia)} pedido{'s' if len(pedidos_dia)!=1 else ''}<br>"
            f"💰  Total: R$ {self._fmt(total_val)}<br>"
            f"👤  Comprador: <b>{comprador}</b>"
        )
        lbl_conf_info.setStyleSheet(f"font-size:12px; color:{TXT}; background:transparent; line-height:1.8;")
        lbl_conf_info.setTextFormat(Qt.RichText)
        vl_c.addWidget(lbl_conf_info)

        lbl_conf_perg = QLabel("Gerar PDF e abrir para impressão?")
        lbl_conf_perg.setStyleSheet(f"font-size:12px; color:{TXT_S}; background:transparent;")
        vl_c.addWidget(lbl_conf_perg)

        sep_c = QFrame(); sep_c.setFrameShape(QFrame.HLine)
        sep_c.setStyleSheet(f"background:#E8DEDE;"); sep_c.setFixedHeight(1)
        vl_c.addWidget(sep_c)

        hl_c = QHBoxLayout(); hl_c.setSpacing(10); hl_c.addStretch()
        btn_nao = btn_outline("Não", h=36)
        btn_nao.setMinimumWidth(80)
        btn_nao.clicked.connect(dlg_conf.reject)
        btn_sim = btn_solid("Sim", RED, h=36)
        btn_sim.setMinimumWidth(80)
        btn_sim.clicked.connect(dlg_conf.accept)
        hl_c.addWidget(btn_nao); hl_c.addWidget(btn_sim)
        vl_c.addLayout(hl_c)

        if dlg_conf.exec() != QDialog.Accepted:
            return

        # ── 4. Gerar PDF ──────────────────────────────────────────────────────
        try:
            from app.infrastructure.relacao_pedidos_pdf import gerar_relacao_pdf

            ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arq  = f"RELACAO_PEDIDOS_{data_ref.strftime('%d%m%Y')}_{ts}.pdf"
            pasta_rel = os.path.join(PEDIDOS_DIR, "relacoes")
            os.makedirs(pasta_rel, exist_ok=True)
            caminho   = os.path.join(pasta_rel, nome_arq)

            gerar_relacao_pdf(
                caminho=caminho,
                pedidos=pedidos_dia,
                data_ref=data_ref,
                comprador=comprador,
                agrupar_por_empresa=True,
            )

            self._abrir_pdf(caminho)

            QMessageBox.information(
                self, "Relatório gerado!",
                f"<b>{nome_arq}</b><br><br>"
                f"Aberto para impressão.<br>"
                f"Salvo em: <code>{pasta_rel}</code>"
            )

        except Exception as e:
            QMessageBox.critical(self, "Erro ao gerar relatório", str(e))
            import traceback; traceback.print_exc()

    # ══════════════════════════════════════════════════════════════════════════
    # AÇÕES DE ARQUIVO
    # ══════════════════════════════════════════════════════════════════════════

    def _abrir_pdf(self, caminho):
        try:
            if sys.platform == "win32":    os.startfile(caminho)
            elif sys.platform == "darwin": subprocess.run(["open", caminho])
            else:                          subprocess.run(["xdg-open", caminho])
        except Exception as e:
            QMessageBox.warning(self, "Erro ao abrir", str(e))

    def _exportar(self, caminho_origem, nome_arquivo):
        pasta = QFileDialog.getExistingDirectory(
            self, "Escolha a pasta onde salvar a cópia do PDF",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if not pasta: return
        destino = os.path.join(pasta, nome_arquivo)
        if os.path.exists(destino):
            resp = QMessageBox.question(self, "Arquivo já existe",
                f"Já existe:\n{nome_arquivo}\n\nDeseja substituir?",
                QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
            if resp != QMessageBox.Yes: return
        try:
            shutil.copy2(caminho_origem, destino)
            msg = QMessageBox(self)
            msg.setWindowTitle("Exportado!")
            msg.setText(f"<b>{nome_arquivo}</b><br><br>Salvo em:<br><code>{destino}</code>")
            msg.setIcon(QMessageBox.Information)
            b_ab = msg.addButton("📂 Abrir pasta", QMessageBox.ActionRole)
            msg.addButton("OK", QMessageBox.AcceptRole)
            msg.exec()
            if msg.clickedButton() == b_ab:
                self._abrir_pasta(pasta)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao exportar", str(e))

    def _abrir_pasta(self, pasta):
        try:
            if sys.platform == "win32":    os.startfile(pasta)
            elif sys.platform == "darwin": subprocess.run(["open", pasta])
            else:                          subprocess.run(["xdg-open", pasta])
        except Exception: pass

    def _abrir_pasta_gerados(self):
        os.makedirs(PEDIDOS_DIR, exist_ok=True)
        self._abrir_pasta(PEDIDOS_DIR)

    @staticmethod
    def _fmt(v):
        try:
            return f"{float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
        except Exception:
            return "0,00"

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._carregar)
