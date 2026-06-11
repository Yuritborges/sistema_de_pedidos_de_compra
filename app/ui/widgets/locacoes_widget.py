# app/ui/widgets/locacoes_widget.py
# Controle de locações — substitui uso diário da planilha Excel no sistema.
import os
import sys
from functools import partial
from datetime import datetime, date, timedelta

from PySide6.QtCore import Qt, QDate, QUrl, QTimer
from PySide6.QtWidgets import (
    QCompleter,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QComboBox,
    QDateEdit,
    QSpinBox,
    QGraphicsDropShadowEffect,
)

from PySide6.QtGui import QColor, QFont, QBrush, QDesktopServices, QPalette, QPen

from config import COMPRADOR_PADRAO
from app.data.database import (
    get_connection,
    get_locacoes_connection,
    init_locacoes_shared_db,
    list_fornecedores_nomes_para_locacao,
    list_obras_nomes_para_locacao,
    REDE_LOCACOES_DB_PATH,
)
from app.data.locacoes_import import (
    LOCACOES_DIAS_ALERTA_ANTECEDENCIA,
    calcular_derivados_locacao as _calcular_derivados,
    derivados_locacao_linha,
    clean_str as _clean,
    consume_last_sync_message,
    destaque_visual_linha_locacao_db,
    import_locacoes_into_connection,
    parse_periodo as _parse_periodo,
    registrar_planilha_na_meta,
    to_iso_date as _to_iso_date,
)
from app.ui.style import (
    BG,
    BDR,
    apply_completer_popup_style,
    CSS_BUSCA,
    CSS_COMBO,
    CSS_INPUT,
    TXT_S,
    TXT,
    RED,
    BLUE,
    GREEN,
    GRAY,
    WHITE,
    SEL,
    btn_outline,
    btn_solid,
    btn_filtro,
    make_card,
    card_container,
)

# Tabela escopada (#locacoes_tabela): fundo transparente nos itens para o delegate pintar a linha inteira.
LOC_TABLE_CSS = f"""
    QTableWidget#locacoes_tabela {{
        background:{WHITE};
        border:none;
        font-size:12px;
        color:{TXT};
        gridline-color:transparent;
        outline:none;
    }}
    QTableWidget#locacoes_tabela::item {{
        padding:8px 12px;
        border-bottom:1px solid #EDE8E8;
        background-color:transparent;
    }}
    QTableWidget#locacoes_tabela QHeaderView::section {{
        background-color:#2C3E50;
        color:{WHITE};
        font-size:10px;
        font-weight:bold;
        padding:12px 10px;
        border:none;
        border-right:1px solid #3D566E;
    }}
    QTableWidget#locacoes_tabela QHeaderView::section:last {{
        border-right:none;
    }}
    QTableWidget#locacoes_tabela QScrollBar:vertical {{
        background:transparent; width:7px; border-radius:4px; margin:4px 0;
    }}
    QTableWidget#locacoes_tabela QScrollBar::handle:vertical {{
        background:#C5BABA; border-radius:4px; min-height:36px;
    }}
    QTableWidget#locacoes_tabela QScrollBar::add-line:vertical,
    QTableWidget#locacoes_tabela QScrollBar::sub-line:vertical {{ height:0; }}
"""

# Vencido: mesmo critério do amarelo — fundo tintado + texto escuro (mais legível que branco em vermelho vivo).
ROW_BG_VENCIDO = QColor("#FFCDD2")
ROW_FG_VENCIDO = QColor("#212121")
ROW_BG_2DIAS = QColor("#FFEE58")
ROW_FG_2DIAS = QColor("#212121")

# Índices de colunas (PDF e botão não usam QTableWidgetItem)
COL_PDF = 5
COL_BOTAO_DEVOLVIDO = 11

# Delegate usa este papel para pintar linha inteira (evita conflito com QSS global do app)
ROLE_ROW_DESTAQUE = Qt.UserRole + 60


def _norm_destaque_tag(raw):
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="ignore")
    s = str(raw).strip().lower()
    if s in ("vencido", "dois_dias"):
        return s
    return None


class LocacoesTableDelegate(QStyledItemDelegate):
    """Garante fundo/texto das linhas VENCIDO e «2 dias» mesmo com stylesheet global."""

    def initStyleOption(self, option: QStyleOptionViewItem, index):
        super().initStyleOption(option, index)
        tag = _norm_destaque_tag(index.data(ROLE_ROW_DESTAQUE))
        sel = bool(option.state & QStyle.StateFlag.State_Selected)
        if tag == "vencido":
            bg = QColor("#EF9A9A") if sel else QColor("#FFCDD2")
            option.backgroundBrush = QBrush(bg)
            tx = QColor("#212121")
            option.palette.setColor(QPalette.ColorRole.Text, tx)
            option.palette.setColor(QPalette.ColorRole.Highlight, bg)
            option.palette.setColor(QPalette.ColorRole.HighlightedText, tx)
            option.showDecorationSelected = False
        elif tag == "dois_dias":
            bg = QColor("#F9A825") if sel else QColor("#FFEE58")
            option.backgroundBrush = QBrush(bg)
            option.palette.setColor(QPalette.ColorRole.Text, QColor("#212121"))
            option.palette.setColor(QPalette.ColorRole.Highlight, bg)
            option.palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#212121"))
            option.showDecorationSelected = False

    def paint(self, painter, option, index):
        """
        QSS global + Fusion ignoravam o brush do delegate; pintamos o fundo à mão e o texto com drawDisplay.
        showDecorationSelected=False evita faixa azul por cima da linha vencida ao selecionar.
        """
        tag = _norm_destaque_tag(index.data(ROLE_ROW_DESTAQUE))
        if tag not in ("vencido", "dois_dias"):
            super().paint(painter, option, index)
            return

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        painter.save()
        painter.fillRect(opt.rect, opt.backgroundBrush)
        opt.state &= ~QStyle.StateFlag.State_Selected
        opt.state &= ~QStyle.StateFlag.State_HasFocus
        w = opt.widget
        txt = (opt.text or "").strip()
        if not txt:
            txt = str(index.data(Qt.ItemDataRole.DisplayRole) or "").strip()
        if txt and w is not None:
            st = w.style()
            text_rect = st.subElementRect(QStyle.SubElement.SE_ItemViewItemText, opt, w)
            if not text_rect.isValid() or text_rect.width() < 4:
                text_rect = opt.rect.adjusted(12, 0, -12, 0)
            st.drawItemText(
                painter,
                text_rect,
                int(opt.displayAlignment),
                opt.palette,
                bool(opt.state & QStyle.StateFlag.State_Enabled),
                txt,
                QPalette.ColorRole.Text,
            )
        btm = QColor("#EDE8E8")
        if tag == "vencido":
            btm = QColor("#E57373")
        elif tag == "dois_dias":
            btm = QColor("#E6D358")
        painter.setPen(QPen(btm))
        painter.drawLine(opt.rect.left(), opt.rect.bottom(), opt.rect.right(), opt.rect.bottom())
        painter.restore()


def _pdf_btn_stylesheet(destaque, tem_pdf: bool) -> str:
    o = "outline:none;border:none;"
    if destaque == "vencido":
        if tem_pdf:
            return f"""
                QPushButton {{{o}
                    background:{WHITE};color:{RED};font-weight:bold;font-size:10px;
                    border-radius:5px;border:1px solid #E57373;
                }}
                QPushButton:hover {{ background:#FFEBEE;color:#922B21; }}
            """
        return f"""
            QPushButton {{{o}
                    background:{WHITE};color:{TXT_S};font-weight:bold;font-size:10px;
                    border-radius:5px;border:1px solid #E57373;
                }}
            QPushButton:hover {{ background:#FFF5F5;color:{TXT}; }}
        """
    if destaque == "dois_dias" and tem_pdf:
        return f"""
            QPushButton {{{o}
                background:{RED};color:white;font-weight:bold;font-size:10px;border-radius:5px;
            }}
            QPushButton:hover {{ background:#A93226; }}
        """
    if tem_pdf:
        return f"""
            QPushButton {{{o}
                background:{RED};color:white;font-weight:bold;font-size:10px;border-radius:5px;
            }}
            QPushButton:hover {{ background:#A93226; }}
        """
    return f"""
        QPushButton {{{o}
            background:#95A5A6;color:white;font-weight:bold;font-size:10px;border-radius:5px;
        }}
        QPushButton:hover {{ background:#7F8C8D; }}
    """


def _ok_btn_stylesheet(destaque) -> str:
    o = "outline:none;border:none;"
    if destaque == "vencido":
        return f"""
            QPushButton {{{o}
                background:{WHITE};color:{GREEN};font-weight:bold;font-size:11px;
                border-radius:5px;border:1px solid #E57373;
            }}
            QPushButton:hover {{ background:#E8F5E9; }}
        """
    return f"""
        QPushButton {{{o}
            background:{GREEN};color:white;font-weight:bold;font-size:11px;border-radius:5px;
        }}
        QPushButton:hover {{ background:#196F3D; }}
    """


def _iso_to_br(iso_val: str) -> str:
    txt = str(iso_val or "").strip()
    if not txt:
        return ""
    try:
        return datetime.strptime(txt[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return txt


def _br_to_iso(txt: str) -> str:
    txt = str(txt or "").strip()
    if not txt:
        return ""
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(txt[:10], fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return ""


def _compact_pedido_numero(txt: str) -> str:
    return "".join((txt or "").split())


def _formatar_item_pedido_locacao(descricao: str, quantidade, unidade: str) -> str:
    desc = _clean(descricao)
    if not desc:
        return ""
    try:
        qtd = float(quantidade or 0)
    except (TypeError, ValueError):
        qtd = 0.0
    un = _clean(unidade)
    if qtd > 0 and un:
        qtd_txt = f"{qtd:g}".replace(".", ",")
        return f"{qtd_txt} {un} — {desc}"
    return desc


def _buscar_pedido_locacao(numero_digitado: str) -> dict | None:
    """
    Localiza pedido na base do comprador atual e retorna cabeçalho + itens
    para preencher o cadastro de locação.
    """
    num = _clean(numero_digitado)
    if not num:
        return None
    cn = _compact_pedido_numero(num).upper()
    try:
        with get_connection() as conn:
            pedido = conn.execute(
                """
                SELECT id, numero, data_pedido, obra_nome, fornecedor_nome, comprador
                FROM pedidos
                WHERE TRIM(numero) = TRIM(?) COLLATE NOCASE
                LIMIT 1
                """,
                (num,),
            ).fetchone()
            if not pedido:
                for row in conn.execute(
                    """
                    SELECT id, numero, data_pedido, obra_nome, fornecedor_nome, comprador
                    FROM pedidos
                    """
                ):
                    if _compact_pedido_numero(_clean(row["numero"])).upper() == cn:
                        pedido = row
                        break
            if not pedido:
                return None

            itens_rows = conn.execute(
                """
                SELECT descricao, quantidade, unidade
                FROM itens_pedido
                WHERE pedido_id = ?
                ORDER BY id
                """,
                (pedido["id"],),
            ).fetchall()

        data_iso = _br_to_iso(_clean(pedido["data_pedido"]))
        itens = []
        for ir in itens_rows or ():
            desc = _clean(ir["descricao"])
            if not desc:
                continue
            itens.append({
                "descricao": desc,
                "quantidade": ir["quantidade"],
                "unidade": _clean(ir["unidade"]),
                "rotulo": _formatar_item_pedido_locacao(
                    desc, ir["quantidade"], ir["unidade"]
                ),
            })

        return {
            "numero": _clean(pedido["numero"]) or num,
            "obra": _clean(pedido["obra_nome"]),
            "fornecedor": _clean(pedido["fornecedor_nome"]),
            "comprador": _clean(pedido["comprador"]),
            "data_pedido_iso": data_iso,
            "itens": itens,
        }
    except Exception:
        return None


def _destaque_visual_linha_locacao(r):
    """Delega para o mesmo critério centralizado em locacoes_import."""
    return destaque_visual_linha_locacao_db(r)


def _hex_fundo_linha(destaque, zebra: QColor):
    if destaque == "vencido":
        return ROW_BG_VENCIDO.name()
    if destaque == "dois_dias":
        return ROW_BG_2DIAS.name()
    return zebra.name()


class LocacaoDialog(QDialog):
    """Cadastro / edição de uma linha de locação."""

    def __init__(self, dados=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Locação")
        self.setMinimumWidth(520)
        dados = dados or {}
        self._preserva_venc = _clean(dados.get("data_vencimento"))
        self.setStyleSheet(f"background:white; color:#222;")

        form = QFormLayout(self)

        self.e_obra = QComboBox()
        self.e_obra.setEditable(True)
        self.e_obra.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.e_obra.setMinimumHeight(32)
        obra_ini = _clean(dados.get("obra"))
        for nome in list_obras_nomes_para_locacao():
            self.e_obra.addItem(nome)
        if obra_ini:
            idx_sel = -1
            for i in range(self.e_obra.count()):
                if self.e_obra.itemText(i).strip().upper() == obra_ini.upper():
                    idx_sel = i
                    break
            if idx_sel >= 0:
                self.e_obra.setCurrentIndex(idx_sel)
            else:
                self.e_obra.setCurrentText(obra_ini)
        else:
            self.e_obra.setEditText("")

        comp_obra = QCompleter(self.e_obra.model())
        comp_obra.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp_obra.setFilterMode(Qt.MatchFlag.MatchContains)
        self.e_obra.setCompleter(comp_obra)
        apply_completer_popup_style(comp_obra)

        self.e_comprador = QComboBox()
        self.e_comprador.setEditable(True)
        for nome in ("IURY", "THAMYRES"):
            self.e_comprador.addItem(nome)
        comp = _clean(dados.get("comprador")) or COMPRADOR_PADRAO or "IURY"
        idx = self.e_comprador.findText(comp)
        if idx >= 0:
            self.e_comprador.setCurrentIndex(idx)
        else:
            self.e_comprador.setCurrentText(comp)

        ped_ini = _clean(dados.get("numero_pedido"))
        pdf_ini = _clean(dados.get("pedido_compra_numero"))
        ped_unificado = ped_ini or pdf_ini

        self.e_pedido = QLineEdit(ped_unificado)
        self.e_pedido_compra = QLineEdit(ped_unificado)
        self.e_pedido_compra.setReadOnly(True)
        self.e_pedido_compra.setPlaceholderText(
            "Espelho do «Nº pedido» — mesmo número usado para localizar o PDF"
        )
        self._timer_pedido_busca = QTimer(self)
        self._timer_pedido_busca.setSingleShot(True)
        self._timer_pedido_busca.setInterval(350)
        self._timer_pedido_busca.timeout.connect(self._preencher_do_pedido)
        self.e_pedido.textChanged.connect(self._on_pedido_text_changed)
        self.e_pedido.returnPressed.connect(self._pedido_tecla_enter)

        self.lbl_pedido_status = QLabel("")
        self.lbl_pedido_status.setStyleSheet(
            f"font-size:10px; color:{TXT_S}; background:transparent;"
        )
        self.lbl_pedido_status.setWordWrap(True)

        self.e_forn = QComboBox()
        self.e_forn.setEditable(True)
        self.e_forn.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.e_forn.setMinimumHeight(32)
        forn_ini = _clean(dados.get("fornecedor"))
        for nome in list_fornecedores_nomes_para_locacao():
            self.e_forn.addItem(nome)
        if forn_ini:
            idx_f = -1
            for i in range(self.e_forn.count()):
                if self.e_forn.itemText(i).strip().upper() == forn_ini.upper():
                    idx_f = i
                    break
            if idx_f >= 0:
                self.e_forn.setCurrentIndex(idx_f)
            else:
                self.e_forn.setCurrentText(forn_ini)
        else:
            self.e_forn.setEditText("")
        comp_forn = QCompleter(self.e_forn.model())
        comp_forn.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp_forn.setFilterMode(Qt.MatchFlag.MatchContains)
        self.e_forn.setCompleter(comp_forn)
        apply_completer_popup_style(comp_forn)

        self.e_item = QLineEdit(_clean(dados.get("item_locado")))

        self.e_item_pedido = QComboBox()
        self.e_item_pedido.setMinimumHeight(32)
        self.e_item_pedido.setStyleSheet(CSS_COMBO)
        self.e_item_pedido.setVisible(False)
        self.e_item_pedido.currentIndexChanged.connect(self._aplicar_item_pedido_escolhido)

        self.e_tipo = QComboBox()
        self.e_tipo.addItem("Obra / equipamento (período livre)", "")
        self.e_tipo.addItem("Caçamba (período em dias na obra — livre)", "CACAMBA")
        tipo_db = _clean(dados.get("tipo")).upper()
        ti = self.e_tipo.findData("CACAMBA")
        if tipo_db == "CACAMBA" and ti >= 0:
            self.e_tipo.setCurrentIndex(ti)

        self.e_data_ped = QDateEdit()
        self.e_data_ped.setCalendarPopup(True)
        self.e_data_ped.setDisplayFormat("dd/MM/yyyy")
        self.e_data_ped.setDate(QDate.currentDate())
        dp = _clean(dados.get("data_pedido"))
        if dp:
            iso = dp if len(dp) >= 10 and dp[4] == "-" else _br_to_iso(dp)
            if iso:
                qd = QDate.fromString(iso[:10], "yyyy-MM-dd")
                if qd.isValid():
                    self.e_data_ped.setDate(qd)

        self.e_periodo = QSpinBox()
        self.e_periodo.setRange(0, 3650)
        pd = dados.get("periodo_dias")
        if pd is not None and str(pd).strip() != "":
            try:
                self.e_periodo.setValue(int(float(pd)))
            except Exception:
                self.e_periodo.setValue(0)
        else:
            self.e_periodo.setValue(0)

        self.e_pedido_ok = QComboBox()
        self.e_pedido_ok.addItems(["Não", "OK"])
        pok = _clean(dados.get("pedido_ok")).upper()
        self.e_pedido_ok.setCurrentIndex(1 if pok == "OK" else 0)

        for w in (
            self.e_pedido,
            self.e_pedido_compra,
            self.e_item,
        ):
            w.setStyleSheet(CSS_INPUT)
        self.e_obra.setStyleSheet(CSS_COMBO)
        self.e_forn.setStyleSheet(CSS_COMBO)
        self.e_comprador.setStyleSheet(CSS_COMBO)
        self.e_pedido_ok.setStyleSheet(CSS_COMBO)
        self.e_tipo.setStyleSheet(CSS_COMBO)
        self.e_tipo.currentIndexChanged.connect(self._ajustar_periodo_por_tipo)

        self._lbl_item_pedido = QLabel("Item do pedido")
        form.addRow("Nº pedido", self.e_pedido)
        form.addRow("", self.lbl_pedido_status)
        form.addRow(self._lbl_item_pedido, self.e_item_pedido)
        form.addRow("Item locado", self.e_item)
        form.addRow("Obra", self.e_obra)
        form.addRow("Comprador", self.e_comprador)
        form.addRow("Fornecedor", self.e_forn)
        form.addRow("Pedido de compra (PDF)", self.e_pedido_compra)
        form.addRow("Tipo", self.e_tipo)
        form.addRow("Data pedido", self.e_data_ped)
        form.addRow("Período (dias na obra)", self.e_periodo)
        form.addRow("Pedido OK (encerrado)", self.e_pedido_ok)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        for role in (
            QDialogButtonBox.StandardButton.Ok,
            QDialogButtonBox.StandardButton.Cancel,
        ):
            btn = bb.button(role)
            if btn is not None:
                btn.setAutoDefault(False)
                btn.setDefault(False)
        form.addRow(bb)

        self._ajustar_periodo_por_tipo()
        self._ultimo_pedido_carregado = ""
        if ped_unificado:
            QTimer.singleShot(0, self._preencher_do_pedido)
        else:
            self.e_pedido.setFocus()

    def _reset_campos_vinculados_pedido(self):
        """Zera campos preenchidos automaticamente pelo nº do pedido."""
        self.e_item.clear()
        self._limpar_seletor_itens_pedido()
        self.e_obra.setEditText("")
        self.e_forn.setEditText("")
        comp = _clean(COMPRADOR_PADRAO) or "IURY"
        idx = self.e_comprador.findText(comp)
        if idx >= 0:
            self.e_comprador.setCurrentIndex(idx)
        else:
            self.e_comprador.setCurrentText(comp)
        self.e_data_ped.setDate(QDate.currentDate())
        self.e_tipo.setCurrentIndex(0)
        self.e_periodo.setValue(0)
        self._ajustar_periodo_por_tipo()

    def _on_pedido_text_changed(self, texto: str):
        self.e_pedido_compra.setText(texto)
        num = texto.strip()
        if not num:
            self._timer_pedido_busca.stop()
            self.lbl_pedido_status.setText("")
            self._ultimo_pedido_carregado = ""
            self._reset_campos_vinculados_pedido()
            return
        if self._ultimo_pedido_carregado and num != self._ultimo_pedido_carregado:
            self._reset_campos_vinculados_pedido()
            self._ultimo_pedido_carregado = ""
        if num != self._ultimo_pedido_carregado:
            self._timer_pedido_busca.start()

    def _pedido_tecla_enter(self):
        """Enter no nº pedido: busca agora e avança o foco — não salva o diálogo."""
        self._timer_pedido_busca.stop()
        self._ultimo_pedido_carregado = ""
        self._preencher_do_pedido(forcar=True)
        if self.e_item_pedido.isVisible():
            self.e_item_pedido.setFocus()
        else:
            self.e_periodo.setFocus()

    def _set_combo_text_insensitive(self, combo: QComboBox, texto: str):
        txt = _clean(texto)
        if not txt:
            return
        for i in range(combo.count()):
            if combo.itemText(i).strip().upper() == txt.upper():
                combo.setCurrentIndex(i)
                return
        combo.setCurrentText(txt)

    def _sugerir_tipo_por_item(self, descricao: str):
        low = (descricao or "").lower()
        if "caçamba" in low or "cacamba" in low:
            ti = self.e_tipo.findData("CACAMBA")
            if ti >= 0:
                self.e_tipo.setCurrentIndex(ti)

    def _limpar_seletor_itens_pedido(self):
        self.e_item_pedido.blockSignals(True)
        self.e_item_pedido.clear()
        self.e_item_pedido.setVisible(False)
        self.e_item_pedido.blockSignals(False)
        if getattr(self, "_lbl_item_pedido", None) is not None:
            self._lbl_item_pedido.setVisible(False)

    def _popular_itens_do_pedido(self, itens: list, item_atual: str = ""):
        self._limpar_seletor_itens_pedido()
        if not itens:
            return

        item_atual_n = _clean(item_atual).upper()
        if len(itens) == 1:
            desc = itens[0]["descricao"]
            self.e_item.setText(desc)
            self._sugerir_tipo_por_item(desc)
            return

        self.e_item_pedido.blockSignals(True)
        self.e_item_pedido.setVisible(True)
        if getattr(self, "_lbl_item_pedido", None) is not None:
            self._lbl_item_pedido.setVisible(True)
        idx_sel = 0
        for i, it in enumerate(itens):
            self.e_item_pedido.addItem(it["rotulo"], it["descricao"])
            if item_atual_n and it["descricao"].upper() == item_atual_n:
                idx_sel = i
        self.e_item_pedido.setCurrentIndex(idx_sel)
        self.e_item_pedido.blockSignals(False)
        self._aplicar_item_pedido_escolhido(idx_sel)

    def _aplicar_item_pedido_escolhido(self, index: int):
        if index < 0 or not self.e_item_pedido.isVisible():
            return
        desc = self.e_item_pedido.itemData(index)
        if desc:
            self.e_item.setText(str(desc))
            self._sugerir_tipo_por_item(str(desc))

    def _preencher_do_pedido(self, forcar: bool = False):
        num = self.e_pedido.text().strip()
        if not num:
            self.lbl_pedido_status.setText("")
            self._ultimo_pedido_carregado = ""
            self._reset_campos_vinculados_pedido()
            return
        if not forcar and len(num) < 3:
            self.lbl_pedido_status.setText("")
            return
        if num == getattr(self, "_ultimo_pedido_carregado", ""):
            return

        dados = _buscar_pedido_locacao(num)
        if not dados:
            self.lbl_pedido_status.setText(
                "Pedido não encontrado na base — preencha os campos manualmente."
            )
            self._reset_campos_vinculados_pedido()
            return

        self._ultimo_pedido_carregado = num
        if dados["numero"] and dados["numero"] != num:
            self.e_pedido.blockSignals(True)
            self.e_pedido.setText(dados["numero"])
            self.e_pedido.blockSignals(False)
            self.e_pedido_compra.setText(dados["numero"])

        if dados.get("obra"):
            self._set_combo_text_insensitive(self.e_obra, dados["obra"])
        if dados.get("fornecedor"):
            self._set_combo_text_insensitive(self.e_forn, dados["fornecedor"])
        if dados.get("comprador"):
            self._set_combo_text_insensitive(self.e_comprador, dados["comprador"])

        iso = dados.get("data_pedido_iso") or ""
        if iso:
            qd = QDate.fromString(iso[:10], "yyyy-MM-dd")
            if qd.isValid():
                self.e_data_ped.setDate(qd)

        n_itens = len(dados.get("itens") or [])
        if n_itens:
            self.lbl_pedido_status.setText(
                f"Pedido {dados['numero']} encontrado — {n_itens} item(ns) no pedido."
            )
            self._popular_itens_do_pedido(dados["itens"], self.e_item.text().strip())
        else:
            self.lbl_pedido_status.setText(
                f"Pedido {dados['numero']} encontrado — sem itens cadastrados."
            )
            self._limpar_seletor_itens_pedido()

    def _ajustar_periodo_por_tipo(self):
        # Mesmo intervalo para todos os tipos: caçambas podem ficar 7, 10+ dias na obra.
        self.e_periodo.setRange(0, 3650)
        if self.e_tipo.currentData() == "CACAMBA":
            self.e_periodo.setToolTip(
                "Dias que a caçamba permanece na obra (ex.: 3, 7, 10). "
                "Use 0 se quiser só controlar pela data de vencimento manual."
            )
        else:
            self.e_periodo.setToolTip("")

    def resultado(self):
        d = self.e_data_ped.date()
        data_pedido = d.toPython().strftime("%Y-%m-%d") if d.isValid() else ""
        per = self.e_periodo.value()
        periodo = None if per <= 0 else per
        pok_db = "OK" if self.e_pedido_ok.currentIndex() == 1 else ""

        venc_iso, dias, situacao = _calcular_derivados(
            data_pedido,
            periodo if periodo is not None else "",
            self._preserva_venc,
            pok_db,
        )
        np = self.e_pedido.text().strip()
        return {
            "obra": self.e_obra.currentText().strip(),
            "comprador": self.e_comprador.currentText().strip().upper(),
            "numero_pedido": np,
            "pedido_compra_numero": np,
            "fornecedor": self.e_forn.currentText().strip(),
            "item_locado": self.e_item.text().strip(),
            "tipo": (self.e_tipo.currentData() or "").strip(),
            "data_pedido": data_pedido,
            "periodo_dias": periodo,
            "data_vencimento": venc_iso,
            "dias_a_vencer": dias,
            "situacao": situacao,
            "pedido_ok": pok_db,
        }


class LocacoesWidget(QWidget):
    """Lista locações com lógica semelhante à planilha LANÇAMENTO + filtros."""

    def __init__(self):
        super().__init__()
        init_locacoes_shared_db()
        self._usuario = (COMPRADOR_PADRAO or "USUARIO").strip().upper()
        self._todos = []
        self._filtrados = []
        self._filtro_preset = "todos"
        self._pending_sync_notice = None
        self._ultima_data_recalculo = date.today()
        self._build()
        self._start_auto_refresh_timer()
        self._pending_sync_notice = consume_last_sync_message()
        self._carregar()

    def _build(self):
        self.setStyleSheet(f"background:{BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Cabeçalho ─────────────────────────────────────────────
        hl_topo = QHBoxLayout()
        hl_topo.setSpacing(14)
        titulo = QLabel("Locações")
        titulo.setStyleSheet(
            f"font-size:22px; font-weight:bold; color:{GRAY}; background:transparent;"
        )
        hl_topo.addWidget(titulo, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"background:{BDR}; margin:4px 4px;")
        sep.setFixedWidth(1)
        hl_topo.addWidget(sep)

        self.btn_novo = btn_solid("+ Novo", GREEN)
        self.btn_novo.setToolTip("Cadastrar nova locação")
        self.btn_novo.clicked.connect(self._novo)
        hl_topo.addWidget(self.btn_novo)

        self.btn_editar = btn_outline("✏ Editar")
        self.btn_editar.clicked.connect(self._editar_selecionado)
        hl_topo.addWidget(self.btn_editar)

        self.btn_excluir = btn_outline("🗑 Excluir")
        self.btn_excluir.clicked.connect(self._excluir_selecionado)
        hl_topo.addWidget(self.btn_excluir)

        self.btn_recalc = btn_outline("↻ Recalcular")
        self.btn_recalc.setToolTip(
            "Atualiza vencimento, dias e situação de todos os registros."
        )
        self.btn_recalc.clicked.connect(self._recalcular_tudo)
        hl_topo.addWidget(self.btn_recalc)

        self.btn_importar = btn_solid("📥 Excel", RED)
        self.btn_importar.setToolTip(
            "Substituir ou acrescentar a partir de outro arquivo Excel (.xlsm / .xlsx). "
            "O fluxo normal é ler só o banco; import só quando mudar de arquivo ou mesclar."
        )
        self.btn_importar.clicked.connect(self._importar_excel)
        hl_topo.addWidget(self.btn_importar)

        self.btn_atualizar = btn_solid("⟳ Atualizar", "#95A5A6")
        self.btn_atualizar.clicked.connect(self._carregar)
        hl_topo.addWidget(self.btn_atualizar)
        root.addLayout(hl_topo)

        # ── Cards resumo ────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        self._card_total, self._lv_kpi_total = make_card("TOTAL", "—", "#34495E")
        self._card_venc, self._lv_kpi_venc = make_card("VENCIDOS", "—", RED)
        self._card_alert, self._lv_kpi_alert = make_card("ALERTA DE VENCIMENTO", "—", "#E67E22")
        self._card_obra, self._lv_kpi_obra = make_card("NA OBRA", "—", GREEN)
        self._card_ok, self._lv_kpi_ok = make_card("ENCERRADOS", "—", "#7F8C8D")
        for w in (
            self._card_total,
            self._card_venc,
            self._card_alert,
            self._card_obra,
            self._card_ok,
        ):
            cards_row.addWidget(w)
        cards_row.addStretch()
        root.addLayout(cards_row)

        # ── Filtros rápidos ────────────────────────────────────────
        hl_f = QHBoxLayout()
        lf = QLabel("Visão rápida")
        lf.setStyleSheet(
            f"font-size:10px; font-weight:bold; color:{TXT_S}; "
            f"background:transparent; letter-spacing:1px;"
        )
        hl_f.addWidget(lf)
        hl_f.setSpacing(8)
        self._btn_presets = {}
        for chave, rotulo in [
            ("todos", "Todos"),
            ("vencido", "Vencidos"),
            ("atualizar", "Vencendo"),
            ("na_obra", "Na obra"),
            ("ok", "Encerrados"),
        ]:
            b = btn_filtro(rotulo)
            b.clicked.connect(lambda _, k=chave: self._set_preset(k))
            hl_f.addWidget(b)
            self._btn_presets[chave] = b
        hl_f.addStretch()
        root.addLayout(hl_f)

        hl_janela = QHBoxLayout()
        lj = QLabel("Grade por vencimento")
        lj.setStyleSheet(
            f"font-size:10px; font-weight:bold; color:{TXT_S}; "
            f"background:transparent; letter-spacing:1px;"
        )
        hl_janela.addWidget(lj)
        self.combo_janela_venc = QComboBox()
        self.combo_janela_venc.setStyleSheet(CSS_COMBO)
        self.combo_janela_venc.setMinimumWidth(300)
        self.combo_janela_venc.addItem("Todos (sem filtro de data)", None)
        self.combo_janela_venc.addItem("Janela ±30 dias (recomendado)", 30)
        self.combo_janela_venc.addItem("Janela ±60 dias", 60)
        self.combo_janela_venc.addItem("Janela ±90 dias", 90)
        self.combo_janela_venc.setCurrentIndex(1)
        self.combo_janela_venc.currentIndexChanged.connect(lambda _: self._aplicar_filtro())
        hl_janela.addWidget(self.combo_janela_venc)
        lj_hint = QLabel(
            "Mostra linhas cuja data de vencimento ou de pedido cai na janela em torno de hoje. "
            "Itens VENCIDOS sempre aparecem."
        )
        lj_hint.setStyleSheet(f"font-size:10px; color:{TXT_S}; background:transparent;")
        lj_hint.setWordWrap(True)
        hl_janela.addWidget(lj_hint, 1)
        root.addLayout(hl_janela)

        # ── Busca ───────────────────────────────────────────────────
        hl_busca = QHBoxLayout()
        hl_busca.setSpacing(10)
        busca_wrap = QWidget()
        busca_wrap.setFixedHeight(36)
        busca_wrap.setMinimumWidth(320)
        bwl = QHBoxLayout(busca_wrap)
        bwl.setContentsMargins(0, 0, 0, 0)
        self.e_busca = QLineEdit()
        self.e_busca.setPlaceholderText(
            "Buscar obra, comprador, pedido, fornecedor, item, tipo ou situação..."
        )
        self.e_busca.setStyleSheet(CSS_BUSCA)
        self.e_busca.textChanged.connect(self._aplicar_filtro)
        self.e_busca.returnPressed.connect(self._aplicar_filtro)
        bwl.addWidget(self.e_busca)
        ico = QLabel("🔍")
        ico.setStyleSheet("background:transparent; font-size:14px; border:none;")
        ico.setFixedWidth(30)
        ico.setParent(busca_wrap)
        ico.move(8, 9)
        ico.raise_()
        hl_busca.addWidget(busca_wrap, 1)
        bt = btn_solid("Pesquisar", BLUE, h=34)
        bt.clicked.connect(self._aplicar_filtro)
        hl_busca.addWidget(bt)
        root.addLayout(hl_busca)

        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet(
            f"font-size:11px; color:{TXT_S}; background:transparent; padding-left:4px;"
        )
        root.addWidget(self.lbl_info)

        # ── Tabela em card com sombra ───────────────────────────────
        container = card_container()
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(22)
        sombra.setOffset(0, 3)
        sombra.setColor(QColor(0, 0, 0, 26))
        container.setGraphicsEffect(sombra)
        cv = QVBoxLayout(container)
        cv.setContentsMargins(0, 12, 0, 12)

        self.tabela = QTableWidget(0, 12)
        self.tabela.setObjectName("locacoes_tabela")
        self.tabela.setHorizontalHeaderLabels([
            "Obra",
            "Comprador",
            "Nº Pedido",
            "Fornecedor",
            "Item locado",
            "PDF",
            "Data pedido",
            "Período",
            "Vencimento",
            "Dias",
            "Situação",
            "Pedido OK",
        ])
        self.tabela.setStyleSheet(LOC_TABLE_CSS)
        self.tabela.setItemDelegate(LocacoesTableDelegate(self.tabela))
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setShowGrid(False)
        self.tabela.setAlternatingRowColors(False)
        self.tabela.cellDoubleClicked.connect(self._on_double_click)
        hh = self.tabela.horizontalHeader()
        hh.setHighlightSections(False)
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Fixed)
        hh.setSectionResizeMode(2, QHeaderView.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.Fixed)
        for col in range(6, 12):
            hh.setSectionResizeMode(col, QHeaderView.Fixed)
        self.tabela.setColumnWidth(1, 96)
        self.tabela.setColumnWidth(2, 82)
        self.tabela.setColumnWidth(COL_PDF, 84)
        self.tabela.setColumnWidth(6, 96)
        self.tabela.setColumnWidth(7, 64)
        self.tabela.setColumnWidth(8, 96)
        self.tabela.setColumnWidth(9, 56)
        self.tabela.setColumnWidth(10, 108)
        self.tabela.setColumnWidth(COL_BOTAO_DEVOLVIDO, 172)
        cv.addWidget(self.tabela)
        root.addWidget(container, 1)

        rodape = QLabel(f"Base compartilhada na rede: {REDE_LOCACOES_DB_PATH}")
        rodape.setStyleSheet(f"font-size:10px; color:{TXT_S}; background:transparent;")
        rodape.setWordWrap(True)
        root.addWidget(rodape)

        self._set_preset("todos")

    def _start_auto_refresh_timer(self):
        """
        Mantém «Dias» e «Situação» atualizados mesmo se o sistema ficar aberto
        por longos períodos (virada de dia).
        """
        self._timer_auto_refresh = QTimer(self)
        # 60s é leve para ~centenas de linhas e evita números "congelados".
        self._timer_auto_refresh.setInterval(60 * 1000)
        self._timer_auto_refresh.timeout.connect(self._refresh_derivados_se_necessario)
        self._timer_auto_refresh.start()

    def _refresh_derivados_se_necessario(self):
        """
        Recalcula em memória quando o dia muda, sem gravar no banco
        (o banco já sincroniza em _carregar/_recalcular_tudo).
        """
        hoje = date.today()
        if hoje == self._ultima_data_recalculo:
            return
        self._ultima_data_recalculo = hoje
        alterou = False
        for r in self._todos:
            venc, dias, sit = derivados_locacao_linha(r)
            if (
                venc != str(r.get("data_vencimento", ""))
                or str(dias) != str(r.get("dias_a_vencer", ""))
                or sit != str(r.get("situacao", ""))
            ):
                r["data_vencimento"] = venc
                r["dias_a_vencer"] = dias
                r["situacao"] = sit
                alterou = True
        if alterou:
            self._atualizar_kpis()
            self._aplicar_filtro()

    def _atualizar_kpis(self):
        if not getattr(self, "_lv_kpi_total", None):
            return
        rows = self._todos
        n = len(rows)

        def sit_upper(r):
            return str(r.get("situacao", "")).strip().upper()

        venc = sum(1 for r in rows if destaque_visual_linha_locacao_db(r) == "vencido")
        alert = sum(1 for r in rows if destaque_visual_linha_locacao_db(r) == "dois_dias")
        obra = sum(1 for r in rows if sit_upper(r) == "NA OBRA")
        ok = sum(
            1 for r in rows
            if sit_upper(r) == "OK" or str(r.get("pedido_ok", "")).strip().upper() == "OK"
        )

        self._lv_kpi_total.setText(str(n))
        self._lv_kpi_venc.setText(str(venc))
        self._lv_kpi_alert.setText(str(alert))
        self._lv_kpi_obra.setText(str(obra))
        self._lv_kpi_ok.setText(str(ok))

    def _set_preset(self, chave):
        self._filtro_preset = chave
        for k, b in self._btn_presets.items():
            b.setChecked(k == chave)
        self._aplicar_filtro()

    def _on_double_click(self, row, col):
        if col in (COL_PDF, COL_BOTAO_DEVOLVIDO):
            return
        self._editar_linha(row)

    def _id_linha(self, row_idx):
        it = self.tabela.item(row_idx, 0)
        if not it:
            return None
        return it.data(Qt.UserRole)

    def _tentar_travar_registro(self, oid: int, timeout_s: int = 90):
        """
        Trava leve por registro:
        - permite editar se não estiver travado;
        - trava antiga (> timeout_s) expira automaticamente;
        - mesmo usuário pode retomar.
        """
        with get_locacoes_connection() as conn:
            conn.execute(
                """
                UPDATE locacoes_registros
                   SET editando_por = ?, editando_desde = datetime('now')
                 WHERE id = ?
                   AND (
                        COALESCE(editando_por, '') = ''
                        OR UPPER(editando_por) = ?
                        OR (julianday('now') - julianday(COALESCE(editando_desde, datetime('now','-365 day')))) * 86400 > ?
                   )
                """,
                (self._usuario, oid, self._usuario, timeout_s),
            )
            ok = conn.total_changes > 0
            if ok:
                return True, ""
            row = conn.execute(
                "SELECT editando_por, editando_desde FROM locacoes_registros WHERE id=?",
                (oid,),
            ).fetchone()
            dono = _clean(row["editando_por"]) if row else ""
            desde = _clean(row["editando_desde"]) if row else ""
            return False, f"{dono} ({desde})".strip()

    def _liberar_trava(self, oid: int):
        with get_locacoes_connection() as conn:
            conn.execute(
                """
                UPDATE locacoes_registros
                   SET editando_por = NULL, editando_desde = NULL
                 WHERE id = ? AND (UPPER(COALESCE(editando_por,'')) = ? OR COALESCE(editando_por,'') = '')
                """,
                (oid, self._usuario),
            )

    def _novo(self):
        dlg = LocacaoDialog(parent=self)
        if dlg.exec() != QDialog.Accepted:
            return
        dados = dlg.resultado()
        if not dados.get("obra") and not dados.get("numero_pedido"):
            QMessageBox.warning(self, "Validação", "Informe pelo menos obra ou nº do pedido.")
            return
        try:
            with get_locacoes_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO locacoes_registros (
                        obra, comprador, numero_pedido, fornecedor, item_locado, tipo,
                        pedido_compra_numero,
                        data_pedido, periodo_dias, data_vencimento, dias_a_vencer,
                        situacao, pedido_ok, origem_planilha, atualizado_em
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """,
                    (
                        dados["obra"],
                        dados["comprador"],
                        dados["numero_pedido"],
                        dados["fornecedor"],
                        dados["item_locado"],
                        dados.get("tipo") or "",
                        dados.get("pedido_compra_numero") or "",
                        dados["data_pedido"],
                        dados["periodo_dias"],
                        dados["data_vencimento"],
                        dados["dias_a_vencer"],
                        dados["situacao"],
                        dados["pedido_ok"],
                        "",
                    ),
                )
            self._carregar()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _editar_selecionado(self):
        r = self.tabela.currentRow()
        if r < 0:
            QMessageBox.information(self, "Seleção", "Selecione uma linha para editar.")
            return
        self._editar_linha(r)

    def _editar_linha(self, row_idx):
        oid = self._id_linha(row_idx)
        if oid is None:
            return
        row_db = next((x for x in self._todos if x.get("id") == oid), None)
        if not row_db:
            self._carregar()
            row_db = next((x for x in self._todos if x.get("id") == oid), None)
        if not row_db:
            return
        ok, dono = self._tentar_travar_registro(oid)
        if not ok:
            QMessageBox.warning(
                self,
                "Registro em uso",
                "Este registro está sendo editado por outro usuário.\n\n"
                f"{dono}\n\n"
                "Aguarde alguns segundos e tente novamente.",
            )
            return
        dlg = LocacaoDialog(dados=row_db, parent=self)
        if dlg.exec() != QDialog.Accepted:
            self._liberar_trava(oid)
            return
        dados = dlg.resultado()
        try:
            with get_locacoes_connection() as conn:
                row_v = conn.execute(
                    "SELECT versao FROM locacoes_registros WHERE id=?",
                    (oid,),
                ).fetchone()
                versao_atual = int(row_v["versao"]) if row_v else 0
                cur = conn.execute(
                    """
                    UPDATE locacoes_registros SET
                        obra=?, comprador=?, numero_pedido=?, fornecedor=?, item_locado=?,
                        tipo=?, pedido_compra_numero=?,
                        data_pedido=?, periodo_dias=?, data_vencimento=?, dias_a_vencer=?,
                        situacao=?, pedido_ok=?, versao=versao+1,
                        editando_por=NULL, editando_desde=NULL,
                        atualizado_em=datetime('now')
                    WHERE id=? AND versao=?
                    """,
                    (
                        dados["obra"],
                        dados["comprador"],
                        dados["numero_pedido"],
                        dados["fornecedor"],
                        dados["item_locado"],
                        dados.get("tipo") or "",
                        dados.get("pedido_compra_numero") or "",
                        dados["data_pedido"],
                        dados["periodo_dias"],
                        dados["data_vencimento"],
                        dados["dias_a_vencer"],
                        dados["situacao"],
                        dados["pedido_ok"],
                        oid,
                        versao_atual,
                    ),
                )
                if cur.rowcount == 0:
                    self._liberar_trava(oid)
                    QMessageBox.warning(
                        self,
                        "Conflito de edição",
                        "Esse registro foi alterado por outro usuário enquanto você editava.\n"
                        "A tela será recarregada para evitar sobrescrita.",
                    )
                    self._carregar()
                    return
            self._carregar()
        except Exception as e:
            self._liberar_trava(oid)
            QMessageBox.critical(self, "Erro", str(e))

    def _excluir_selecionado(self):
        r = self.tabela.currentRow()
        if r < 0:
            QMessageBox.information(self, "Seleção", "Selecione uma linha para excluir.")
            return
        oid = self._id_linha(r)
        if oid is None:
            return
        if QMessageBox.question(
            self,
            "Confirmar",
            "Excluir este registro de locação?",
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        try:
            ok, dono = self._tentar_travar_registro(oid)
            if not ok:
                QMessageBox.warning(
                    self,
                    "Registro em uso",
                    "Não foi possível excluir porque outro usuário está editando este registro.\n\n"
                    f"{dono}",
                )
                return
            with get_locacoes_connection() as conn:
                conn.execute("DELETE FROM locacoes_registros WHERE id=?", (oid,))
            self._carregar()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _recalcular_tudo(self):
        try:
            with get_locacoes_connection() as conn:
                rows = conn.execute(
                    "SELECT id, data_pedido, periodo_dias, data_vencimento, pedido_ok FROM locacoes_registros"
                ).fetchall()
                for r in rows:
                    venc, dias, sit = _calcular_derivados(
                        r["data_pedido"],
                        r["periodo_dias"],
                        r["data_vencimento"],
                        r["pedido_ok"],
                    )
                    conn.execute(
                        """
                        UPDATE locacoes_registros SET
                            data_vencimento=?, dias_a_vencer=?, situacao=?,
                            atualizado_em=datetime('now')
                        WHERE id=?
                        """,
                        (venc, dias, sit, r["id"]),
                    )
            self._carregar()
            QMessageBox.information(self, "Recálculo", "Todos os registros foram atualizados.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _importar_excel(self):
        modo = QMessageBox.question(
            self,
            "Importar Excel",
            "Substituir todos os registros existentes?\n\n"
            "Sim = apaga a base atual e importa de novo (ideal na primeira migração).\n"
            "Não = apenas acrescenta linhas no final.",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
        )
        if modo == QMessageBox.Cancel:
            return
        substituir = modo == QMessageBox.Yes

        arq, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar planilha de locações",
            os.getcwd(),
            "Planilhas (*.xlsm *.xlsx *.xls)",
        )
        if not arq:
            return

        try:
            with get_locacoes_connection() as conn:
                inseridos = import_locacoes_into_connection(conn, arq, substituir)
                registrar_planilha_na_meta(conn, arq)

            self._carregar()
            QMessageBox.information(
                self,
                "Importação concluída",
                f"{inseridos} registros importados."
                + (" (base anterior substituída.)" if substituir else ""),
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro ao importar", f"Falha na importação:\n\n{e}")

    def _carregar(self, notificar_sidebar: bool = True):
        self._todos = []
        try:
            with get_locacoes_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT
                        id, obra, comprador, numero_pedido, fornecedor, item_locado,
                        tipo, pedido_compra_numero,
                        data_pedido, periodo_dias, data_vencimento, dias_a_vencer,
                        situacao, pedido_ok
                    FROM locacoes_registros
                    """
                ).fetchall()
                atualizar_bd = []
                for r in rows:
                    base = {
                        "id": r["id"],
                        "obra": _clean(r["obra"]),
                        "comprador": _clean(r["comprador"]),
                        "numero_pedido": _clean(r["numero_pedido"]),
                        "fornecedor": _clean(r["fornecedor"]),
                        "item_locado": _clean(r["item_locado"]),
                        "tipo": _clean(r["tipo"]),
                        "pedido_compra_numero": _clean(r["pedido_compra_numero"]),
                        "data_pedido": _clean(r["data_pedido"]),
                        "periodo_dias": r["periodo_dias"],
                        "data_vencimento": _clean(r["data_vencimento"]),
                        "dias_a_vencer": _clean(r["dias_a_vencer"]),
                        "situacao": _clean(r["situacao"]),
                        "pedido_ok": _clean(r["pedido_ok"]),
                    }
                    venc, dias, sit = derivados_locacao_linha(base)
                    if (
                        venc != base["data_vencimento"]
                        or dias != base["dias_a_vencer"]
                        or sit != base["situacao"]
                    ):
                        atualizar_bd.append((venc, dias, sit, r["id"]))
                    base["data_vencimento"] = venc
                    base["dias_a_vencer"] = dias
                    base["situacao"] = sit
                    self._todos.append(base)
                if atualizar_bd:
                    for venc, dias, sit, oid in atualizar_bd:
                        conn.execute(
                            """
                            UPDATE locacoes_registros SET
                                data_vencimento=?, dias_a_vencer=?, situacao=?,
                                atualizado_em=datetime('now')
                            WHERE id=?
                            """,
                            (venc, dias, sit, oid),
                        )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível carregar locações.\n\n{e}")
        # Ordena: primeiro vencidos, depois os mais próximos de vencer, por fim os demais.
        # Dentro de cada grupo, usa dias_a_vencer (quando houver) e, em seguida,
        # a data do pedido (mais recentes primeiro).
        from datetime import datetime

        def _parse_int(val, default=99999):
            try:
                return int(str(val or "").strip())
            except ValueError:
                return default

        def _parse_date_iso(val):
            try:
                return datetime.fromisoformat(str(val or "").strip()).date()
            except Exception:
                return None

        def _grupo(r):
            tag = destaque_visual_linha_locacao_db(r)
            if tag == "vencido":
                return 0
            if tag == "dois_dias":
                return 1
            return 2

        def _sort_key(r):
            g = _grupo(r)
            dias = _parse_int(r.get("dias_a_vencer"))
            dp = _parse_date_iso(r.get("data_pedido"))
            dp_ord = -int(dp.toordinal()) if dp else 0
            return (g, dias, dp_ord)

        self._todos.sort(key=_sort_key)

        self._atualizar_kpis()
        self._aplicar_filtro()
        if notificar_sidebar:
            self._notificar_mainwindow_locacoes_atualizadas()

    def _notificar_mainwindow_locacoes_atualizadas(self):
        """Atualiza alerta na sidebar / título assim que os dados de locações mudam."""
        try:
            mw = self.window()
            if mw is not None and hasattr(mw, "_poll_locacoes_vencimento"):
                QTimer.singleShot(0, mw._poll_locacoes_vencimento)
        except Exception:
            pass

    def _passa_preset(self, r):
        sit = str(r.get("situacao", "")).strip().upper()
        if self._filtro_preset == "todos":
            return True
        if self._filtro_preset == "ok":
            return sit == "OK" or str(r.get("pedido_ok", "")).upper() == "OK"
        if self._filtro_preset == "vencido":
            return sit == "VENCIDO"
        if self._filtro_preset == "atualizar":
            return sit == "ATUALIZAR"
        if self._filtro_preset == "na_obra":
            return sit == "NA OBRA"
        return True

    def _passa_janela_vencimento(self, r):
        if not getattr(self, "combo_janela_venc", None):
            return True
        dias_win = self.combo_janela_venc.currentData()
        if dias_win is None:
            return True
        sit = str(r.get("situacao", "")).strip().upper()
        if sit == "VENCIDO":
            return True
        hoje = date.today()
        lo = hoje - timedelta(days=int(dias_win))
        hi = hoje + timedelta(days=int(dias_win))

        def _parse_iso_d(iso: str):
            if not iso or len(iso) < 10:
                return None
            try:
                return datetime.strptime(iso[:10], "%Y-%m-%d").date()
            except ValueError:
                return None

        vd = _parse_iso_d(_clean(r.get("data_vencimento")))
        pd = _parse_iso_d(_clean(r.get("data_pedido")))
        if vd is not None and lo <= vd <= hi:
            return True
        if pd is not None and lo <= pd <= hi:
            return True
        if vd is None and pd is None:
            return True
        return False

    def _aplicar_filtro(self):
        if not getattr(self, "e_busca", None):
            return
        termo = self.e_busca.text().strip().lower()
        base = [
            r for r in self._todos
            if self._passa_preset(r) and self._passa_janela_vencimento(r)
        ]
        if not termo:
            self._filtrados = base
        else:
            self._filtrados = []
            for r in base:
                tipo_rot = str(r.get("tipo", "")).strip().upper()
                tipo_txt = "caçamba cacamba" if tipo_rot == "CACAMBA" else ""
                blob = " ".join([
                    str(r.get("obra", "")),
                    str(r.get("comprador", "")),
                    str(r.get("numero_pedido", "")),
                    str(r.get("pedido_compra_numero", "")),
                    str(r.get("fornecedor", "")),
                    str(r.get("item_locado", "")),
                    tipo_txt,
                    str(r.get("situacao", "")),
                    str(r.get("pedido_ok", "")),
                ]).lower()
                if termo in blob:
                    self._filtrados.append(r)
        self._render()

    def _wrap_centro_fundo(self, cor_hex: str, inner: QWidget) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(0)
        lay.addStretch(1)
        lay.addWidget(inner, 0, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        lay.addStretch(1)
        w.setStyleSheet(f"background-color:{cor_hex};")
        if isinstance(inner, QPushButton):
            inner.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        return w

    @staticmethod
    def _compact_pedido_numero(txt: str) -> str:
        return _compact_pedido_numero(txt)

    def _buscar_caminho_pdf_pedido(self, numero_digitado: str) -> tuple[str, str]:
        """
        Retorna (caminho_pdf, numero_encontrado) ou ('','') se não achar.
        """
        num = _clean(numero_digitado)
        if not num:
            return "", ""
        cn = self._compact_pedido_numero(num).upper()
        try:
            with get_connection() as conn:
                pr = conn.execute(
                    """
                    SELECT caminho_pdf, numero FROM pedidos
                    WHERE TRIM(numero) = TRIM(?) COLLATE NOCASE
                    LIMIT 1
                    """,
                    (num,),
                ).fetchone()
                if pr and _clean(pr["caminho_pdf"]):
                    return _clean(pr["caminho_pdf"]), _clean(pr["numero"])

                for row in conn.execute(
                    "SELECT numero, caminho_pdf FROM pedidos WHERE caminho_pdf IS NOT NULL AND TRIM(caminho_pdf) != ''"
                ):
                    n_db = _clean(row["numero"])
                    if self._compact_pedido_numero(n_db).upper() == cn:
                        return _clean(row["caminho_pdf"]), n_db
        except Exception:
            pass
        return "", ""

    def _candidatos_numero_pedido_pdf(self, row: dict) -> list:
        """Ordem: vínculo explícito; depois Nº Pedido da locação (costuma ser o pedido do sistema)."""
        out = []
        for key in ("pedido_compra_numero", "numero_pedido"):
            v = _clean(row.get(key))
            if v and v not in out:
                out.append(v)
        return out

    def _abrir_arquivo_pdf(self, path: str) -> bool:
        path = os.path.normpath(path)
        if not os.path.isfile(path):
            return False
        url = QUrl.fromLocalFile(path)
        if QDesktopServices.openUrl(url):
            return True
        if sys.platform == "win32":
            try:
                os.startfile(path)
                return True
            except OSError:
                pass
        return False

    def _abrir_pdf_pedido_locacao(self, oid: int):
        row = next((x for x in self._todos if x.get("id") == oid), None)
        if not row:
            self._carregar()
            row = next((x for x in self._todos if x.get("id") == oid), None)
        if not row:
            QMessageBox.warning(self, "PDF", "Registro não encontrado.")
            return
        candidatos = self._candidatos_numero_pedido_pdf(row)
        if not candidatos:
            QMessageBox.information(
                self,
                "PDF",
                "Não há número de pedido nesta linha para localizar o PDF.\n\n"
                "Preencha «Nº Pedido» (planilha / locação) ou «Pedido de compra» em Editar — "
                "o sistema tenta os dois na base da aba Pedidos.",
            )
            return
        path = ""
        num_usado = ""
        for num in candidatos:
            pth, _ = self._buscar_caminho_pdf_pedido(num)
            if pth and os.path.isfile(pth):
                path = pth
                num_usado = num
                break
        if not path:
            lista = ", ".join(f"«{c}»" for c in candidatos)
            QMessageBox.warning(
                self,
                "PDF não encontrado",
                f"Não há PDF na sua base para: {lista}\n\n"
                f"Os pedidos são buscados no banco do usuário atual ({COMPRADOR_PADRAO}). "
                "O número precisa ser o mesmo cadastrado em Pedidos gerados.",
            )
            return
        if not self._abrir_arquivo_pdf(path):
            QMessageBox.warning(
                self,
                "PDF",
                f"Não foi possível abrir o arquivo:\n{path}",
            )
            return
        # Grava vínculo quando achou pelo Nº Pedido e o campo explícito estava vazio
        if not _clean(row.get("pedido_compra_numero")) and num_usado:
            try:
                with get_locacoes_connection() as conn:
                    conn.execute(
                        """
                        UPDATE locacoes_registros SET
                            pedido_compra_numero=?,
                            versao=versao+1,
                            atualizado_em=datetime('now')
                        WHERE id=?
                          AND (pedido_compra_numero IS NULL OR TRIM(pedido_compra_numero)='')
                        """,
                        (num_usado, oid),
                    )
                for lst in (self._todos, self._filtrados):
                    for x in lst:
                        if x.get("id") == oid:
                            x["pedido_compra_numero"] = num_usado
                            break
                self._render()
            except Exception:
                pass

    def _reverter_devolucao_equipamento(self, oid: int):
        if QMessageBox.question(
            self,
            "Desfazer devolução",
            "Deseja desmarcar a devolução?\n\n"
            "O registro volta a acompanhar vencimento e situação normalmente.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        try:
            with get_locacoes_connection() as conn:
                row = conn.execute(
                    """
                    SELECT data_pedido, periodo_dias, data_vencimento
                    FROM locacoes_registros WHERE id=?
                    """,
                    (oid,),
                ).fetchone()
                if not row:
                    return
                venc, dias, sit = _calcular_derivados(
                    row["data_pedido"],
                    row["periodo_dias"],
                    row["data_vencimento"],
                    "",
                )
                conn.execute(
                    """
                    UPDATE locacoes_registros SET
                        pedido_ok='',
                        data_vencimento=?, dias_a_vencer=?, situacao=?,
                        versao=versao+1, atualizado_em=datetime('now')
                    WHERE id=?
                    """,
                    (venc, dias, sit, oid),
                )
            self._carregar()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _confirmar_devolucao_equipamento(self, oid: int):
        if QMessageBox.question(
            self,
            "Confirmar devolução",
            "Tem certeza de que o equipamento foi devolvido?\n\n"
            "Esta ação marca o registro como encerrado (Pedido OK).",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        try:
            with get_locacoes_connection() as conn:
                row = conn.execute(
                    """
                    SELECT data_pedido, periodo_dias, data_vencimento
                    FROM locacoes_registros WHERE id=?
                    """,
                    (oid,),
                ).fetchone()
                if not row:
                    return
                venc, dias, sit = _calcular_derivados(
                    row["data_pedido"],
                    row["periodo_dias"],
                    row["data_vencimento"],
                    "OK",
                )
                conn.execute(
                    """
                    UPDATE locacoes_registros SET
                        pedido_ok='OK',
                        data_vencimento=?, dias_a_vencer=?, situacao=?,
                        versao=versao+1, atualizado_em=datetime('now')
                    WHERE id=?
                    """,
                    (venc, dias, sit, oid),
                )
            self._carregar()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _render(self):
        self.tabela.setRowCount(0)
        self.tabela.verticalHeader().setDefaultSectionSize(46)

        def badge_situacao(item: QTableWidgetItem, sit: str, zebra: QColor):
            sit = (sit or "").strip().upper()
            if sit == "VENCIDO":
                item.setBackground(QBrush(QColor("#FADBD8")))
                item.setForeground(QColor("#78281F"))
            elif sit == "ATUALIZAR":
                item.setBackground(QBrush(QColor("#FDEBD0")))
                item.setForeground(QColor("#9C640C"))
            elif sit == "NA OBRA":
                item.setBackground(QBrush(QColor("#D4EFDF")))
                item.setForeground(QColor("#145A32"))
            elif sit == "OK":
                item.setBackground(QBrush(QColor("#E8F6F3")))
                item.setForeground(QColor("#1B4F72"))
            else:
                item.setBackground(QBrush(zebra))
                item.setForeground(QColor(TXT))

            f = item.font()
            f.setBold(True)
            f.setPointSize(10)
            item.setFont(f)

        for _, r in enumerate(self._filtrados):
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)
            zebra = QColor("#F4F6F8") if row % 2 else QColor(WHITE)

            oid = r.get("id")
            sit_raw = str(r.get("situacao", "")).strip().upper()
            pok_raw = str(r.get("pedido_ok", "")).strip().upper()
            destaque = _destaque_visual_linha_locacao(r)
            bg_hex = _hex_fundo_linha(destaque, zebra)

            tipo_rot = str(r.get("tipo", "")).strip().upper()
            item_txt = str(r.get("item_locado", "") or "")
            if tipo_rot == "CACAMBA" and item_txt:
                item_txt = f"{item_txt} · Caçamba"

            texto_por_col = {
                0: r.get("obra", ""),
                1: r.get("comprador", ""),
                2: r.get("numero_pedido", ""),
                3: r.get("fornecedor", ""),
                4: item_txt,
                6: _iso_to_br(r.get("data_pedido", "")),
                7: "" if r.get("periodo_dias") is None else str(r.get("periodo_dias")),
                8: _iso_to_br(r.get("data_vencimento", "")),
                9: r.get("dias_a_vencer", ""),
                10: r.get("situacao", ""),
            }

            # Itens vazios sob PDF/botão: sem isso o Qt pinta seleção azul só nas colunas com widget.
            base_flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            for col in (COL_PDF, COL_BOTAO_DEVOLVIDO):
                pit = QTableWidgetItem("")
                pit.setFlags(base_flags)
                pit.setTextAlignment(Qt.AlignCenter)
                if destaque == "vencido":
                    pit.setData(ROLE_ROW_DESTAQUE, "vencido")
                    pit.setForeground(QBrush(ROW_FG_VENCIDO))
                elif destaque == "dois_dias":
                    pit.setData(ROLE_ROW_DESTAQUE, "dois_dias")
                    pit.setForeground(QBrush(ROW_FG_2DIAS))
                else:
                    pit.setBackground(QBrush(zebra))
                    pit.setForeground(QColor(TXT))
                self.tabela.setItem(row, col, pit)

            tem_pdf = bool(self._candidatos_numero_pedido_pdf(r))
            btn_pdf = QPushButton("PDF")
            btn_pdf.setFlat(True)
            btn_pdf.setCursor(Qt.PointingHandCursor)
            btn_pdf.setFixedSize(62, 28)
            btn_pdf.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn_pdf.setAutoDefault(False)
            btn_pdf.setDefault(False)
            btn_pdf.setStyleSheet(_pdf_btn_stylesheet(destaque, tem_pdf))
            btn_pdf.setToolTip(
                "Abre o PDF na aba Pedidos — usa «Pedido de compra» ou o «Nº Pedido» da linha"
                if tem_pdf
                else "Informe «Nº Pedido» ou «Pedido de compra» em Editar para localizar o PDF"
            )
            btn_pdf.clicked.connect(partial(self._abrir_pdf_pedido_locacao, int(oid)))
            self.tabela.setCellWidget(
                row, COL_PDF, self._wrap_centro_fundo(bg_hex, btn_pdf),
            )

            if pok_raw == "OK":
                btn_rev = QPushButton("✓ Reverter")
                btn_rev.setFlat(True)
                btn_rev.setCursor(Qt.PointingHandCursor)
                btn_rev.setFixedSize(148, 30)
                btn_rev.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                btn_rev.setAutoDefault(False)
                btn_rev.setDefault(False)
                btn_rev.setStyleSheet(
                    f"""
                    QPushButton {{
                        background:{WHITE}; color:{TXT_S}; font-weight:bold; font-size:11px;
                        border-radius:6px; border:1.5px solid {BDR}; padding:4px 12px;
                    }}
                    QPushButton:hover {{ color:{RED}; border-color:{RED}; background:#FFFBFB; }}
                    """
                )
                btn_rev.setToolTip(
                    "Desfazer devolução: volta a controlar vencimento normalmente"
                )
                btn_rev.clicked.connect(partial(self._reverter_devolucao_equipamento, int(oid)))
                self.tabela.setCellWidget(
                    row, COL_BOTAO_DEVOLVIDO, self._wrap_centro_fundo(bg_hex, btn_rev),
                )
            else:
                btn_ok = QPushButton("OK")
                btn_ok.setFlat(True)
                btn_ok.setCursor(Qt.PointingHandCursor)
                btn_ok.setFixedSize(52, 28)
                btn_ok.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                btn_ok.setAutoDefault(False)
                btn_ok.setDefault(False)
                btn_ok.setStyleSheet(_ok_btn_stylesheet(destaque))
                btn_ok.setToolTip("Marca que o equipamento foi devolvido (pede confirmação)")
                btn_ok.clicked.connect(partial(self._confirmar_devolucao_equipamento, int(oid)))
                self.tabela.setCellWidget(
                    row, COL_BOTAO_DEVOLVIDO, self._wrap_centro_fundo(bg_hex, btn_ok),
                )

            for c in range(12):
                if c in (COL_PDF, COL_BOTAO_DEVOLVIDO):
                    continue
                txt = str(texto_por_col.get(c, ""))
                it = QTableWidgetItem(txt)
                if c == 0:
                    it.setData(Qt.UserRole, oid)
                if c in (1, 2, 6, 7, 8, 9, 10):
                    it.setTextAlignment(Qt.AlignCenter)

                if destaque == "vencido":
                    it.setData(ROLE_ROW_DESTAQUE, "vencido")
                    it.setForeground(QBrush(ROW_FG_VENCIDO))
                    if c == 10:
                        bf = it.font()
                        bf.setBold(True)
                        bf.setPointSize(10)
                        it.setFont(bf)
                elif destaque == "dois_dias":
                    it.setData(ROLE_ROW_DESTAQUE, "dois_dias")
                    it.setForeground(QBrush(ROW_FG_2DIAS))
                    if c == 10:
                        bf = it.font()
                        bf.setBold(True)
                        bf.setPointSize(10)
                        it.setFont(bf)
                elif c == 10:
                    badge_situacao(it, sit_raw, zebra)
                elif c == 9 and pok_raw != "OK":
                    try:
                        d = int(str(txt).strip())
                        if d < 0:
                            it.setForeground(QColor("#C0392B"))
                            bf = it.font()
                            bf.setBold(True)
                            it.setFont(bf)
                        elif 0 <= d <= LOCACOES_DIAS_ALERTA_ANTECEDENCIA:
                            it.setForeground(QColor("#CA6F1E"))
                    except ValueError:
                        pass
                    it.setBackground(QBrush(zebra))
                else:
                    it.setBackground(QBrush(zebra))

                self.tabela.setItem(row, c, it)

        nf = len(self._filtrados)
        nt = len(self._todos)
        prefix = ""
        if getattr(self, "_pending_sync_notice", None):
            pn = self._pending_sync_notice
            self._pending_sync_notice = None
            prefix = (
                f"<span style='color:{GREEN};font-weight:600;'>{pn}</span><br/>"
            )
        jhint = ""
        if getattr(self, "combo_janela_venc", None):
            jw = self.combo_janela_venc.currentData()
            if jw is not None:
                jhint = (
                    f" <span style='color:{TXT_S};'>· Grade: pedido ou vencimento ±{jw} dias "
                    f"(vencidos sempre visíveis)</span>"
                )
        self.lbl_info.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_info.setText(
            prefix
            + f"<span style='color:{TXT_S};'>Exibindo</span> "
            f"<b style='color:{RED};font-size:12px;'>{nf}</b> "
            f"<span style='color:{TXT_S};'>de</span> "
            f"<b style='color:{GRAY};'>{nt}</b> "
            f"<span style='color:{TXT_S};'>registros.</span>"
            + jhint
        )
