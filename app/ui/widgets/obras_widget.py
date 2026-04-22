# app/ui/widgets/obras_widget.py
# Aba de cadastro e gerenciamento de obras.
import os, sys, json, subprocess
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QFrame, QGraphicsDropShadowEffect, QDialog,
    QFormLayout, QDialogButtonBox, QComboBox, QSplitter,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

# ── Estilo centralizado ───────────────────────────────────────────────────────
from app.ui.style import (
    RED, GRAY, WHITE, BG, BDR, BDR_F, TXT, TXT_S, SEL, HOV, GREEN, BLUE,
    RO_BG, CSS_INPUT, CSS_COMBO, CSS_BUSCA, CSS_TABLE, CSS_TABLE_SM,
    CORES_EMPRESA,
    btn_solid, btn_outline, make_card, card_container,
)

_ASSETS = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets')
)
_OBR = os.path.join(_ASSETS, 'obras.json')


def _load_json(p):
    try:
        with open(p, encoding='utf-8') as f: return json.load(f)
    except Exception: return {}

def _save_json(p, d):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# DIÁLOGO — EDITAR OBRA
# ══════════════════════════════════════════════════════════════════════════════

class EditarObraDialog(QDialog):
    def __init__(self, nome_obra, dados, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editar Obra — {nome_obra}")
        self.setMinimumWidth(560)
        self.setStyleSheet(f"background:{WHITE}; color:{TXT};")

        form = QFormLayout(self)
        form.setSpacing(10); form.setContentsMargins(20, 20, 20, 20)

        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{TXT}; font-size:12px;"); return l

        def fld(val="", ro=False):
            f = QLineEdit(val); f.setReadOnly(ro); f.setStyleSheet(CSS_INPUT); return f

        try:
            from config import EMPRESAS_FATURADORAS
            empresas = list(EMPRESAS_FATURADORAS.keys())
        except Exception:
            empresas = ["BRASUL", "JB", "B&B", "INTERIORANA", "INTERBRAS"]

        self._nome     = fld(nome_obra, ro=True)
        self._escola   = fld(dados.get("escola", ""))
        self._fat      = QComboBox(); self._fat.addItems(empresas)
        self._fat.setStyleSheet(CSS_COMBO)
        idx = self._fat.findText(dados.get("faturamento", ""))
        if idx >= 0: self._fat.setCurrentIndex(idx)
        self._end      = fld(dados.get("endereco", ""))
        self._bairro   = fld(dados.get("bairro", ""))
        self._cep      = fld(dados.get("cep", ""))
        self._cidade   = fld(dados.get("cidade", ""))
        self._uf       = fld(dados.get("uf", "SP"))
        self._contrato = fld(dados.get("contrato", "0"))

        form.addRow(lbl("Nome da Obra"),         self._nome)
        form.addRow(lbl("Escola / Descrição"),   self._escola)
        form.addRow(lbl("Faturamento"),          self._fat)
        form.addRow(lbl("Endereço de Entrega"),  self._end)
        form.addRow(lbl("Bairro"),               self._bairro)
        form.addRow(lbl("CEP"),                  self._cep)
        form.addRow(lbl("Cidade"),               self._cidade)
        form.addRow(lbl("UF"),                   self._uf)
        form.addRow(lbl("Nº Contrato"),          self._contrato)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        bb.button(QDialogButtonBox.Save).setText("💾  Salvar")
        bb.button(QDialogButtonBox.Save).setStyleSheet(
            f"background:{RED}; color:white; font-weight:bold;"
            f"padding:6px 20px; border-radius:5px; border:none;")
        form.addRow(bb)

    @property
    def resultado(self):
        return {
            "escola":      self._escola.text().strip(),
            "faturamento": self._fat.currentText(),
            "endereco":    self._end.text().strip(),
            "bairro":      self._bairro.text().strip(),
            "cep":         self._cep.text().strip(),
            "cidade":      self._cidade.text().strip(),
            "uf":          self._uf.text().strip() or "SP",
            "contrato":    self._contrato.text().strip() or "0",
        }


# ══════════════════════════════════════════════════════════════════════════════
# WIDGET PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class ObrasWidget(QWidget):

    def __init__(self):
        super().__init__()
        self._obras = {}
        self._obra_atual = None
        self._pedidos_obra_atual = []
        self._build()
        self._carregar()

    def _build(self):
        self.setStyleSheet(f"background:{BG};")
        vl = QVBoxLayout(self)
        vl.setContentsMargins(24, 20, 24, 20)
        vl.setSpacing(16)

        # ── Cabeçalho ─────────────────────────────────────────────────────────
        hl_top = QHBoxLayout()
        tv = QVBoxLayout(); tv.setSpacing(2)
        titulo = QLabel("Obras")
        titulo.setStyleSheet(f"font-size:20px; font-weight:bold; color:{GRAY}; background:transparent;")
        sub = QLabel("Cadastro e histórico de obras")
        sub.setStyleSheet(f"font-size:11px; color:{TXT_S}; background:transparent;")
        tv.addWidget(titulo); tv.addWidget(sub)
        hl_top.addLayout(tv); hl_top.addStretch()
        btn_att = btn_solid("↻  Atualizar", "#95A5A6")
        btn_att.clicked.connect(self._carregar)
        hl_top.addWidget(btn_att)
        vl.addLayout(hl_top)

        # ── Cards ─────────────────────────────────────────────────────────────
        hl_cards = QHBoxLayout(); hl_cards.setSpacing(14)
        c1, self._lv_total   = make_card("Total de Obras",    "—", RED)
        c2, self._lv_cidade  = make_card("Cidades",           "—", BLUE)
        c3, self._lv_pedidos = make_card("Pedidos Emitidos",  "—", GREEN)
        hl_cards.addWidget(c1); hl_cards.addWidget(c2); hl_cards.addWidget(c3)
        hl_cards.addStretch()
        vl.addLayout(hl_cards)

        # ── Busca ─────────────────────────────────────────────────────────────
        hl_busca = QHBoxLayout(); hl_busca.setSpacing(10)
        busca_wrap = QWidget(); busca_wrap.setFixedHeight(36); busca_wrap.setMaximumWidth(420)
        bwl = QHBoxLayout(busca_wrap); bwl.setContentsMargins(0,0,0,0); bwl.setSpacing(0)
        self.e_busca = QLineEdit()
        self.e_busca.setPlaceholderText("Buscar por nome, escola, cidade...")
        self.e_busca.setStyleSheet(CSS_BUSCA)
        self.e_busca.textChanged.connect(self._filtrar)
        bwl.addWidget(self.e_busca)
        ico = QLabel("🔍"); ico.setStyleSheet("background:transparent; font-size:13px; border:none;")
        ico.setFixedWidth(28); ico.setParent(busca_wrap); ico.move(8, 9); ico.raise_()
        hl_busca.addWidget(busca_wrap); hl_busca.addStretch()
        self._lbl_cont = QLabel("")
        self._lbl_cont.setStyleSheet(f"font-size:11px; color:{TXT_S}; background:transparent;")
        hl_busca.addWidget(self._lbl_cont)
        vl.addLayout(hl_busca)

        # ── Splitter: tabela + painel de relatório ─────────────────────────────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background:#E8DEDE; width:2px; }")

        tabela_container = card_container()
        sombra1 = QGraphicsDropShadowEffect()
        sombra1.setBlurRadius(16); sombra1.setOffset(0,2); sombra1.setColor(QColor(0,0,0,18))
        tabela_container.setGraphicsEffect(sombra1)
        tcl = QVBoxLayout(tabela_container); tcl.setContentsMargins(0,0,0,0)

        self.tabela = QTableWidget(0, 6)
        self.tabela.setHorizontalHeaderLabels(["Obra", "Escola", "Cidade", "UF", "Faturamento", "Ações"])
        self.tabela.setStyleSheet(CSS_TABLE)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setShowGrid(False)
        self.tabela.setFrameShape(QFrame.NoFrame)
        hh = self.tabela.horizontalHeader(); hh.setHighlightSections(False)
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Fixed); self.tabela.setColumnWidth(2, 120)
        hh.setSectionResizeMode(3, QHeaderView.Fixed); self.tabela.setColumnWidth(3, 45)
        hh.setSectionResizeMode(4, QHeaderView.Fixed); self.tabela.setColumnWidth(4, 110)
        hh.setSectionResizeMode(5, QHeaderView.Fixed); self.tabela.setColumnWidth(5, 150)
        self.tabela.itemSelectionChanged.connect(self._on_selecao)
        tcl.addWidget(self.tabela)
        splitter.addWidget(tabela_container)

        self._painel = self._build_painel()
        splitter.addWidget(self._painel)
        splitter.setSizes([650, 400])
        vl.addWidget(splitter, 1)

    def _build_painel(self):
        painel = card_container()
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(16); sombra.setOffset(0,2); sombra.setColor(QColor(0,0,0,18))
        painel.setGraphicsEffect(sombra)

        vl = QVBoxLayout(painel); vl.setContentsMargins(16,16,16,16); vl.setSpacing(12)

        self._lbl_obra_sel = QLabel("← Selecione uma obra")
        self._lbl_obra_sel.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{GRAY}; background:transparent;")
        self._lbl_obra_sel.setWordWrap(True)
        vl.addWidget(self._lbl_obra_sel)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:#E8DEDE;"); sep.setFixedHeight(1)
        vl.addWidget(sep)

        self._lbl_dados_obra = QLabel("")
        self._lbl_dados_obra.setStyleSheet(
            f"font-size:11px; color:{TXT_S}; background:transparent; line-height:1.6;")
        self._lbl_dados_obra.setWordWrap(True)
        vl.addWidget(self._lbl_dados_obra)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"background:#E8DEDE;"); sep2.setFixedHeight(1)
        vl.addWidget(sep2)

        hl_resumo = QHBoxLayout(); hl_resumo.setSpacing(8)
        self._card_npedidos  = self._mini_card("Pedidos",    "—", RED)
        self._card_total_obra = self._mini_card("Total Gasto", "—", GREEN)
        hl_resumo.addWidget(self._card_npedidos)
        hl_resumo.addWidget(self._card_total_obra)
        vl.addLayout(hl_resumo)

        lbl_ped = QLabel("PEDIDOS EMITIDOS")
        lbl_ped.setStyleSheet(
            f"font-size:9px; font-weight:700; color:{TXT_S}; background:transparent; letter-spacing:1px;")
        vl.addWidget(lbl_ped)

        self._tabela_pedidos = QTableWidget(0, 4)
        self._tabela_pedidos.setHorizontalHeaderLabels(["Nº", "Data", "Fornecedor", "Total"])
        self._tabela_pedidos.setStyleSheet(CSS_TABLE_SM)
        self._tabela_pedidos.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabela_pedidos.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabela_pedidos.verticalHeader().setVisible(False)
        self._tabela_pedidos.setShowGrid(False)
        self._tabela_pedidos.setFrameShape(QFrame.NoFrame)
        hh2 = self._tabela_pedidos.horizontalHeader(); hh2.setHighlightSections(False)
        hh2.setSectionResizeMode(0, QHeaderView.Fixed); self._tabela_pedidos.setColumnWidth(0, 55)
        hh2.setSectionResizeMode(1, QHeaderView.Fixed); self._tabela_pedidos.setColumnWidth(1, 80)
        hh2.setSectionResizeMode(2, QHeaderView.Stretch)
        hh2.setSectionResizeMode(3, QHeaderView.Fixed); self._tabela_pedidos.setColumnWidth(3, 85)
        vl.addWidget(self._tabela_pedidos, 1)

        sep3 = QFrame(); sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet(f"background:#E8DEDE;"); sep3.setFixedHeight(1)
        vl.addWidget(sep3)

        self._btn_export_xls = btn_solid("📊  Exportar Excel", GREEN)
        self._btn_export_xls.setEnabled(False)
        self._btn_export_xls.setToolTip("Gera Excel com 3 abas: Resumo, Pedidos e Itens")
        self._btn_export_xls.clicked.connect(self._exportar_relatorio_excel)
        vl.addWidget(self._btn_export_xls)
        return painel

    def _mini_card(self, titulo, valor, cor):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background:#FAFAFA; border-radius:8px;
                border-left:3px solid {cor};
                border-top:1px solid #EEE5E5;
                border-right:1px solid #EEE5E5;
                border-bottom:1px solid #EEE5E5;
            }}
        """)
        vl = QVBoxLayout(card); vl.setContentsMargins(10,8,10,8); vl.setSpacing(2)
        lt = QLabel(titulo.upper())
        lt.setStyleSheet(f"font-size:8px; font-weight:700; color:{TXT_S}; background:transparent; border:none; letter-spacing:1px;")
        lv = QLabel(valor)
        lv.setStyleSheet(f"font-size:16px; font-weight:bold; color:{cor}; background:transparent; border:none;")
        lv.setObjectName("mini_val")
        vl.addWidget(lt); vl.addWidget(lv)
        return card

    # ══════════════════════════════════════════════════════════════════════════
    # DADOS
    # ══════════════════════════════════════════════════════════════════════════

    def _carregar(self):
        self._obras = _load_json(_OBR)
        self._pedidos_por_obra = {}
        self._total_por_obra   = {}
        try:
            from app.data.database import get_connection
            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT obra_nome, COUNT(*) as n, SUM(valor_total) as vt "
                    "FROM pedidos GROUP BY obra_nome"
                ).fetchall()
                for row in rows:
                    self._pedidos_por_obra[row["obra_nome"]] = row["n"]
                    self._total_por_obra[row["obra_nome"]]   = row["vt"] or 0.0
        except Exception as e:
            print(f"[ObrasWidget] {e}")

        self._preencher_tabela(self._obras)
        self._atualizar_cards()

    def _atualizar_cards(self):
        total   = len(self._obras)
        cidades = len({v.get("cidade","") for v in self._obras.values() if v.get("cidade","")})
        pedidos = sum(self._pedidos_por_obra.values())
        self._lv_total.setText(str(total))
        self._lv_cidade.setText(str(cidades))
        self._lv_pedidos.setText(str(pedidos))

    def _filtrar(self, texto):
        termo = texto.strip().lower()
        if not termo:
            self._preencher_tabela(self._obras); return
        filtradas = {
            k: v for k, v in self._obras.items()
            if termo in k.lower()
            or termo in v.get("escola","").lower()
            or termo in v.get("cidade","").lower()
            or termo in v.get("bairro","").lower()
        }
        self._preencher_tabela(filtradas)

    def _preencher_tabela(self, obras):
        self.tabela.setRowCount(0)
        for nome, dados in sorted(obras.items()):
            r = self.tabela.rowCount()
            self.tabela.insertRow(r)
            self.tabela.setRowHeight(r, 48)
            bg = WHITE if r % 2 == 0 else "#FBF7F7"

            def _it(txt, align=Qt.AlignVCenter|Qt.AlignLeft, bold=False, cor=None):
                it = QTableWidgetItem(str(txt)); it.setTextAlignment(align)
                it.setBackground(QColor(bg))
                if bold: f = QFont(); f.setBold(True); it.setFont(f)
                if cor:  it.setForeground(QColor(cor))
                it.setData(Qt.UserRole, nome)
                return it

            fat     = dados.get("faturamento", "—")
            cor_fat = CORES_EMPRESA.get(fat, TXT_S)

            self.tabela.setItem(r, 0, _it(nome, bold=True))
            self.tabela.setItem(r, 1, _it(dados.get("escola","—"), cor=TXT_S))
            self.tabela.setItem(r, 2, _it(dados.get("cidade","—"), cor=TXT_S))
            self.tabela.setItem(r, 3, _it(dados.get("uf","SP"), Qt.AlignVCenter|Qt.AlignCenter, cor=TXT_S))
            self.tabela.setItem(r, 4, _it(fat, Qt.AlignVCenter|Qt.AlignCenter, bold=True, cor=cor_fat))

            cell = QWidget(); cell.setStyleSheet(f"background:{bg};")
            hl = QHBoxLayout(cell); hl.setContentsMargins(6,6,6,6); hl.setSpacing(6)
            be = btn_solid("✏ Editar", BLUE, h=30)
            be.clicked.connect(lambda _, n=nome: self._editar(n))
            bx = btn_solid("🗑", "#E74C3C", h=30); bx.setFixedWidth(34)
            bx.setToolTip(f"Excluir obra '{nome}'")
            bx.clicked.connect(lambda _, n=nome: self._excluir(n))
            hl.addWidget(be); hl.addWidget(bx)
            self.tabela.setCellWidget(r, 5, cell)

        total = len(obras)
        self._lbl_cont.setText(f"{total} obra{'s' if total!=1 else ''}")
        if total == 0:
            self.tabela.setRowCount(1); self.tabela.setSpan(0,0,1,6)
            it = QTableWidgetItem("Nenhuma obra encontrada.")
            it.setTextAlignment(Qt.AlignCenter); it.setForeground(QColor(TXT_S))
            self.tabela.setItem(0,0,it)

    # ══════════════════════════════════════════════════════════════════════════
    # RELATÓRIO DA OBRA SELECIONADA
    # ══════════════════════════════════════════════════════════════════════════

    def _on_selecao(self):
        rows = self.tabela.selectedItems()
        if not rows: return
        nome = rows[0].data(Qt.UserRole)
        if nome: self._mostrar_relatorio(nome)

    def _mostrar_relatorio(self, nome_obra):
        dados = self._obras.get(nome_obra, {})
        self._lbl_obra_sel.setText(f"📍 {nome_obra}")
        self._btn_export_xls.setEnabled(True)
        self._obra_atual = nome_obra

        info = []
        if dados.get("escola"):      info.append(f"🏫  {dados['escola']}")
        if dados.get("endereco"):    info.append(f"📌  {dados['endereco']}")
        if dados.get("cidade"):      info.append(f"🏙  {dados['cidade']} — {dados.get('uf','SP')}")
        if dados.get("cep"):         info.append(f"CEP: {dados['cep']}")
        if dados.get("contrato"):    info.append(f"Contrato Nº: {dados['contrato']}")
        if dados.get("faturamento"): info.append(f"Faturamento: {dados['faturamento']}")
        self._lbl_dados_obra.setText("\n".join(info) if info else "Sem dados cadastrados.")

        pedidos = []
        try:
            from app.data.database import get_connection
            with get_connection() as conn:
                pedidos = conn.execute(
                    "SELECT numero, data_pedido, fornecedor_nome, valor_total "
                    "FROM pedidos WHERE obra_nome = ? ORDER BY CAST(numero AS INTEGER) DESC",
                    (nome_obra,)
                ).fetchall()
        except Exception as e:
            print(f"[ObrasWidget] relatório: {e}")

        def _vt(p):
            try: v = p["valor_total"]; return float(v) if v is not None else 0.0
            except: return 0.0

        total_gasto = sum(_vt(p) for p in pedidos)
        for lv in self._card_npedidos.findChildren(QLabel):
            if lv.objectName() == "mini_val": lv.setText(str(len(pedidos)))
        for lv in self._card_total_obra.findChildren(QLabel):
            if lv.objectName() == "mini_val": lv.setText(f"R$ {self._fmt(total_gasto)}")

        self._tabela_pedidos.setRowCount(0)
        for p in pedidos:
            r = self._tabela_pedidos.rowCount()
            self._tabela_pedidos.insertRow(r)
            self._tabela_pedidos.setRowHeight(r, 36)
            bg = WHITE if r % 2 == 0 else "#FBF7F7"

            def _it2(txt, align=Qt.AlignVCenter|Qt.AlignLeft, cor=None, bold=False):
                it = QTableWidgetItem(str(txt)); it.setTextAlignment(align)
                it.setBackground(QColor(bg))
                if cor:  it.setForeground(QColor(cor))
                if bold: f = QFont(); f.setBold(True); it.setFont(f)
                return it

            def _pf(key, default="—"):
                try: v = p[key]; return str(v) if v is not None else default
                except: return default

            self._tabela_pedidos.setItem(r, 0, _it2(f"#{_pf('numero','?')}", Qt.AlignVCenter|Qt.AlignCenter, cor=RED, bold=True))
            self._tabela_pedidos.setItem(r, 1, _it2(_pf("data_pedido"), Qt.AlignVCenter|Qt.AlignCenter, cor=TXT_S))
            self._tabela_pedidos.setItem(r, 2, _it2(_pf("fornecedor_nome"), cor=TXT_S))
            self._tabela_pedidos.setItem(r, 3, _it2(f"R$ {self._fmt(_vt(p))}", Qt.AlignVCenter|Qt.AlignRight, cor=GRAY, bold=True))

        self._pedidos_obra_atual = list(pedidos)
        if not pedidos:
            self._tabela_pedidos.setRowCount(1); self._tabela_pedidos.setSpan(0,0,1,4)
            it = QTableWidgetItem("Nenhum pedido emitido para esta obra.")
            it.setTextAlignment(Qt.AlignCenter); it.setForeground(QColor(TXT_S))
            self._tabela_pedidos.setItem(0,0,it)

    # ══════════════════════════════════════════════════════════════════════════
    # AÇÕES
    # ══════════════════════════════════════════════════════════════════════════

    def _editar(self, nome_obra):
        dados = self._obras.get(nome_obra, {})
        dlg = EditarObraDialog(nome_obra, dados, self)
        if dlg.exec() != QDialog.Accepted: return
        self._obras[nome_obra] = dlg.resultado
        _save_json(_OBR, self._obras)
        self._carregar()
        QMessageBox.information(self, "Salvo!", f"Obra '{nome_obra}' atualizada com sucesso.")

    def _excluir(self, nome_obra):
        resp = QMessageBox.question(
            self, "Confirmar exclusão",
            f"Deseja realmente excluir a obra:\n\n'{nome_obra}'?\n\n"
            f"Os pedidos desta obra no banco de dados NÃO serão apagados.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes: return
        if nome_obra in self._obras:
            del self._obras[nome_obra]
            _save_json(_OBR, self._obras)
            self._carregar()
            self._lbl_obra_sel.setText("← Selecione uma obra")
            self._lbl_dados_obra.setText("")
            self._tabela_pedidos.setRowCount(0)
            QMessageBox.information(self, "Removida", f"Obra '{nome_obra}' removida do cadastro.")

    def _exportar_relatorio_excel(self):
        if not self._obra_atual: return
        from PySide6.QtWidgets import QFileDialog
        from datetime import datetime as _dt
        nome_obra = self._obra_atual
        dados     = self._obras.get(nome_obra, {})
        pedidos   = self._pedidos_obra_atual

        itens_por_pedido = {}
        try:
            from app.data.database import get_connection
            with get_connection() as conn:
                rows = conn.execute("""
                    SELECT p.numero, i.descricao, i.quantidade, i.unidade,
                           i.valor_unitario, i.valor_total, i.categoria
                    FROM itens_pedido i
                    JOIN pedidos p ON p.id = i.pedido_id
                    WHERE p.obra_nome = ?
                    ORDER BY CAST(p.numero AS INTEGER), i.id
                """, (nome_obra,)).fetchall()
                for row in rows:
                    num = str(row["numero"])
                    if num not in itens_por_pedido: itens_por_pedido[num] = []
                    itens_por_pedido[num].append(row)
        except Exception as e:
            print(f"[Excel] itens: {e}")

        nome_safe = "".join(c for c in nome_obra if c.isalnum() or c in " _-")[:40].strip().replace(" ","_")
        ts        = _dt.now().strftime("%Y%m%d_%H%M%S")
        pasta_doc = os.path.join(os.path.expanduser("~"), "Documents")
        pasta_ini = pasta_doc if os.path.isdir(pasta_doc) else os.path.expanduser("~")
        sugestao  = os.path.join(pasta_ini, f"RELATORIO_{nome_safe}_{ts}.xlsx")

        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar Relatório Excel", sugestao, "Excel (*.xlsx)")
        if not caminho: return

        try:
            from app.ui.widgets.relatorio_obra_excel import gerar_excel
            gerar_excel(caminho, nome_obra, dados, pedidos, itens_por_pedido)
            msg = QMessageBox(self)
            msg.setWindowTitle("Excel gerado!")
            msg.setText(f"<b>{os.path.basename(caminho)}</b><br><br>Salvo em:<br><code>{caminho}</code>")
            msg.setIcon(QMessageBox.Information)
            b_ab = msg.addButton("📂 Abrir", QMessageBox.ActionRole)
            msg.addButton("OK", QMessageBox.AcceptRole)
            msg.exec()
            if msg.clickedButton() == b_ab:
                try:
                    if sys.platform == "win32": os.startfile(caminho)
                    elif sys.platform == "darwin": subprocess.run(["open", caminho])
                    else: subprocess.run(["xdg-open", caminho])
                except Exception: pass
        except PermissionError:
            QMessageBox.critical(self, "Erro", "Arquivo já está aberto. Feche e tente novamente.")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao gerar Excel", str(e))

    @staticmethod
    def _fmt(v):
        try:
            return f"{float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
        except Exception:
            return "0,00"

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._carregar)
