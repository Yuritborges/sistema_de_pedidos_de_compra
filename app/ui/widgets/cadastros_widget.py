# app/ui/widgets/cadastros_widget.py
# Aba de manutenção de cadastros do sistema.
# Permite editar fornecedores e obras existentes sem abrir JSON/SQLite.

import os
import json
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox,
    QLineEdit, QPushButton, QMessageBox, QGridLayout, QTabWidget,
    QTextEdit, QCompleter, QGraphicsDropShadowEffect
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

FORNECEDORES_JSON = os.path.join(ASSETS_DIR, "fornecedores.json")
OBRAS_JSON = os.path.join(ASSETS_DIR, "obras.json")
FUNCIONARIOS_JSON = os.path.join(ASSETS_DIR, "funcionarios.json")


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{path}.bak_{stamp}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                original = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(original)
        except Exception:
            pass
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class CadastrosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.fornecedores = {}
        self.obras = {}
        self._build()
        self._carregar_tudo()

    def _build(self):
        self.setStyleSheet("""
            QWidget { background:#f3f5f8; color:#1f2937; font-family:Segoe UI; font-size:12px; }
            QFrame#headerCard, QFrame#sectionCard { background:#ffffff; border:1px solid #e7eaee; border-radius:18px; }
            QLabel#pageTitle { font-size:24px; font-weight:800; color:#192434; background:transparent; }
            QLabel#pageSubtitle { font-size:12px; color:#6b7280; background:transparent; }
            QLabel#sectionTitle { font-size:14px; font-weight:800; color:#374151; background:transparent; }
            QLabel#fieldLabel { font-size:11px; font-weight:700; color:#6b7280; background:transparent; }
            QLineEdit, QTextEdit, QComboBox {
                background:#ffffff;
                border:1px solid #d7dde5;
                border-radius:10px;
                padding:8px 10px;
                min-height:34px;
                color:#1f2937;
                font-size:12px;
            }
            QTextEdit { min-height:70px; }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border:1.5px solid #c0392b;
                background:#fffefe;
            }

            /* ComboBox premium com seta visível */
            QComboBox {
                padding-right:34px;
            }
            QComboBox::drop-down {
                subcontrol-origin:padding;
                subcontrol-position:top right;
                width:34px;
                border:none;
                border-top-right-radius:10px;
                border-bottom-right-radius:10px;
                background:#f8fafc;
            }
            QComboBox::down-arrow {
                width:0px;
                height:0px;
                margin-right:11px;
                border-left:6px solid transparent;
                border-right:6px solid transparent;
                border-top:7px solid #6b7280;
            }
            QComboBox:hover::down-arrow {
                border-top:7px solid #c0392b;
            }
            QComboBox QAbstractItemView {
                background:#ffffff;
                color:#1f2937;
                border:1px solid #d7dde5;
                border-radius:10px;
                padding:6px;
                outline:none;
                font-size:12px;
                selection-background-color:#fdecea;
                selection-color:#c0392b;
            }
            QComboBox QAbstractItemView::item {
                min-height:30px;
                padding:6px 10px;
            }

            /* Scrollbar dos combos e telas */
            QScrollBar:vertical {
                background:#eef2f6;
                width:14px;
                margin:3px;
                border-radius:7px;
            }
            QScrollBar::handle:vertical {
                background:#9fb0c2;
                border:1px solid #8899ab;
                border-radius:7px;
                min-height:40px;
            }
            QScrollBar::handle:vertical:hover {
                background:#8599ad;
            }
            QScrollBar::add-line, QScrollBar::sub-line,
            QScrollBar::up-arrow, QScrollBar::down-arrow {
                width:0px;
                height:0px;
                background:transparent;
                border:none;
            }

            QPushButton { background:#c0392b; color:white; border:none; border-radius:10px; padding:8px 14px; min-height:36px; font-weight:800; }
            QPushButton:hover { background:#a93226; }
            QPushButton#secondaryButton { background:#ffffff; color:#1f2937; border:1px solid #d7dde5; }
            QPushButton#secondaryButton:hover { background:#f3f4f6; }
            QPushButton#dangerButton { background:#7f1d1d; color:white; }
            QPushButton#dangerButton:hover { background:#991b1b; }
            QTabWidget::pane { border:none; background:transparent; }
            QTabBar::tab { background:#ffffff; border:1px solid #e7eaee; border-bottom:none; border-top-left-radius:10px; border-top-right-radius:10px; padding:10px 18px; margin-right:4px; font-weight:700; color:#374151; }
            QTabBar::tab:selected { background:#c0392b; color:white; border:1px solid #c0392b; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)
        root.addWidget(self._build_header())

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_fornecedores_tab(), "Fornecedores")
        self.tabs.addTab(self._build_obras_tab(), "Obras")
        root.addWidget(self.tabs, 1)

    def _build_header(self):
        card = QFrame(); card.setObjectName("headerCard"); self._apply_shadow(card)
        layout = QHBoxLayout(card); layout.setContentsMargins(20, 16, 20, 16); layout.setSpacing(12)
        text = QVBoxLayout(); text.setSpacing(3)
        title = QLabel("Cadastros"); title.setObjectName("pageTitle")
        subtitle = QLabel("Manutenção de fornecedores e obras sem abrir JSON ou banco de dados"); subtitle.setObjectName("pageSubtitle")
        text.addWidget(title); text.addWidget(subtitle)
        layout.addLayout(text); layout.addStretch()
        btn_recarregar = QPushButton("↻ Recarregar"); btn_recarregar.clicked.connect(self._carregar_tudo)
        layout.addWidget(btn_recarregar)
        return card

    def _build_fornecedores_tab(self):
        page = QWidget(); root = QVBoxLayout(page); root.setContentsMargins(0,14,0,0); root.setSpacing(14)
        card = QFrame(); card.setObjectName("sectionCard"); self._apply_shadow(card)
        layout = QVBoxLayout(card); layout.setContentsMargins(18,16,18,16); layout.setSpacing(14)
        title = QLabel("Editar Fornecedor"); title.setObjectName("sectionTitle"); layout.addWidget(title)
        top = QHBoxLayout(); top.setSpacing(10)
        self.cb_fornecedor = QComboBox(); self.cb_fornecedor.setEditable(True); self.cb_fornecedor.setInsertPolicy(QComboBox.NoInsert)
        self.cb_fornecedor.currentTextChanged.connect(self._fornecedor_selecionado)
        comp = QCompleter(); comp.setCaseSensitivity(Qt.CaseInsensitive); comp.setFilterMode(Qt.MatchContains); self.cb_fornecedor.setCompleter(comp)
        top.addWidget(self._field("Fornecedor existente", self.cb_fornecedor), 1)
        btn_novo = QPushButton("+ Novo Fornecedor"); btn_novo.setObjectName("secondaryButton"); btn_novo.clicked.connect(self._novo_fornecedor); top.addWidget(btn_novo)
        layout.addLayout(top)

        grid = QGridLayout(); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(10)
        self.ed_for_nome = QLineEdit(); self.ed_for_razao = QLineEdit(); self.ed_for_email = QLineEdit(); self.ed_for_vendedor = QLineEdit()
        self.ed_for_telefone = QLineEdit(); self.ed_for_pix = QLineEdit(); self.ed_for_favorecido = QTextEdit()
        grid.addWidget(self._field("Nome curto / Apelido", self.ed_for_nome), 0, 0)
        grid.addWidget(self._field("Vendedor", self.ed_for_vendedor), 0, 1)
        grid.addWidget(self._field("Telefone", self.ed_for_telefone), 0, 2)
        grid.addWidget(self._field("Razão Social", self.ed_for_razao), 1, 0, 1, 2)
        grid.addWidget(self._field("E-mail", self.ed_for_email), 1, 2)
        grid.addWidget(self._field("PIX", self.ed_for_pix), 2, 0)
        grid.addWidget(self._field("Favorecido / Dados bancários", self.ed_for_favorecido), 2, 1, 1, 2)
        layout.addLayout(grid)

        actions = QHBoxLayout(); actions.addStretch()
        btn_excluir = QPushButton("Excluir"); btn_excluir.setObjectName("dangerButton"); btn_excluir.clicked.connect(self._excluir_fornecedor)
        btn_salvar = QPushButton("Salvar Fornecedor"); btn_salvar.clicked.connect(self._salvar_fornecedor)
        actions.addWidget(btn_excluir); actions.addWidget(btn_salvar); layout.addLayout(actions)
        root.addWidget(card); root.addStretch(); return page

    def _build_obras_tab(self):
        page = QWidget(); root = QVBoxLayout(page); root.setContentsMargins(0,14,0,0); root.setSpacing(14)
        card = QFrame(); card.setObjectName("sectionCard"); self._apply_shadow(card)
        layout = QVBoxLayout(card); layout.setContentsMargins(18,16,18,16); layout.setSpacing(14)
        title = QLabel("Editar Obra"); title.setObjectName("sectionTitle"); layout.addWidget(title)
        top = QHBoxLayout(); top.setSpacing(10)
        self.cb_obra = QComboBox(); self.cb_obra.setEditable(True); self.cb_obra.setInsertPolicy(QComboBox.NoInsert)
        self.cb_obra.currentTextChanged.connect(self._obra_selecionada)
        comp = QCompleter(); comp.setCaseSensitivity(Qt.CaseInsensitive); comp.setFilterMode(Qt.MatchContains); self.cb_obra.setCompleter(comp)
        top.addWidget(self._field("Obra existente", self.cb_obra), 1)
        btn_novo = QPushButton("+ Nova Obra"); btn_novo.setObjectName("secondaryButton"); btn_novo.clicked.connect(self._nova_obra); top.addWidget(btn_novo)
        layout.addLayout(top)

        grid = QGridLayout(); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(10)
        self.ed_obra_nome = QLineEdit(); self.ed_obra_faturamento = QLineEdit(); self.ed_obra_escola = QLineEdit(); self.ed_obra_endereco = QLineEdit()
        self.ed_obra_bairro = QLineEdit(); self.ed_obra_cep = QLineEdit(); self.ed_obra_contrato = QLineEdit(); self.ed_obra_cidade = QLineEdit()
        self.ed_obra_uf = QLineEdit(); self.ed_obra_empreiteiro = QLineEdit(); self.ed_obra_contato = QLineEdit()
        grid.addWidget(self._field("Nome da Obra", self.ed_obra_nome), 0, 0)
        grid.addWidget(self._field("Faturamento", self.ed_obra_faturamento), 0, 1)
        grid.addWidget(self._field("Contrato", self.ed_obra_contrato), 0, 2)
        grid.addWidget(self._field("Escola / Descrição", self.ed_obra_escola), 1, 0, 1, 3)
        grid.addWidget(self._field("Endereço", self.ed_obra_endereco), 2, 0, 1, 2)
        grid.addWidget(self._field("Bairro", self.ed_obra_bairro), 2, 2)
        grid.addWidget(self._field("Cidade", self.ed_obra_cidade), 3, 0)
        grid.addWidget(self._field("UF", self.ed_obra_uf), 3, 1)
        grid.addWidget(self._field("CEP", self.ed_obra_cep), 3, 2)
        grid.addWidget(self._field("Empreiteiro", self.ed_obra_empreiteiro), 4, 0)
        grid.addWidget(self._field("Contato", self.ed_obra_contato), 4, 1, 1, 2)
        layout.addLayout(grid)

        actions = QHBoxLayout(); actions.addStretch()
        btn_excluir = QPushButton("Excluir"); btn_excluir.setObjectName("dangerButton"); btn_excluir.clicked.connect(self._excluir_obra)
        btn_salvar = QPushButton("Salvar Obra"); btn_salvar.clicked.connect(self._salvar_obra)
        actions.addWidget(btn_excluir); actions.addWidget(btn_salvar); layout.addLayout(actions)
        root.addWidget(card); root.addStretch(); return page

    def _field(self, label_text, widget, *args):
        wrap = QWidget(); layout = QVBoxLayout(wrap); layout.setContentsMargins(0,0,0,0); layout.setSpacing(4)
        label = QLabel(label_text); label.setObjectName("fieldLabel")
        layout.addWidget(label); layout.addWidget(widget); return wrap

    def _apply_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(18); shadow.setOffset(0,4); shadow.setColor(QColor(0,0,0,18)); widget.setGraphicsEffect(shadow)

    def _carregar_tudo(self):
        self.fornecedores = _load_json(FORNECEDORES_JSON, {})
        self.obras = _load_json(OBRAS_JSON, {})
        self._popular_fornecedores(); self._popular_obras()

    def _popular_fornecedores(self):
        nomes = sorted(self.fornecedores.keys())
        self.cb_fornecedor.blockSignals(True); self.cb_fornecedor.clear(); self.cb_fornecedor.addItems(nomes)
        if self.cb_fornecedor.completer(): self.cb_fornecedor.completer().setModel(self.cb_fornecedor.model())
        self.cb_fornecedor.blockSignals(False)
        if nomes: self.cb_fornecedor.setCurrentIndex(0); self._fornecedor_selecionado(nomes[0])
        else: self._limpar_fornecedor()

    def _popular_obras(self):
        nomes = sorted(self.obras.keys())
        self.cb_obra.blockSignals(True); self.cb_obra.clear(); self.cb_obra.addItems(nomes)
        if self.cb_obra.completer(): self.cb_obra.completer().setModel(self.cb_obra.model())
        self.cb_obra.blockSignals(False)
        if nomes: self.cb_obra.setCurrentIndex(0); self._obra_selecionada(nomes[0])
        else: self._limpar_obra()

    def _fornecedor_selecionado(self, nome):
        nome = (nome or "").strip()
        if not nome or nome not in self.fornecedores: return
        dados = self.fornecedores.get(nome, {}) or {}
        self.ed_for_nome.setText(nome)
        self.ed_for_razao.setText(str(dados.get("razao", "")))
        self.ed_for_email.setText(str(dados.get("email", "")))
        self.ed_for_vendedor.setText(str(dados.get("vendedor", "")))
        self.ed_for_telefone.setText(str(dados.get("telefone", "")))
        self.ed_for_pix.setText(str(dados.get("pix", "")))
        self.ed_for_favorecido.setPlainText(str(dados.get("favorecido", "")))

    def _novo_fornecedor(self): self.cb_fornecedor.setCurrentText(""); self._limpar_fornecedor(); self.ed_for_nome.setFocus()
    def _limpar_fornecedor(self):
        self.ed_for_nome.clear(); self.ed_for_razao.clear(); self.ed_for_email.clear(); self.ed_for_vendedor.clear(); self.ed_for_telefone.clear(); self.ed_for_pix.clear(); self.ed_for_favorecido.clear()

    def _salvar_fornecedor(self):
        nome_novo = self.ed_for_nome.text().strip().upper(); nome_antigo = self.cb_fornecedor.currentText().strip()
        if not nome_novo: QMessageBox.warning(self, "Atenção", "Informe o nome curto/apelido do fornecedor."); return
        dados = {"razao": self.ed_for_razao.text().strip(), "email": self.ed_for_email.text().strip(), "vendedor": self.ed_for_vendedor.text().strip(), "telefone": self.ed_for_telefone.text().strip(), "pix": self.ed_for_pix.text().strip(), "favorecido": self.ed_for_favorecido.toPlainText().strip()}
        if nome_antigo and nome_antigo in self.fornecedores and nome_antigo != nome_novo:
            resp = QMessageBox.question(self, "Renomear fornecedor", f"Você está renomeando:\n\n{nome_antigo}\n\npara:\n\n{nome_novo}\n\nDeseja continuar?", QMessageBox.Yes | QMessageBox.No)
            if resp != QMessageBox.Yes: return
            self.fornecedores.pop(nome_antigo, None)
        self.fornecedores[nome_novo] = dados; _save_json(FORNECEDORES_JSON, self.fornecedores)
        self._popular_fornecedores(); self.cb_fornecedor.setCurrentText(nome_novo); QMessageBox.information(self, "Salvo", "Fornecedor salvo com sucesso.")

    def _excluir_fornecedor(self):
        nome = self.cb_fornecedor.currentText().strip()
        if not nome or nome not in self.fornecedores: QMessageBox.warning(self, "Atenção", "Selecione um fornecedor existente para excluir."); return
        resp = QMessageBox.question(self, "Confirmar exclusão", f"Tem certeza que deseja excluir o fornecedor?\n\n{nome}\n\nEssa ação remove o cadastro da base JSON.", QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes: return
        self.fornecedores.pop(nome, None); _save_json(FORNECEDORES_JSON, self.fornecedores); self._popular_fornecedores(); QMessageBox.information(self, "Excluído", "Fornecedor excluído com sucesso.")

    def _obra_selecionada(self, nome):
        nome = (nome or "").strip()
        if not nome or nome not in self.obras: return
        dados = self.obras.get(nome, {}) or {}
        self.ed_obra_nome.setText(nome); self.ed_obra_faturamento.setText(str(dados.get("faturamento", ""))); self.ed_obra_escola.setText(str(dados.get("escola", "")))
        self.ed_obra_endereco.setText(str(dados.get("endereco", ""))); self.ed_obra_bairro.setText(str(dados.get("bairro", ""))); self.ed_obra_cep.setText(str(dados.get("cep", "")))
        self.ed_obra_contrato.setText(str(dados.get("contrato", ""))); self.ed_obra_cidade.setText(str(dados.get("cidade", ""))); self.ed_obra_uf.setText(str(dados.get("uf", "")))
        self.ed_obra_empreiteiro.setText(str(dados.get("empreiteiro", ""))); self.ed_obra_contato.setText(str(dados.get("contato", "")))

    def _nova_obra(self): self.cb_obra.setCurrentText(""); self._limpar_obra(); self.ed_obra_nome.setFocus()
    def _limpar_obra(self):
        self.ed_obra_nome.clear(); self.ed_obra_faturamento.clear(); self.ed_obra_escola.clear(); self.ed_obra_endereco.clear(); self.ed_obra_bairro.clear(); self.ed_obra_cep.clear(); self.ed_obra_contrato.clear(); self.ed_obra_cidade.clear(); self.ed_obra_uf.clear(); self.ed_obra_empreiteiro.clear(); self.ed_obra_contato.clear()

    def _salvar_obra(self):
        nome_novo = self.ed_obra_nome.text().strip().upper(); nome_antigo = self.cb_obra.currentText().strip()
        if not nome_novo: QMessageBox.warning(self, "Atenção", "Informe o nome da obra."); return
        dados = {"faturamento": self.ed_obra_faturamento.text().strip().upper(), "escola": self.ed_obra_escola.text().strip(), "endereco": self.ed_obra_endereco.text().strip(), "bairro": self.ed_obra_bairro.text().strip(), "cep": self.ed_obra_cep.text().strip(), "contrato": self.ed_obra_contrato.text().strip(), "cidade": self.ed_obra_cidade.text().strip(), "uf": self.ed_obra_uf.text().strip().upper() or "SP", "empreiteiro": self.ed_obra_empreiteiro.text().strip(), "contato": self.ed_obra_contato.text().strip()}
        if nome_antigo and nome_antigo in self.obras and nome_antigo != nome_novo:
            resp = QMessageBox.question(self, "Renomear obra", f"Você está renomeando:\n\n{nome_antigo}\n\npara:\n\n{nome_novo}\n\nDeseja continuar?", QMessageBox.Yes | QMessageBox.No)
            if resp != QMessageBox.Yes: return
            self.obras.pop(nome_antigo, None)
        self.obras[nome_novo] = dados; _save_json(OBRAS_JSON, self.obras)
        self._popular_obras(); self.cb_obra.setCurrentText(nome_novo); QMessageBox.information(self, "Salvo", "Obra salva com sucesso.")

    def _excluir_obra(self):
        nome = self.cb_obra.currentText().strip()
        if not nome or nome not in self.obras: QMessageBox.warning(self, "Atenção", "Selecione uma obra existente para excluir."); return
        resp = QMessageBox.question(self, "Confirmar exclusão", f"Tem certeza que deseja excluir a obra?\n\n{nome}\n\nEssa ação remove o cadastro da base JSON.", QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes: return
        self.obras.pop(nome, None); _save_json(OBRAS_JSON, self.obras); self._popular_obras(); QMessageBox.information(self, "Excluído", "Obra excluída com sucesso.")
