# app/ui/widgets/pedidos_widget.py
# Aba de pedidos gerados com filtros e impressão.
import os, sys, subprocess, shutil, tempfile
from datetime import datetime, date, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QLineEdit, QFrame, QGraphicsDropShadowEffect,
    QDialog, QDialogButtonBox, QDateEdit, QSizePolicy, QApplication,
)
from PySide6.QtCore import Qt, QTimer, QDate
from PySide6.QtGui import QColor, QFont

# ── Estilo centralizado ───────────────────────────────────────────────────────
from app.ui.style import (
    RED, GRAY, WHITE, BG, BDR, TXT, TXT_S, SEL, HOV, GREEN, BLUE,
    CSS_BUSCA, CSS_TABLE, CORES_EMPRESA,
    btn_solid, btn_outline, btn_filtro, make_card, card_container,
)

from config import PEDIDOS_DIR, COMPRADOR_PADRAO


class PedidosWidget(QWidget):

    _PAGE_SIZE = 50  # quantos pedidos renderizar por vez

    def __init__(self):
        super().__init__()
        self._todos             = []
        self._filtrados         = []   # resultado após filtros (paginação age sobre isso)
        self._pagina_atual      = 0    # quantas páginas já foram renderizadas
        self._filtro_ativo      = None
        self._data_inicio       = None
        self._data_fim          = None
        self._build()
        self._set_filtro_data("todos")
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
        sub = QLabel(f"Pedidos registrados no banco — comprador: {COMPRADOR_PADRAO}")
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
        hh.setSectionResizeMode(5, QHeaderView.Fixed);  self.tabela.setColumnWidth(5, 380)
        cvl.addWidget(self.tabela)
        vl.addWidget(container, 1)

        # ── Rodapé paginação ───────────────────────────────────────────────────
        hl_pag = QHBoxLayout(); hl_pag.setSpacing(12)
        self._lbl_pagina = QLabel("")
        self._lbl_pagina.setStyleSheet(f"font-size:11px; color:{TXT_S}; background:transparent;")
        self._btn_mais = btn_outline("⬇  Carregar mais 50")
        self._btn_mais.setFixedHeight(32)
        self._btn_mais.setVisible(False)
        self._btn_mais.clicked.connect(self._carregar_mais)
        hl_pag.addWidget(self._lbl_pagina)
        hl_pag.addStretch()
        hl_pag.addWidget(self._btn_mais)
        vl.addLayout(hl_pag)

        rodape = QLabel(f"📌  {PEDIDOS_DIR}")
        rodape.setStyleSheet(f"font-size:10px; color:{TXT_S}; background:transparent;")
        rodape.setWordWrap(True)
        vl.addWidget(rodape)

    # ══════════════════════════════════════════════════════════════════════════
    # DADOS
    # ══════════════════════════════════════════════════════════════════════════

    def _carregar(self):
        """
        Carrega pedidos SOMENTE do banco de dados.

        Correção importante:
        - Antes esta tela varria a pasta de PDFs e montava a lista por arquivo.
        - Isso criava "pedido fantasma": PDF existia, mas o pedido não existia no banco.
        - Agora a tela lista apenas pedidos gravados na tabela pedidos.

        Resultado:
        - Botão Editar nunca aparece para pedido inexistente.
        - Relação de pedidos usa a mesma origem confiável: banco.
        - PDFs soltos na pasta não entram mais no financeiro.
        - Carrega somente o comprador atual (IURY ou THAMYRES).
        - Limita aos últimos 300 pedidos para evitar travamento.
        """
        self._todos = []
        os.makedirs(PEDIDOS_DIR, exist_ok=True)

        def _parse_data(data_txt):
            txt = str(data_txt or "").strip()
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(txt, fmt)
                except Exception:
                    pass
            return datetime.now()

        def _achar_pdf(numero, caminho_db):
            # Primeiro usa o caminho registrado no banco, se existir.
            caminho = str(caminho_db or "").strip()
            if caminho and os.path.exists(caminho):
                return caminho, os.path.basename(caminho)

            # Fallback: procura PDF com o número do pedido na pasta.
            # Isso NÃO cria pedido fantasma, porque só roda para pedido que já existe no banco.
            try:
                prefixo = f"PC-{numero}-".upper()
                for nome in os.listdir(PEDIDOS_DIR):
                    if nome.lower().endswith(".pdf") and nome.upper().startswith(prefixo):
                        caminho2 = os.path.join(PEDIDOS_DIR, nome)
                        if os.path.exists(caminho2):
                            return caminho2, nome
            except Exception:
                pass

            return "", f"PC-{numero}.pdf"

        try:
            from app.data.database import get_connection

            with get_connection() as conn:
                # MODO ADMIN:
                # Se COMPRADOR_PADRAO = "ADMIN", carrega TODOS os pedidos do banco.
                # Para qualquer outro comprador, mantém o filtro normal por comprador.
                comprador_atual = str(COMPRADOR_PADRAO or "").strip().upper()

                if comprador_atual == "ADMIN":
                    rows = conn.execute("""
                        SELECT
                            id,
                            numero,
                            data_pedido,
                            obra_nome,
                            fornecedor_nome,
                            fornecedor_razao,
                            empresa_faturadora,
                            condicao_pagamento,
                            forma_pagamento,
                            valor_total,
                            caminho_pdf,
                            comprador
                        FROM pedidos
                        ORDER BY CAST(numero AS INTEGER) DESC, id DESC
                    """).fetchall()
                else:
                    rows = conn.execute("""
                        SELECT
                            id,
                            numero,
                            data_pedido,
                            obra_nome,
                            fornecedor_nome,
                            fornecedor_razao,
                            empresa_faturadora,
                            condicao_pagamento,
                            forma_pagamento,
                            valor_total,
                            caminho_pdf,
                            comprador
                        FROM pedidos
                        WHERE UPPER(TRIM(COALESCE(comprador, ''))) = UPPER(TRIM(?))
                        ORDER BY CAST(numero AS INTEGER) DESC, id DESC
                        LIMIT 300
                    """, (comprador_atual,)).fetchall()

            for row in rows:
                numero = str(row["numero"] or "").strip()
                if not numero:
                    continue

                caminho, nome_pdf = _achar_pdf(numero, row["caminho_pdf"])
                data_dt = _parse_data(row["data_pedido"])
                empresa = str(row["empresa_faturadora"] or "—").upper()
                obra = str(row["obra_nome"] or "—")
                fornecedor = str(row["fornecedor_nome"] or row["fornecedor_razao"] or "—")

                try:
                    valor_total = float(row["valor_total"] or 0)
                except Exception:
                    valor_total = 0.0

                self._todos.append({
                    "id":                 row["id"],
                    "nome":               nome_pdf,
                    "caminho":            caminho,
                    "numero":             numero,
                    "obra":               obra,
                    "fornecedor":         fornecedor,
                    "empresa":            empresa,
                    "data":               data_dt,
                    "valor_total":        valor_total,
                    "empresa_faturadora": empresa,
                    "condicao_pagamento": row["condicao_pagamento"] or "—",
                    "forma_pagamento":    row["forma_pagamento"] or "—",
                    "obra_nome":          obra,
                    "fornecedor_nome":    fornecedor,
                    "comprador":          row["comprador"] or "",
                })

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao carregar pedidos",
                f"Não foi possível carregar os pedidos do banco.\n\n{e}"
            )

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
            fim = inicio + timedelta(days=6)
            resultado = [r for r in resultado if inicio <= r["data"].date() <= fim]
        elif self._filtro_ativo == "mes":
            resultado = [r for r in resultado if
                         r["data"].year == hoje.year and r["data"].month == hoje.month]
        elif self._filtro_ativo == "custom" and self._data_inicio and self._data_fim:
            resultado = [r for r in resultado if
                         self._data_inicio <= r["data"].date() <= self._data_fim]

        # Armazena resultado filtrado e reseta paginação
        self._filtrados    = resultado
        self._pagina_atual = 0
        self.tabela.setRowCount(0)
        self._renderizar_pagina()

    def _renderizar_pagina(self):
        """Renderiza a próxima fatia de _PAGE_SIZE registros na tabela."""
        inicio = self._pagina_atual * self._PAGE_SIZE
        fim    = inicio + self._PAGE_SIZE
        fatia  = self._filtrados[inicio:fim]

        self.tabela.setUpdatesEnabled(False)
        for dados in fatia:
            self._inserir_linha(dados)
        self.tabela.setUpdatesEnabled(True)

        self._pagina_atual += 1
        total    = len(self._filtrados)
        exibidos = min(self._pagina_atual * self._PAGE_SIZE, total)

        self._lbl_cont.setText(f"{total} pedido{'s' if total != 1 else ''}")
        self._lbl_pagina.setText(f"Exibindo {exibidos} de {total} pedidos")
        tem_mais = exibidos < total
        self._btn_mais.setVisible(tem_mais)
        if tem_mais:
            restantes = total - exibidos
            self._btn_mais.setText(f"⬇  Carregar mais {min(self._PAGE_SIZE, restantes)}")

        # Estado vazio
        if total == 0:
            self.tabela.setRowCount(1)
            self.tabela.setSpan(0, 0, 1, 6)
            it = QTableWidgetItem("Nenhum pedido encontrado.")
            it.setTextAlignment(Qt.AlignCenter)
            it.setForeground(QColor(TXT_S))
            self.tabela.setItem(0, 0, it)
            self._lbl_pagina.setText("")

    def _carregar_mais(self):
        """Carrega a próxima página de pedidos na tabela."""
        self._renderizar_pagina()

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

    def _inserir_linha(self, dados):
        """Insere uma única linha na tabela. Usado pela paginação."""
        r = self.tabela.rowCount()
        self.tabela.insertRow(r)
        self.tabela.setRowHeight(r, 92)
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
        vl_acoes = QVBoxLayout(cell)
        vl_acoes.setContentsMargins(10, 10, 10, 10)
        vl_acoes.setSpacing(10)

        num = dados["numero"]
        p = dados["caminho"]
        n = dados["nome"]
        pid = int(dados["id"])

        ba = btn_solid("📄 Abrir", BLUE, h=30)
        ba.setMinimumWidth(72)
        ba.clicked.connect(lambda _, x=p: self._abrir_pdf(x))

        be = btn_solid("💾 Exportar", GREEN, h=30)
        be.setMinimumWidth(88)
        be.clicked.connect(lambda _, x=p, y=n: self._exportar(x, y))

        br = btn_solid("🖨 Reimprimir", "#8E44AD", h=30)
        br.setMinimumWidth(100)
        br.setToolTip(f"Regera o PDF do pedido #{num}")
        br.clicked.connect(lambda _, x=num: self._reimprimir(x))

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.setContentsMargins(0, 0, 0, 0)
        row1.addWidget(ba)
        row1.addWidget(be)
        row1.addWidget(br)
        row1.addStretch(1)

        bed = btn_solid("✏️ Editar", "#F39C12", h=30)
        bed.setMinimumWidth(78)
        bed.setToolTip(f"Carrega o pedido #{num} na aba Pedido de Compra para edição")
        bed.clicked.connect(lambda _, x=num: self._editar_pedido(x))

        bpr = btn_solid("📅 Prazo obra", "#25D366", h=30)
        bpr.setMinimumWidth(104)
        bpr.setToolTip(
            "Gera imagem com prazo de entrega e itens para colar no WhatsApp (Ctrl+V)."
        )
        bpr.clicked.connect(lambda _, x=pid: self._gerar_imagem_prazo_obra(x))

        bx = btn_solid("🗑 Excluir", "#C0392B", h=30)
        bx.setMinimumWidth(82)
        bx.setToolTip(f"Remove o pedido #{num} do banco e da relação")
        bx.clicked.connect(lambda _, x=num: self._excluir_pedido(x))

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.setContentsMargins(0, 0, 0, 0)
        row2.addWidget(bed)
        row2.addWidget(bpr)
        row2.addWidget(bx)
        row2.addStretch(1)

        vl_acoes.addLayout(row1)
        vl_acoes.addLayout(row2)
        self.tabela.setCellWidget(r, 5, cell)

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
        if not caminho or not os.path.exists(caminho):
            QMessageBox.warning(
                self,
                "PDF não encontrado",
                "Este pedido existe no banco, mas o arquivo PDF não foi encontrado.\n\n"
                "Use o botão 'Reimprimir' para gerar o PDF novamente."
            )
            return
        try:
            if sys.platform == "win32":    os.startfile(caminho)
            elif sys.platform == "darwin": subprocess.run(["open", caminho])
            else:                          subprocess.run(["xdg-open", caminho])
        except Exception as e:
            QMessageBox.warning(self, "Erro ao abrir", str(e))

    def _exportar(self, caminho_origem, nome_arquivo):
        if not caminho_origem or not os.path.exists(caminho_origem):
            QMessageBox.warning(
                self,
                "PDF não encontrado",
                "Não encontrei o PDF deste pedido para exportar.\n\n"
                "Use 'Reimprimir' primeiro para gerar o arquivo novamente."
            )
            return

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

    def _excluir_pedido(self, numero):
        """
        Exclui um pedido do banco com confirmação.

        Importante:
        - Remove primeiro os itens vinculados em itens_pedido.
        - Depois remove o pedido da tabela pedidos.
        - Não apaga o PDF automaticamente; o PDF fica como arquivo histórico/backup.
        - Como a tela agora lista apenas banco, o pedido some da tela e das relações.
        """
        numero = str(numero).strip()

        resp = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja excluir o pedido #{numero}?\n\n"
            "Ele será removido do banco e não aparecerá mais em Pedidos Gerados nem nas Relações.\n\n"
            "O arquivo PDF não será apagado automaticamente.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if resp != QMessageBox.Yes:
            return

        try:
            from app.data.database import get_connection

            with get_connection() as conn:
                pedido = conn.execute(
                    "SELECT id, caminho_pdf FROM pedidos WHERE numero = ?",
                    (numero,)
                ).fetchone()

                if not pedido:
                    QMessageBox.information(
                        self,
                        "Pedido não encontrado",
                        f"O pedido #{numero} não existe mais no banco."
                    )
                    self._carregar()
                    return

                pedido_id = pedido["id"]

                conn.execute(
                    "DELETE FROM itens_pedido WHERE pedido_id = ?",
                    (pedido_id,)
                )
                conn.execute(
                    "DELETE FROM pedidos WHERE id = ?",
                    (pedido_id,)
                )

            try:
                from app.data.database import sincronizar_com_rede
                sincronizar_com_rede(silencioso=True)
            except Exception:
                pass

            QMessageBox.information(
                self,
                "Pedido excluído",
                f"Pedido #{numero} removido com sucesso.\n\n"
                "Ele não aparecerá mais na lista nem nas relações."
            )

            self._carregar()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao excluir pedido",
                f"Não foi possível excluir o pedido #{numero}.\n\n{e}"
            )

    def _gerar_imagem_prazo_obra(self, pedido_id: int):
        from app.infrastructure.prazo_entrega_imagem import gerar_imagem_prazo_entrega

        gerar_imagem_prazo_entrega(self, pedido_id)

    def _editar_pedido(self, numero):
        """
        Carrega um pedido já gerado de volta na aba Pedido de Compra.

        Regra desta primeira versão:
        - O pedido é aberto como edição usando o mesmo número.
        - Ao gerar novamente, o PedidoService atualiza o registro existente
          e recria os itens/PDF com os novos dados.
        """
        try:
            from app.data.database import get_connection

            with get_connection() as conn:
                pedido = conn.execute(
                    "SELECT * FROM pedidos WHERE numero = ?",
                    (str(numero),)
                ).fetchone()

                if not pedido:
                    QMessageBox.warning(
                        self,
                        "Pedido não encontrado",
                        f"Pedido #{numero} não foi encontrado no banco."
                    )
                    return

                itens = conn.execute(
                    """
                    SELECT descricao, quantidade, unidade, valor_unitario, valor_total, categoria
                    FROM itens_pedido
                    WHERE pedido_id = ?
                    ORDER BY id
                    """,
                    (pedido["id"],)
                ).fetchall()

            if not itens:
                resp = QMessageBox.question(
                    self,
                    "Pedido sem itens",
                    f"O pedido #{numero} não possui itens registrados.\n\n"
                    "Deseja abrir mesmo assim para edição?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if resp != QMessageBox.Yes:
                    return

            janela = self.window()
            pedido_widget = None

            if hasattr(janela, "_pages") and "pedido" in getattr(janela, "_pages", {}):
                pedido_widget = janela._pages["pedido"]
                if hasattr(janela, "_nav"):
                    janela._nav("pedido")
                elif hasattr(janela, "_stack"):
                    janela._stack.setCurrentWidget(pedido_widget)

            if pedido_widget is None or not hasattr(pedido_widget, "carregar_pedido_existente"):
                QMessageBox.warning(
                    self,
                    "Não foi possível editar",
                    "Não encontrei a aba Pedido de Compra para carregar este pedido."
                )
                return

            pedido_widget.carregar_pedido_existente(pedido, itens)

            QMessageBox.information(
                self,
                "Pedido carregado para edição",
                f"Pedido #{numero} carregado na aba Pedido de Compra.\n\n"
                "Faça os ajustes e clique novamente no botão da empresa para gerar o PDF atualizado."
            )

        except Exception as e:
            QMessageBox.critical(self, "Erro ao editar pedido", str(e))

    def _reimprimir(self, numero):
        # Busca os dados do pedido no banco e regera o PDF
        try:
            from app.data.database import get_connection
            from app.core.services.pedido_service import PedidoService
            from app.core.dto.pedido_dto import PedidoDTO, ItemPedidoDTO

            with get_connection() as conn:
                ped = conn.execute(
                    "SELECT * FROM pedidos WHERE numero = ?", (numero,)
                ).fetchone()
                if not ped:
                    QMessageBox.warning(self, "Não encontrado",
                        f"Pedido #{numero} não encontrado no banco.\n"
                        "Só é possível reimprimir pedidos gerados por este sistema.")
                    return

                itens_db = conn.execute(
                    "SELECT descricao, quantidade, unidade, valor_unitario "
                    "FROM itens_pedido WHERE pedido_id = ?", (ped["id"],)
                ).fetchall()

            itens = [
                ItemPedidoDTO(
                    descricao=i["descricao"],
                    quantidade=float(i["quantidade"] or 1),
                    unidade=i["unidade"] or "UNID.",
                    valor_unitario=float(i["valor_unitario"] or 0),
                )
                for i in itens_db
            ]

            if not itens:
                QMessageBox.warning(self, "Sem itens",
                    f"O pedido #{numero} não tem itens registrados no banco.")
                return

            dto = PedidoDTO(
                numero=str(ped["numero"]),
                data_pedido=str(ped["data_pedido"] or ""),
                empresa_faturadora=str(ped["empresa_faturadora"] or "BRASUL"),
                comprador=str(ped["comprador"] or ""),
                obra=str(ped["obra_nome"] or ""),
                escola=str(ped["escola"] or ""),
                endereco_entrega="", bairro_entrega="",
                cep_entrega="", cidade_entrega="", uf_entrega="SP",
                fornecedor_nome=str(ped["fornecedor_nome"] or ""),
                fornecedor_razao=str(ped["fornecedor_razao"] or ""),
                condicao_pagamento=str(ped["condicao_pagamento"] or ""),
                forma_pagamento=str(ped["forma_pagamento"] or ""),
                prazo_entrega=int(ped["prazo_entrega"] or 0),
                itens=itens,
            )

            service = PedidoService()
            path = service._generator.gerar(dto)

            msg = QMessageBox(self)
            msg.setWindowTitle(f"Pedido #{numero} reimpresso!")
            msg.setText(f"PDF gerado em:\n{path}")
            msg.setIcon(QMessageBox.Information)
            b_abrir = msg.addButton("📄 Abrir PDF", QMessageBox.ActionRole)
            msg.addButton("OK", QMessageBox.AcceptRole)
            msg.exec()
            if msg.clickedButton() == b_abrir:
                import os, sys, subprocess
                if sys.platform == "win32":
                    os.startfile(path)
                else:
                    subprocess.run(["xdg-open", path])
            self._carregar()

        except Exception as e:
            QMessageBox.critical(self, "Erro ao reimprimir", str(e))

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._carregar)