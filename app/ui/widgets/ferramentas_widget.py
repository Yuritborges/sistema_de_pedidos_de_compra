import os
import json
import unicodedata
from datetime import datetime, date

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QFrame,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)
from PySide6.QtGui import QPixmap, QColor

from app.data.database import get_connection, sincronizar_com_rede
from app.data.cadastros_store import OBRAS_JSON
from app.ui.style import (
    BG,
    BLUE,
    CSS_BUSCA,
    CSS_COMBO,
    CSS_INPUT,
    CSS_TABLE,
    GREEN,
    GRAY,
    RED,
    TXT_S,
    btn_outline,
    btn_solid,
    make_card,
)


def _normalizar_texto(txt: str) -> str:
    base = unicodedata.normalize("NFKD", str(txt or ""))
    sem_acento = "".join(ch for ch in base if not unicodedata.combining(ch))
    return sem_acento.strip().upper()


def _br_to_iso(valor: str) -> str:
    txt = str(valor or "").strip()
    if not txt or txt.upper() == "NAT":
        return ""
    if len(txt) >= 10 and txt[4] == "-" and txt[7] == "-":
        return txt[:10]
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(txt, fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return ""


def _iso_to_br(valor: str) -> str:
    txt = str(valor or "").strip()
    if not txt:
        return ""
    try:
        return datetime.strptime(txt[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return txt


def _txt_limpo(valor) -> str:
    txt = str(valor or "").strip()
    if txt.lower() in ("nan", "nat", "none"):
        return ""
    return txt


class RegistroFerramentaDialog(QDialog):
    def __init__(self, dados=None, parent=None, categorias=None, obras=None):
        super().__init__(parent)
        self.setWindowTitle("Registro de Ferramenta")
        self.setMinimumWidth(520)
        dados = dados or {}
        categorias = categorias or []
        obras = obras or []

        self.setStyleSheet("""
            QCalendarWidget QWidget { alternate-background-color: #FFFFFF; }
            QCalendarWidget QAbstractItemView:enabled {
                color: #111827;
                background: #FFFFFF;
                selection-background-color: #C0392B;
                selection-color: #FFFFFF;
            }
            QCalendarWidget QToolButton {
                color: #111827;
                background: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
                padding: 2px 6px;
            }
            QCalendarWidget QToolButton:hover {
                background: #FDECEC;
                color: #9F1239;
            }
            QCalendarWidget QMenu { background: #FFFFFF; color: #111827; }
            QCalendarWidget QSpinBox {
                color: #111827; background: #FFFFFF;
                selection-background-color: #C0392B;
                selection-color: #FFFFFF;
            }
            QCalendarWidget QHeaderView::section {
                background: #C0392B;
                color: #FFFFFF;
                padding: 4px;
                border: none;
            }
        """)

        form = QFormLayout(self)
        form.setSpacing(10)

        self.e_categoria = QComboBox()
        self.e_categoria.setEditable(True)
        self.e_categoria.addItem("")
        for cat in categorias:
            self.e_categoria.addItem(cat)
        self.e_categoria.setCurrentText(str(dados.get("categoria", "") or ""))
        self.e_serie = QLineEdit(str(dados.get("numero_serie", "") or ""))
        self.e_ferramenta = QLineEdit(str(dados.get("ferramenta", "") or ""))
        self.e_responsavel = QLineEdit(str(dados.get("responsavel", "") or ""))
        self.e_obra = QComboBox()
        self.e_obra.setEditable(True)
        self.e_obra.addItem("")
        for obra in obras:
            self.e_obra.addItem(obra)
        self.e_obra.setCurrentText(str(dados.get("obra", "") or ""))
        self.e_obs = QLineEdit(str(dados.get("observacoes", "") or ""))
        self.e_serie_escritorio = QLineEdit(str(dados.get("numero_serie_escritorio", "") or ""))
        self.e_foto_ref = QLineEdit(str(dados.get("foto_ref", "") or ""))
        self.e_saida = QDateEdit()
        self.e_saida.setCalendarPopup(True)
        self.e_saida.setDisplayFormat("dd/MM/yyyy")
        self.e_saida.setSpecialValueText("")
        self.e_saida.setDate(QDate.currentDate())
        self.e_devolucao = QDateEdit()
        self.e_devolucao.setCalendarPopup(True)
        self.e_devolucao.setDisplayFormat("dd/MM/yyyy")
        self.e_devolucao.setMinimumDate(QDate(2000, 1, 1))
        self.e_devolucao.setSpecialValueText("Sem devolução")
        self.e_devolucao.setDate(self.e_devolucao.minimumDate())

        saida_iso = str(dados.get("data_saida", "") or "").strip()
        if saida_iso:
            try:
                self.e_saida.setDate(QDate.fromString(saida_iso, "yyyy-MM-dd"))
            except Exception:
                pass
        dev_iso = str(dados.get("data_devolucao", "") or "").strip()
        if dev_iso:
            try:
                self.e_devolucao.setDate(QDate.fromString(dev_iso, "yyyy-MM-dd"))
            except Exception:
                pass

        for campo in (
            self.e_serie,
            self.e_ferramenta,
            self.e_responsavel,
            self.e_obs,
            self.e_serie_escritorio,
            self.e_foto_ref,
        ):
            campo.setStyleSheet(CSS_INPUT)
        self.e_categoria.setStyleSheet(CSS_COMBO)
        self.e_obra.setStyleSheet(CSS_COMBO)

        btn_salvar = btn_solid("Salvar", RED)
        btn_cancelar = btn_outline("Cancelar")
        btn_salvar.clicked.connect(self.accept)
        btn_cancelar.clicked.connect(self.reject)

        form.addRow("Categoria", self.e_categoria)
        form.addRow("Nº de série", self.e_serie)
        form.addRow("Ferramenta", self.e_ferramenta)
        form.addRow("Responsável", self.e_responsavel)
        form.addRow("Data saída", self.e_saida)
        form.addRow("Data devolução", self.e_devolucao)
        form.addRow("Obra", self.e_obra)
        form.addRow("Nº Série Escritório", self.e_serie_escritorio)
        hl_foto = QHBoxLayout()
        hl_foto.addWidget(self.e_foto_ref, 1)
        btn_foto = btn_outline("Selecionar foto")
        btn_foto.clicked.connect(self._selecionar_foto)
        hl_foto.addWidget(btn_foto)
        form.addRow("Foto do item", hl_foto)
        form.addRow("Observações", self.e_obs)
        hl = QHBoxLayout()
        hl.addStretch()
        hl.addWidget(btn_cancelar)
        hl.addWidget(btn_salvar)
        form.addRow(hl)

    def dados(self):
        dev_qdate = self.e_devolucao.date()
        dev = dev_qdate.toPython()
        saida = self.e_saida.date().toPython()
        sem_devolucao = dev_qdate == self.e_devolucao.minimumDate()
        data_devolucao = "" if sem_devolucao else dev.strftime("%Y-%m-%d")
        data_saida = saida.strftime("%Y-%m-%d") if self.e_saida.date().isValid() else ""
        status = "DEVOLVIDO" if data_devolucao else "EM USO"
        return {
            "categoria": self.e_categoria.currentText().strip(),
            "numero_serie": self.e_serie.text().strip(),
            "ferramenta": self.e_ferramenta.text().strip(),
            "responsavel": self.e_responsavel.text().strip(),
            "data_saida": data_saida,
            "data_devolucao": data_devolucao,
            "obra": self.e_obra.currentText().strip(),
            "numero_serie_escritorio": self.e_serie_escritorio.text().strip(),
            "foto_ref": self.e_foto_ref.text().strip(),
            "observacoes": self.e_obs.text().strip(),
            "status": status,
        }

    def _selecionar_foto(self):
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar foto da ferramenta",
            os.path.expanduser("~"),
            "Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.gif)"
        )
        if caminho:
            self.e_foto_ref.setText(caminho)


class FerramentasWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._todos = []
        self._dados_visiveis = []
        self._build()
        self._carregar()

    def _obras_disponiveis(self):
        try:
            if not os.path.exists(OBRAS_JSON):
                return []
            with open(OBRAS_JSON, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, dict):
                return sorted([str(k).strip() for k in dados.keys() if str(k).strip()])
        except Exception:
            pass
        return []

    def _categorias_disponiveis(self):
        cats = {str(i.get("categoria") or "").strip() for i in self._todos}
        return sorted([c for c in cats if c])

    def _build(self):
        self.setStyleSheet(f"background:{BG};")
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        top = QHBoxLayout()
        tv = QVBoxLayout()
        titulo = QLabel("Ferramentas")
        titulo.setStyleSheet(f"font-size:20px; font-weight:bold; color:{GRAY};")
        sub = QLabel("Controle de ferramentas conforme planilha padrão")
        sub.setStyleSheet(f"font-size:11px; color:{TXT_S};")
        tv.addWidget(titulo)
        tv.addWidget(sub)
        top.addLayout(tv)
        top.addStretch()
        self.btn_importar = btn_outline("Importar planilha")
        self.btn_importar.clicked.connect(self._importar_planilha_padrao)
        btn_novo = btn_solid("Novo registro", RED)
        btn_novo.clicked.connect(self._novo_registro)
        btn_editar = btn_outline("Editar selecionado")
        btn_editar.clicked.connect(self._editar_selecionado)
        btn_excluir = btn_outline("Excluir selecionado")
        btn_excluir.clicked.connect(self._excluir_selecionado)
        btn_atualizar = btn_solid("Atualizar", "#95A5A6")
        btn_atualizar.clicked.connect(self._carregar)
        top.addWidget(self.btn_importar)
        top.addWidget(btn_novo)
        top.addWidget(btn_editar)
        top.addWidget(btn_excluir)
        top.addWidget(btn_atualizar)
        root.addLayout(top)

        cards = QHBoxLayout()
        c1, self.lv_total = make_card("Total", "0", RED)
        c2, self.lv_uso = make_card("Em uso", "0", BLUE)
        c3, self.lv_dev = make_card("Devolvido", "0", GREEN)
        cards.addWidget(c1)
        cards.addWidget(c2)
        cards.addWidget(c3)
        cards.addStretch()
        root.addLayout(cards)

        hl_categoria = QHBoxLayout()
        lbl_categoria = QLabel("Categoria")
        lbl_categoria.setStyleSheet("font-size:11px; font-weight:700; color:#6B7280;")
        self.cb_categoria = QComboBox()
        self.cb_categoria.setStyleSheet(CSS_COMBO)
        self.cb_categoria.setMinimumWidth(340)
        hl_categoria.addWidget(lbl_categoria)
        hl_categoria.addWidget(self.cb_categoria)
        hl_categoria.addStretch()
        root.addLayout(hl_categoria)

        filtros = QHBoxLayout()
        self.cb_status = QComboBox()
        self.cb_status.addItems(["Todos", "EM USO", "DEVOLVIDO"])
        self.cb_status.setStyleSheet(CSS_COMBO)
        self.e_busca = QLineEdit()
        self.e_busca.setPlaceholderText("Buscar ferramenta, série, obra ou responsável...")
        self.e_busca.setStyleSheet(CSS_BUSCA)
        self.e_busca.setMinimumWidth(320)
        filtros.addWidget(self.cb_status)
        filtros.addWidget(self.e_busca, 1)
        root.addLayout(filtros)

        self.tabela = QTableWidget(0, 12)
        self.tabela.setHorizontalHeaderLabels([
            "Categoria", "Nº Série", "Ferramenta", "Responsável",
            "Saída", "Devolução", "Dias em uso", "Obra", "Nº Série Escritório",
            "Foto Ref", "Status", "Obs",
        ])
        self.tabela.setStyleSheet(
            CSS_TABLE + """
            QTableWidget {
                background: #FFFFFF;
                alternate-background-color: #FAFAFA;
                color: #111827;
                gridline-color: #E5E7EB;
                selection-background-color: #FDECEC;
                selection-color: #7F1D1D;
            }
            QTableWidget::item {
                color: #111827;
                padding: 4px 6px;
            }
            QHeaderView::section {
                background: #C0392B;
                color: #FFFFFF;
                border: 1px solid #A93226;
                font-weight: 700;
                padding: 6px;
            }
            """
        )
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.verticalHeader().setVisible(False)
        hh = self.tabela.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)
        hh.setMinimumSectionSize(70)
        hh.setStretchLastSection(False)
        self.tabela.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.tabela.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tabela.setColumnWidth(0, 120)   # Categoria
        self.tabela.setColumnWidth(1, 110)   # N° Série
        self.tabela.setColumnWidth(2, 240)   # Ferramenta
        self.tabela.setColumnWidth(3, 160)   # Responsável
        self.tabela.setColumnWidth(4, 95)    # Saída
        self.tabela.setColumnWidth(5, 95)    # Devolução
        self.tabela.setColumnWidth(6, 90)    # Dias em uso
        self.tabela.setColumnWidth(7, 220)   # Obra
        self.tabela.setColumnWidth(8, 140)   # N° Série Escritório
        self.tabela.setColumnWidth(9, 220)   # Foto Ref
        self.tabela.setColumnWidth(10, 90)   # Status
        self.tabela.setColumnWidth(11, 260)  # Obs

        tabela_frame = QFrame()
        tabela_frame.setStyleSheet("QFrame { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; }")
        tabela_lay = QVBoxLayout(tabela_frame)
        tabela_lay.setContentsMargins(8, 8, 8, 8)
        tabela_lay.addWidget(self.tabela)

        detalhes_frame = self._criar_painel_detalhes()

        split = QSplitter(Qt.Horizontal)
        split.setChildrenCollapsible(False)
        split.addWidget(tabela_frame)
        split.addWidget(detalhes_frame)
        split.setSizes([920, 340])
        root.addWidget(split, 1)

        self.cb_status.currentTextChanged.connect(self._aplicar_filtros)
        self.cb_categoria.currentTextChanged.connect(self._aplicar_filtros)
        self.e_busca.textChanged.connect(self._aplicar_filtros)
        self.tabela.itemSelectionChanged.connect(self._ao_selecionar_linha)
        self.tabela.itemClicked.connect(self._abrir_acoes_linha)

    def _carregar(self):
        sql = """
            SELECT *
              FROM ferramentas_registros
             ORDER BY COALESCE(data_saida, atualizado_em) DESC, id DESC
        """
        with get_connection() as conn:
            self._todos = [dict(r) for r in conn.execute(sql).fetchall()]
        self._repopular_categoria()
        self._aplicar_filtros()

    def _repopular_categoria(self):
        categorias = sorted({str(i.get("categoria") or "").strip() for i in self._todos if str(i.get("categoria") or "").strip()})
        atual = self._categoria_ativa()
        self.cb_categoria.blockSignals(True)
        self.cb_categoria.clear()
        self.cb_categoria.addItem("Todas")
        self.cb_categoria.addItems(categorias)
        alvo = atual if atual in categorias else "Todas"
        idx = self.cb_categoria.findText(alvo)
        self.cb_categoria.setCurrentIndex(idx if idx >= 0 else 0)
        self.cb_categoria.blockSignals(False)

    def _categoria_ativa(self):
        txt = self.cb_categoria.currentText().strip()
        return txt or "Todas"

    def _criar_painel_detalhes(self):
        box = QFrame()
        box.setStyleSheet("QFrame { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; }")
        vl = QVBoxLayout(box)
        vl.setContentsMargins(14, 14, 14, 14)
        vl.setSpacing(10)

        t = QLabel("Detalhes da ferramenta")
        t.setStyleSheet("font-size: 13px; font-weight: 700; color: #111827;")
        vl.addWidget(t)

        self.lbl_foto = QLabel("Sem foto")
        self.lbl_foto.setAlignment(Qt.AlignCenter)
        self.lbl_foto.setFixedHeight(150)
        self.lbl_foto.setStyleSheet(
            "background:#F9FAFB; border:1px dashed #D1D5DB; border-radius:8px; color:#6B7280; font-size:11px;"
        )
        vl.addWidget(self.lbl_foto)

        self.lbl_detalhes = QLabel("Selecione um item da tabela para visualizar os detalhes.")
        self.lbl_detalhes.setWordWrap(True)
        self.lbl_detalhes.setStyleSheet("font-size:11px; color:#374151; line-height:1.5;")
        vl.addWidget(self.lbl_detalhes)
        vl.addStretch()
        return box

    def _dias_em_uso(self, item):
        saida = str(item.get("data_saida") or "").strip()
        devolucao = str(item.get("data_devolucao") or "").strip()
        if not saida:
            return "—"
        fim = date.today()
        if devolucao:
            try:
                fim = datetime.strptime(devolucao[:10], "%Y-%m-%d").date()
            except Exception:
                fim = date.today()
        try:
            inicio = datetime.strptime(saida[:10], "%Y-%m-%d").date()
            dias = max((fim - inicio).days, 0)
            return str(dias)
        except Exception:
            return "—"

    def _resolver_foto(self, ref):
        txt = str(ref or "").strip()
        if not txt:
            return ""
        if os.path.exists(txt):
            return txt
        base = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        candidatos = [
            os.path.join(base, txt),
            os.path.join(base, "documentos", "ferramentas", txt),
            os.path.join(base, "assets", txt),
        ]
        return next((p for p in candidatos if os.path.exists(p)), "")

    def _ao_selecionar_linha(self):
        row = self.tabela.currentRow()
        if row < 0:
            return
        item = self.tabela.item(row, 0)
        if not item:
            return
        reg_id = int(item.data(Qt.UserRole) or 0)
        reg = next((d for d in self._dados_visiveis if int(d.get("id") or 0) == reg_id), None)
        if reg:
            self._mostrar_detalhes(reg)

    def _mostrar_detalhes(self, item):
        status = str(item.get("status") or "—")
        foto_path = self._resolver_foto(item.get("foto_ref", ""))
        if foto_path:
            pix = QPixmap(foto_path)
            if not pix.isNull():
                self.lbl_foto.setPixmap(pix.scaled(300, 145, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.lbl_foto.setText("")
            else:
                self.lbl_foto.setPixmap(QPixmap())
                self.lbl_foto.setText("Foto inválida")
        else:
            self.lbl_foto.setPixmap(QPixmap())
            self.lbl_foto.setText("Sem foto")

        cor = "#16A34A" if status == "DEVOLVIDO" else "#DC2626"
        texto = (
            f"<b style='font-size:12px;'>{item.get('ferramenta','—')}</b><br>"
            f"<span style='color:{cor}; font-weight:700;'>Status: {status}</span><br><br>"
            f"<b>Categoria:</b> {item.get('categoria','—')}<br>"
            f"<b>Série:</b> {item.get('numero_serie','—')}<br>"
            f"<b>Série Escritório:</b> {item.get('numero_serie_escritorio','—')}<br>"
            f"<b>Responsável:</b> {item.get('responsavel','—')}<br>"
            f"<b>Obra/Local:</b> {item.get('obra','—')}<br>"
            f"<b>Data de saída:</b> {_iso_to_br(item.get('data_saida','')) or '—'}<br>"
            f"<b>Data de devolução:</b> {_iso_to_br(item.get('data_devolucao','')) or '—'}<br>"
            f"<b>Dias em uso:</b> {self._dias_em_uso(item)}<br>"
            f"<b>Observações:</b> {item.get('observacoes','—') or '—'}"
        )
        self.lbl_detalhes.setText(texto)

    def _aplicar_filtros(self):
        status = self.cb_status.currentText()
        categoria = self._categoria_ativa()
        termo = self.e_busca.text().strip().upper()
        dados = []
        for item in self._todos:
            if status != "Todos" and (item.get("status") or "") != status:
                continue
            if categoria != "Todas" and (item.get("categoria") or "") != categoria:
                continue
            blob = " ".join([
                str(item.get("ferramenta") or ""),
                str(item.get("numero_serie") or ""),
                str(item.get("obra") or ""),
                str(item.get("responsavel") or ""),
            ]).upper()
            if termo and termo not in blob:
                continue
            dados.append(item)
        self._dados_visiveis = dados
        self._preencher_tabela(dados)
        self.lv_total.setText(str(len(dados)))
        self.lv_uso.setText(str(sum(1 for d in dados if (d.get("status") or "") == "EM USO")))
        self.lv_dev.setText(str(sum(1 for d in dados if (d.get("status") or "") == "DEVOLVIDO")))
        if dados:
            self._mostrar_detalhes(dados[0])
        else:
            self.lbl_foto.setPixmap(QPixmap())
            self.lbl_foto.setText("Sem foto")
            self.lbl_detalhes.setText("Nenhum item encontrado para os filtros aplicados.")

    def _preencher_tabela(self, dados):
        self.tabela.setRowCount(len(dados))
        for r, item in enumerate(dados):
            valores = [
                _txt_limpo(item.get("categoria", "")),
                _txt_limpo(item.get("numero_serie", "")),
                _txt_limpo(item.get("ferramenta", "")),
                _txt_limpo(item.get("responsavel", "")),
                _iso_to_br(item.get("data_saida", "")),
                _iso_to_br(item.get("data_devolucao", "")),
                self._dias_em_uso(item),
                _txt_limpo(item.get("obra", "")),
                _txt_limpo(item.get("numero_serie_escritorio", "")),
                _txt_limpo(item.get("foto_ref", "")),
                _txt_limpo(item.get("status", "")),
                _txt_limpo(item.get("observacoes", "")),
            ]
            for c, v in enumerate(valores):
                cel = QTableWidgetItem(str(v or ""))
                if c in (4, 5, 6, 10):
                    cel.setTextAlignment(Qt.AlignCenter)
                if c == 10:
                    cel.setForeground(QColor("#2C2C2C"))
                self.tabela.setItem(r, c, cel)
            self.tabela.item(r, 0).setData(Qt.UserRole, int(item.get("id") or 0))

    def _registro_selecionado_id(self):
        row = self.tabela.currentRow()
        if row < 0:
            return 0
        item = self.tabela.item(row, 0)
        return int(item.data(Qt.UserRole) or 0) if item else 0

    def _registro_por_id(self, reg_id: int):
        return next((d for d in self._dados_visiveis if int(d.get("id") or 0) == int(reg_id)), None)

    def _novo_registro(self):
        dlg = RegistroFerramentaDialog(
            parent=self,
            categorias=self._categorias_disponiveis(),
            obras=self._obras_disponiveis(),
        )
        if dlg.exec() != QDialog.Accepted:
            return
        dados = dlg.dados()
        if not dados["ferramenta"]:
            QMessageBox.warning(self, "Atenção", "Informe a ferramenta.")
            return
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO ferramentas_registros (
                    categoria, numero_serie, ferramenta, responsavel,
                    data_saida, data_devolucao, obra, observacoes, numero_serie_escritorio,
                    foto_ref, status, atualizado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    dados["categoria"], dados["numero_serie"], dados["ferramenta"],
                    dados["responsavel"], dados["data_saida"], dados["data_devolucao"],
                    dados["obra"], dados["observacoes"], dados["numero_serie_escritorio"],
                    dados["foto_ref"], dados["status"],
                ),
            )
        sincronizar_com_rede(silencioso=True)
        self._carregar()

    def _editar_selecionado(self):
        reg_id = self._registro_selecionado_id()
        if not reg_id:
            QMessageBox.information(self, "Ferramentas", "Selecione um registro para editar.")
            return
        self._editar_registro(reg_id)

    def _editar_registro(self, reg_id: int):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM ferramentas_registros WHERE id = ?", (reg_id,)).fetchone()
        if not row:
            return
        dlg = RegistroFerramentaDialog(
            dict(row),
            self,
            categorias=self._categorias_disponiveis(),
            obras=self._obras_disponiveis(),
        )
        if dlg.exec() != QDialog.Accepted:
            return
        dados = dlg.dados()
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE ferramentas_registros
                   SET categoria = ?, numero_serie = ?, ferramenta = ?, responsavel = ?,
                       data_saida = ?, data_devolucao = ?, obra = ?, observacoes = ?,
                       numero_serie_escritorio = ?, foto_ref = ?, status = ?, atualizado_em = datetime('now')
                 WHERE id = ?
                """,
                (
                    dados["categoria"], dados["numero_serie"], dados["ferramenta"],
                    dados["responsavel"], dados["data_saida"], dados["data_devolucao"],
                    dados["obra"], dados["observacoes"], dados["numero_serie_escritorio"],
                    dados["foto_ref"], dados["status"], reg_id,
                ),
            )
        sincronizar_com_rede(silencioso=True)
        self._carregar()

    def _excluir_selecionado(self):
        reg_id = self._registro_selecionado_id()
        if not reg_id:
            QMessageBox.information(self, "Ferramentas", "Selecione um registro para excluir.")
            return
        self._excluir_registro_id(reg_id)

    def _excluir_registro_id(self, reg_id: int):
        reg = self._registro_por_id(reg_id) or {}
        nome = _txt_limpo(reg.get("ferramenta", "")) or "item sem nome"
        serie = _txt_limpo(reg.get("numero_serie", ""))
        resp = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Deseja excluir este registro?\n\nFerramenta: {nome}\nSérie: {serie or '—'}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return
        with get_connection() as conn:
            conn.execute("DELETE FROM ferramentas_registros WHERE id = ?", (reg_id,))
        sincronizar_com_rede(silencioso=True)
        self._carregar()

    def _devolver_registro_hoje(self, reg_id: int):
        data_hoje = datetime.now().strftime("%Y-%m-%d")
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE ferramentas_registros
                   SET data_devolucao = ?, status = 'DEVOLVIDO', atualizado_em = datetime('now')
                 WHERE id = ?
                """,
                (data_hoje, reg_id),
            )
        sincronizar_com_rede(silencioso=True)
        self._carregar()

    def _abrir_acoes_linha(self, _item):
        reg_id = self._registro_selecionado_id()
        if not reg_id:
            return
        reg = self._registro_por_id(reg_id)
        if not reg:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Controle da ferramenta")
        dlg.setMinimumWidth(760)
        dlg.setStyleSheet("""
            QDialog { background: #F8FAFC; }
            QFrame#card {
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
            QLabel#titulo {
                font-size: 18px;
                font-weight: 800;
                color: #111827;
            }
            QLabel#sub {
                font-size: 11px;
                color: #6B7280;
            }
            QLabel#foto {
                background: #F9FAFB;
                border: 1px dashed #D1D5DB;
                border-radius: 10px;
                color: #6B7280;
                font-size: 11px;
            }
            QLabel#badgeUso {
                background: #FEF2F2;
                color: #991B1B;
                border: 1px solid #FECACA;
                border-radius: 10px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 800;
            }
            QLabel#badgeDev {
                background: #ECFDF3;
                color: #166534;
                border: 1px solid #A7F3D0;
                border-radius: 10px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 800;
            }
        """)
        vl = QVBoxLayout(dlg)
        vl.setContentsMargins(14, 12, 14, 12)

        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(12)

        status = str(reg.get("status") or "").upper()
        badge = QLabel("DEVOLVIDO" if status == "DEVOLVIDO" else "EM USO")
        badge.setObjectName("badgeDev" if status == "DEVOLVIDO" else "badgeUso")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedWidth(120)

        titulo = QLabel(f"🧰 {reg.get('ferramenta','Ferramenta')}")
        titulo.setObjectName("titulo")
        sub = QLabel(
            f"Categoria: {reg.get('categoria','—')}  |  Série: {reg.get('numero_serie','—')}"
        )
        sub.setObjectName("sub")

        topo = QHBoxLayout()
        topo.addWidget(titulo)
        topo.addStretch()
        topo.addWidget(badge)
        cl.addLayout(topo)
        cl.addWidget(sub)

        corpo = QHBoxLayout()
        corpo.setSpacing(12)

        foto = QLabel("Sem foto")
        foto.setObjectName("foto")
        foto.setAlignment(Qt.AlignCenter)
        foto.setMinimumSize(280, 220)
        foto_path = self._resolver_foto(reg.get("foto_ref", ""))
        if foto_path:
            pix = QPixmap(foto_path)
            if not pix.isNull():
                foto.setPixmap(pix.scaled(270, 210, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                foto.setText("")
        corpo.addWidget(foto)

        info = QLabel(
            f"👤 <b>Responsável:</b> {_txt_limpo(reg.get('responsavel','')) or '—'}<br>"
            f"📍 <b>Obra/Local:</b> {_txt_limpo(reg.get('obra','')) or '—'}<br>"
            f"📅 <b>Saída:</b> {_iso_to_br(reg.get('data_saida','')) or '—'}<br>"
            f"✅ <b>Devolução:</b> {_iso_to_br(reg.get('data_devolucao','')) or '—'}<br>"
            f"⏱ <b>Dias em uso:</b> {self._dias_em_uso(reg)}<br>"
            f"🏷 <b>Série Escritório:</b> {_txt_limpo(reg.get('numero_serie_escritorio','')) or '—'}<br>"
            f"📝 <b>Observações:</b> {_txt_limpo(reg.get('observacoes','')) or '—'}"
        )
        info.setWordWrap(True)
        info.setStyleSheet("font-size:12px; color:#374151; line-height:1.7;")
        corpo.addWidget(info, 1)
        cl.addLayout(corpo)
        vl.addWidget(card)

        hl = QHBoxLayout()
        hl.addStretch()
        btn_cancelar = btn_outline("Fechar")
        btn_editar = btn_outline("✏ Editar completo")
        btn_excluir = btn_outline("🗑 Excluir item")
        btn_devolver = btn_solid("✅ Devolver agora", RED)
        if status == "DEVOLVIDO":
            btn_devolver.setEnabled(False)
            btn_devolver.setToolTip("Este item já está devolvido.")
        hl.addWidget(btn_cancelar)
        hl.addWidget(btn_editar)
        hl.addWidget(btn_excluir)
        hl.addWidget(btn_devolver)
        vl.addLayout(hl)

        btn_cancelar.clicked.connect(dlg.reject)
        btn_editar.clicked.connect(lambda: (dlg.accept(), self._editar_registro(reg_id)))
        btn_excluir.clicked.connect(lambda: (dlg.accept(), self._excluir_registro_id(reg_id)))

        def devolver():
            self._devolver_registro_hoje(reg_id)
            dlg.accept()
            QMessageBox.information(
                self,
                "Devolução registrada",
                "Item marcado como DEVOLVIDO com a data de hoje."
            )

        btn_devolver.clicked.connect(devolver)
        dlg.exec()

    def _importar_planilha_padrao(self):
        caminho = os.path.normpath(os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "documentos", "ferramentas",
            "CONTROLE DE FERRAMENTAS BRASUL CONSTRUTORA.xlsx",
        ))
        if not os.path.exists(caminho):
            QMessageBox.warning(self, "Importação", f"Arquivo não encontrado:\n{caminho}")
            return
        try:
            import pandas as pd
        except Exception:
            QMessageBox.warning(self, "Importação", "Pandas não está disponível para ler o Excel.")
            return

        try:
            xls = pd.ExcelFile(caminho)
            inseridos = 0
            with get_connection() as conn:
                conn.execute(
                    "DELETE FROM ferramentas_registros WHERE origem_planilha = ?",
                    (caminho,),
                )
                for aba in xls.sheet_names:
                    df = pd.read_excel(caminho, sheet_name=aba)
                    if df.empty:
                        continue
                    colunas = {c: _normalizar_texto(c) for c in df.columns}

                    def pick(data, *tokens):
                        for k, v in data.items():
                            if all(t in k for t in tokens):
                                return v
                        return ""

                    def pick_serie_principal(data):
                        for k, v in data.items():
                            if "SERIE" in k and "ESCRITORIO" not in k:
                                return v
                        return ""

                    for _, row in df.iterrows():
                        data = {colunas[c]: row[c] for c in df.columns}
                        ferramenta = _txt_limpo(pick(data, "FERRAMENTA"))
                        serie = _txt_limpo(pick_serie_principal(data))
                        if not ferramenta and not serie:
                            continue
                        responsavel = _txt_limpo(pick(data, "RESPONSAVEL"))
                        saida = _br_to_iso(str(pick(data, "SAIDA") or ""))
                        devolucao = _br_to_iso(str(pick(data, "DEVOLU") or ""))
                        obra = _txt_limpo(pick(data, "OBRA") or pick(data, "OBSERVA"))
                        obs = _txt_limpo(pick(data, "OBSERVACAO") or pick(data, "UNNAMED"))
                        serie_esc = _txt_limpo(pick(data, "SERIE", "ESCRITORIO"))
                        foto = _txt_limpo(pick(data, "FOTO"))
                        status = "DEVOLVIDO" if devolucao else "EM USO"
                        conn.execute(
                            """
                            INSERT INTO ferramentas_registros (
                                categoria, numero_serie, ferramenta, responsavel, data_saida,
                                data_devolucao, obra, observacoes, numero_serie_escritorio,
                                foto_ref, status, origem_planilha, atualizado_em
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                            """,
                            (
                                aba.strip(),
                                serie,
                                ferramenta,
                                responsavel,
                                saida,
                                devolucao,
                                obra,
                                obs,
                                serie_esc,
                                foto,
                                status,
                                caminho,
                            ),
                        )
                        inseridos += 1
            sincronizar_com_rede(silencioso=True)
            self._carregar()
            QMessageBox.information(self, "Importação", f"Importação concluída: {inseridos} registros.")
        except Exception as e:
            QMessageBox.critical(self, "Importação", f"Falha ao importar planilha:\n{e}")
