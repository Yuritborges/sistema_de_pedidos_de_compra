# app/ui/widgets/formulario_pedido.py
# Formulário de criação e edição de pedidos de compra.
import os, sys, subprocess, json, copy
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDoubleSpinBox, QGroupBox, QScrollArea, QSpinBox, QCompleter,
    QDialog, QFormLayout, QDialogButtonBox, QTextEdit, QAbstractItemView,
    QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeyEvent

from config import (EMPRESAS_FATURADORAS, UNIDADES,
                    CONDICOES_PAGAMENTO, FORMAS_PAGAMENTO, COMPRADOR_PADRAO)
from app.core.dto.pedido_dto import PedidoDTO, ItemPedidoDTO
from app.core.services.pedido_service import PedidoService
from app.data.database import (
    proximo_numero_pedido,
    atualizar_numero_pedido,
)

# ── Caminhos dos arquivos JSON ─────────────────────────────────────────────────
_ASSETS = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets')
)
_OBR = os.path.join(_ASSETS, 'obras.json')
_FOR = os.path.join(_ASSETS, 'fornecedores.json')
_EMP = os.path.join(_ASSETS, 'empresas_extra.json')  # empresas cadastradas pelo usuário
_PED_RASC = os.path.join(_ASSETS, 'pedidos_salvos')  # rascunhos de pedidos salvos pelo usuário


def _load(p):
    try:
        with open(p, encoding='utf-8') as f: return json.load(f)
    except Exception: return {}

def _save(p, d):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


# ── Paleta ─────────────────────────────────────────────────────────────────────
RED   = "#C0392B"
GRAY  = "#2C2C2C"
WHITE = "#FFFFFF"
BG    = "#F0EDED"
CARD  = "#FFFFFF"
BDR   = "#D8CCCC"
BDR_F = "#C0392B"
TXT   = "#1A1A1A"
TXT_S = "#6B5555"
RO_BG = "#F5F0F0"
SEL   = "#FADBD8"
HOV   = "#FEF0EF"
GREEN = "#1E8449"

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS_INPUT = f"""
    QLineEdit {{
        color:{TXT}; background:{WHITE};
        border:1.5px solid {BDR}; border-radius:5px;
        padding:4px 10px; font-size:12px; min-height:30px;
        selection-background-color:{SEL}; selection-color:{GRAY};
    }}
    QLineEdit:focus {{ border:1.5px solid {BDR_F}; background:#FFFBFB; }}
    QLineEdit:read-only {{ color:{TXT_S}; background:{RO_BG}; border:1.5px solid #E8DEDE; }}
    QSpinBox, QDoubleSpinBox {{
        color:{TXT}; background:{WHITE};
        border:1.5px solid {BDR}; border-radius:5px;
        padding:4px 8px; font-size:12px; min-height:30px;
        selection-background-color:{SEL};
    }}
    QSpinBox:focus, QDoubleSpinBox:focus {{ border:1.5px solid {BDR_F}; }}
"""
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
        outline:none; padding:2px; font-size:12px;
    }}
    QComboBox QAbstractItemView::item {{
        color:{TXT}; background:{WHITE}; min-height:28px; padding:4px 10px;
    }}
    QComboBox QAbstractItemView::item:hover   {{ background:{HOV}; color:{TXT}; }}
    QComboBox QAbstractItemView::item:selected {{ background:{SEL}; color:{GRAY}; }}
"""
CSS_POPUP = f"""
    QAbstractItemView {{
        color:{TXT}; background:{WHITE};
        border:1.5px solid {BDR_F}; border-radius:5px;
        selection-background-color:{SEL}; selection-color:{GRAY};
        font-size:12px; padding:2px; outline:none;
    }}
    QAbstractItemView::item {{
        color:{TXT}; background:{WHITE}; min-height:28px; padding:4px 10px;
    }}
    QAbstractItemView::item:hover   {{ background:{HOV}; color:{TXT}; }}
    QAbstractItemView::item:selected {{ background:{SEL}; color:{GRAY}; }}
"""
CSS_GROUP = f"""
    QGroupBox {{
        font-weight:bold; font-size:12px; color:{RED};
        border:1.5px solid #E8D5D3; border-radius:10px;
        margin-top:8px; padding:14px 12px 10px 12px; background:{CARD};
    }}
    QGroupBox::title {{
        subcontrol-origin:margin; left:14px; padding:0 6px;
        color:{RED}; background:{CARD};
    }}
    QGroupBox QLabel {{
        color:{TXT_S}; background:transparent;
        font-size:11px; font-weight:500;
    }}
"""
CSS_TEXTAREA = f"""
    QTextEdit {{
        color:{TXT}; background:{WHITE};
        border:1.5px solid {BDR}; border-radius:5px;
        padding:6px 10px; font-size:12px;
    }}
    QTextEdit:focus {{ border:1.5px solid {BDR_F}; background:#FFFBFB; }}
"""

# ── Helpers de UI ──────────────────────────────────────────────────────────────
def _fld(val="", ro=False):
    f = QLineEdit(val); f.setReadOnly(ro); f.setStyleSheet(CSS_INPUT); return f

def _combo(items):
    c = QComboBox(); c.addItems(items); c.setStyleSheet(CSS_COMBO)
    c.view().setStyleSheet(
        f"color:{TXT};background:{WHITE};"
        f"selection-background-color:{SEL};selection-color:{GRAY};")
    return c

def _grp(titulo):
    b = QGroupBox(titulo); b.setStyleSheet(CSS_GROUP); return b

def _col(label, widget, w=-1):
        # Layout vertical: label em cima, widget embaixo.
    col = QVBoxLayout(); col.setSpacing(4)
    lbl = QLabel(label)
    lbl.setStyleSheet(f"font-size:11px;color:{TXT_S};font-weight:600;background:transparent;")
    col.addWidget(lbl)
    if w > 0: widget.setFixedWidth(w)
    col.addWidget(widget)
    return col

def _btn(texto, cor, mini=False):
    b = QPushButton(texto); b.setFixedHeight(32 if mini else 36)
    pad = "0 12px" if mini else "0 18px"
    b.setStyleSheet(f"""
        QPushButton {{
            background:{cor}; color:white; font-size:12px;
            font-weight:bold; border-radius:6px; border:none;
            padding:{pad}; letter-spacing:0.3px;
        }}
        QPushButton:hover   {{ background:{cor}DD; }}
        QPushButton:pressed {{ background:{cor}AA; }}
    """)
    return b

def _make_completer(lista, parent):
        # Autocomplete que encontra o termo em qualquer parte do texto.
    c = QCompleter(lista, parent)
    c.setCaseSensitivity(Qt.CaseInsensitive)
    c.setFilterMode(Qt.MatchContains)
    c.popup().setStyleSheet(CSS_POPUP)
    return c


# ══════════════════════════════════════════════════════════════════════════════
# SPINBOX CUSTOMIZADO — seleciona tudo ao focar
# ══════════════════════════════════════════════════════════════════════════════

class _SpinFoco(QDoubleSpinBox):
    """
    QDoubleSpinBox que seleciona todo o conteúdo ao receber foco.

    PROBLEMA RESOLVIDO:
        No QDoubleSpinBox padrão, ao clicar no campo o cursor vai para o fim
        do texto. Se já tem "1,000" lá, o usuário precisa apagar manualmente
        antes de digitar o novo valor — o que é chato e lento.

    SOLUÇÃO:
        Sobrescrevemos focusInEvent (chamado sempre que o campo ganha foco)
        e chamamos self.selectAll() logo depois do comportamento padrão.
        Isso seleciona todo o texto, então é só digitar e o valor antigo
        some automaticamente.

    COMO FUNCIONA O OVERRIDE (para estudantes):
        focusInEvent é um método da classe-pai (QDoubleSpinBox) que é chamado
        pelo Qt quando o widget recebe o foco. Ao sobrescrever, colocamos nossa
        lógica depois de chamar super().focusInEvent(event) — que mantém o
        comportamento original (trocar a borda para azul, etc.) — e então
        adicionamos selectAll() para selecionar o texto.

    Parâmetro decimais: quantas casas decimais mostrar (3 para qtd, 2 para valor)
    """

    def __init__(self, decimais: int = 2, parent=None):
        super().__init__(parent)
        self.setDecimals(decimais)
        self.setButtonSymbols(QDoubleSpinBox.NoButtons)  # sem setas

    def focusInEvent(self, event):
                # Chamado pelo Qt quando o widget recebe foco (clique ou Tab).
        super().focusInEvent(event)
        # selectAll() precisa ser chamado depois que o Qt terminar de processar
        # o evento de foco — por isso usamos um timer de 0ms (próximo ciclo)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self.selectAll)


# ══════════════════════════════════════════════════════════════════════════════
# DELEGATE — força maiúsculas em tempo real na coluna de descrição
# ══════════════════════════════════════════════════════════════════════════════

from PySide6.QtWidgets import QStyledItemDelegate

class _UpperDelegate(QStyledItemDelegate):
    """
    Delegate que substitui o editor padrão da célula por um QLineEdit
    configurado para converter o texto para maiúsculas a cada tecla pressionada.
    """
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.textChanged.connect(
            lambda txt, e=editor: (
                e.blockSignals(True),
                e.setText(txt.upper()),
                e.blockSignals(False),
            ) if txt != txt.upper() else None
        )
        return editor


# ══════════════════════════════════════════════════════════════════════════════
# TABELA CUSTOMIZADA — navegação com 1 clique e Tab
# ══════════════════════════════════════════════════════════════════════════════

class TabelaItens(QTableWidget):
    """
    QTableWidget com usabilidade melhorada para preenchimento rápido:

    - 1 clique na coluna de descrição (col 0) já abre a edição
    - Tab navega: descrição → quantidade → valor unitário → próxima linha
    - Enter na descrição vai direto para quantidade
    - Setas na tabela funcionam normalmente

    COMO FUNCIONA (para estudantes):
        Sobrescrevemos os métodos mousePressEvent e keyPressEvent da classe-pai.
        Isso é chamado de "override" — pegamos o evento antes que o Qt processe
        e adicionamos nossa lógica antes de (ou em vez de) chamar o original.
    """

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        idx = self.indexAt(event.pos())
        # Abre edição imediata com 1 clique na coluna de descrição
        if idx.isValid() and idx.column() == 0:
            self.editItem(self.item(idx.row(), idx.column()))

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        row = self.currentRow()
        col = self.currentColumn()

        if key == Qt.Key_Tab:
            # Ordem de tabulação: 0 (desc) → 1 (qtd) → 3 (valor) → próxima linha
            ordem = [0, 1, 3]
            if col in ordem:
                prox_idx = ordem.index(col) + 1
                if prox_idx < len(ordem):
                    prox_col = ordem[prox_idx]
                    self.setCurrentCell(row, prox_col)
                    w = self.cellWidget(row, prox_col)
                    if w:
                        w.setFocus()
                        if hasattr(w, 'selectAll'): w.selectAll()
                else:
                    # Fim da linha: desce para a descrição da linha seguinte
                    if row + 1 < self.rowCount():
                        self.setCurrentCell(row + 1, 0)
                        self.editItem(self.item(row + 1, 0))
            return  # não propaga o Tab padrão do Qt

        elif key in (Qt.Key_Return, Qt.Key_Enter):
            if col == 0:
                # Enter na descrição → vai para quantidade
                self.setCurrentCell(row, 1)
                w = self.cellWidget(row, 1)
                if w:
                    w.setFocus()
                    if hasattr(w, 'selectAll'): w.selectAll()
                return

        super().keyPressEvent(event)


# ══════════════════════════════════════════════════════════════════════════════
# DIÁLOGOS DE CADASTRO
# ══════════════════════════════════════════════════════════════════════════════

class NovaObraDialog(QDialog):
        # Janela para cadastrar uma nova obra.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar Nova Obra")
        self.setMinimumWidth(500)
        self.setStyleSheet(f"background:{WHITE}; color:{TXT};")
        form = QFormLayout(self)
        form.setSpacing(10); form.setContentsMargins(20,20,20,20)

        # Carrega empresas base + extras para o combo de faturamento
        import config as _cfg
        todas_empresas = list(_cfg.EMPRESAS_FATURADORAS.keys())
        try:
            extras = _load(_EMP)
            for sigla in extras:
                if sigla not in todas_empresas:
                    todas_empresas.append(sigla)
        except Exception:
            pass

        self._campos = {
            "nome": _fld(), "escola": _fld(),
            "faturamento": _combo(todas_empresas),
            "endereco": _fld(), "bairro": _fld(), "cep": _fld(),
            "cidade": _fld(), "uf": _fld("SP"), "contrato": _fld("0"),
        }
        rotulos = {
            "nome":"Nome da Obra *","escola":"Nome da Escola",
            "faturamento":"Faturamento","endereco":"Endereço de Entrega",
            "bairro":"Bairro","cep":"CEP","cidade":"Cidade",
            "uf":"UF","contrato":"Nº Contrato",
        }
        for k, v in self._campos.items():
            lbl = QLabel(rotulos[k]); lbl.setStyleSheet(f"color:{TXT};font-size:12px;")
            form.addRow(lbl, v)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._aceitar); bb.rejected.connect(self.reject)
        bb.button(QDialogButtonBox.Ok).setStyleSheet(
            f"background:{RED};color:white;font-weight:bold;"
            f"padding:6px 20px;border-radius:5px;border:none;")
        form.addRow(bb)

    def _aceitar(self):
        nome = self._campos["nome"].text().strip()
        if not nome:
            QMessageBox.warning(self,"Campo obrigatório","Informe o nome da obra."); return
        fat = self._campos["faturamento"]
        self.resultado = {
            "nome": nome.upper(),
            "escola": self._campos["escola"].text().strip(),
            "faturamento": fat.currentText() if isinstance(fat,QComboBox) else fat.text(),
            "endereco": self._campos["endereco"].text().strip(),
            "bairro": self._campos["bairro"].text().strip(),
            "cep": self._campos["cep"].text().strip(),
            "cidade": self._campos["cidade"].text().strip(),
            "uf": self._campos["uf"].text().strip() or "SP",
            "contrato": self._campos["contrato"].text().strip() or "0",
        }
        self.accept()


class NovoFornecedorDialog(QDialog):
        # Janela para cadastrar um novo fornecedor.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar Novo Fornecedor")
        self.setMinimumWidth(500)
        self.setStyleSheet(f"background:{WHITE}; color:{TXT};")
        form = QFormLayout(self)
        form.setSpacing(10); form.setContentsMargins(20,20,20,20)
        self._campos = {k: _fld() for k in
                        ["nome","razao","email","vendedor","telefone","pix"]}
        rotulos = {
            "nome":"Nome / Apelido *","razao":"Razão Social","email":"E-mail",
            "vendedor":"Vendedor","telefone":"Telefone","pix":"PIX / CNPJ",
        }
        for k, v in self._campos.items():
            lbl = QLabel(rotulos[k]); lbl.setStyleSheet(f"color:{TXT};font-size:12px;")
            form.addRow(lbl, v)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._aceitar); bb.rejected.connect(self.reject)
        bb.button(QDialogButtonBox.Ok).setStyleSheet(
            f"background:{RED};color:white;font-weight:bold;"
            f"padding:6px 20px;border-radius:5px;border:none;")
        form.addRow(bb)

    def _aceitar(self):
        nome = self._campos["nome"].text().strip()
        if not nome:
            QMessageBox.warning(self,"Campo obrigatório","Informe o nome do fornecedor."); return
        self.resultado = {k: v.text().strip() for k, v in self._campos.items()}
        self.resultado["nome"] = self.resultado["nome"].upper()
        self.accept()


# ══════════════════════════════════════════════════════════════════════════════
# DIÁLOGO — CADASTRAR NOVA EMPRESA FATURADORA
# ══════════════════════════════════════════════════════════════════════════════

class NovaEmpresaDialog(QDialog):
    """
    Janela para cadastrar uma nova empresa faturadora.

    MELHORIAS:
        - Upload de logo: o usuário seleciona qualquer PNG e o sistema
          copia automaticamente para assets/logos/ com o nome correto.
        - Obs. padrão pré-preenchida com o texto padrão do grupo
          (o usuário só precisa digitar o nome da empresa no final).
        - Todos os campos de texto forçam letras maiúsculas.
    """

    _CORES = [
        ("#C0392B", "Vermelho"),    ("#A93226", "Vermelho escuro"),
        ("#1E8449", "Verde"),        ("#1A5276", "Azul"),
        ("#784212", "Marrom"),       ("#117A65", "Verde água"),
        ("#6C3483", "Roxo"),         ("#1F618D", "Azul médio"),
        ("#B7950B", "Dourado"),      ("#555555", "Cinza"),
    ]

    # Texto base que já aparece preenchido no campo Obs. padrão
    _OBS_BASE = "NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA\n"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastrar Nova Empresa Faturadora")
        self.setMinimumWidth(560)
        self.setStyleSheet(f"background:{WHITE}; color:{TXT};")

        self._logo_origem = None   # caminho do PNG selecionado pelo usuário

        form = QFormLayout(self)
        form.setSpacing(10); form.setContentsMargins(20, 20, 20, 20)

        def lbl(t):
            l = QLabel(t); l.setStyleSheet(f"color:{TXT}; font-size:12px;"); return l

        # ── campos de texto — todos forçam maiúsculas ─────────────────────────
        def _fld_upper(placeholder=""):
            f = _fld()
            if placeholder: f.setPlaceholderText(placeholder)
            f.textChanged.connect(lambda txt, w=f: (
                w.blockSignals(True),
                w.setText(txt.upper()),
                w.blockSignals(False)
            ) if txt != txt.upper() else None)
            return f

        self._nome     = _fld_upper("SIGLA USADA NO BOTÃO — EX: NOVA")
        self._razao    = _fld_upper("NOVA EMPRESA CONSTRUTORA LTDA")
        self._endereco = _fld_upper()
        self._telefone = _fld()   # telefone pode ter símbolos, não forçamos
        self._email    = _fld()   # e-mail é case-insensitive, mantemos livre

        # Obs. padrão — QTextEdit para suportar quebra de linha, já pré-preenchido
        self._obs = QTextEdit()
        self._obs.setPlainText(self._OBS_BASE)
        self._obs.setFixedHeight(68)
        self._obs.setStyleSheet(CSS_TEXTAREA)
        self._obs.setToolTip(
            "Texto que aparece no bloco de faturamento do PDF.\n"
            "Complete com o nome da empresa na segunda linha.")
        # Força maiúsculas ao digitar
        self._obs.textChanged.connect(self._obs_maiusculas)

        # ── seletor de logo ───────────────────────────────────────────────────
        logo_row = QHBoxLayout(); logo_row.setSpacing(8)
        self._lbl_logo = QLabel("Nenhum arquivo selecionado")
        self._lbl_logo.setStyleSheet(
            f"font-size:11px; color:{TXT_S}; background:{RO_BG};"
            f"border:1.5px solid {BDR}; border-radius:5px; padding:4px 10px;")
        self._lbl_logo.setMinimumWidth(300)

        btn_logo = QPushButton("📁  Escolher Logo")
        btn_logo.setFixedHeight(32)
        btn_logo.setCursor(Qt.PointingHandCursor)
        btn_logo.setStyleSheet(f"""
            QPushButton {{
                background:#ECF0F1; color:{TXT}; font-size:12px;
                border:1.5px solid {BDR}; border-radius:5px; padding:0 12px;
            }}
            QPushButton:hover {{ background:#D5DBDB; }}
        """)
        btn_logo.clicked.connect(self._escolher_logo)

        # Preview miniatura do logo
        self._preview_logo = QLabel()
        self._preview_logo.setFixedSize(48, 32)
        self._preview_logo.setAlignment(Qt.AlignCenter)
        self._preview_logo.setStyleSheet(
            f"border:1px solid {BDR}; border-radius:4px; background:{WHITE};")
        self._preview_logo.setVisible(False)

        logo_row.addWidget(self._lbl_logo, 1)
        logo_row.addWidget(btn_logo)
        logo_row.addWidget(self._preview_logo)

        aviso_logo = QLabel(
            "Formatos aceitos: PNG. Tamanho recomendado: 300×100 px (proporção 3:1).\n"
            "O arquivo será copiado automaticamente para  assets/logos/")
        aviso_logo.setStyleSheet(f"font-size:10px; color:#7D6A6A;")
        aviso_logo.setWordWrap(True)

        # ── cor do botão ──────────────────────────────────────────────────────
        self._cor_combo = QComboBox(); self._cor_combo.setStyleSheet(CSS_COMBO)
        for hx, nm in self._CORES:
            self._cor_combo.addItem(f"  {nm}  ({hx})", hx)
        self._cor_combo.view().setStyleSheet(
            f"color:{TXT};background:{WHITE};"
            f"selection-background-color:{SEL};selection-color:{GRAY};")

        # ── monta o formulário ────────────────────────────────────────────────
        form.addRow(lbl("Sigla / Botão *"),        self._nome)
        form.addRow(lbl("Razão Social *"),          self._razao)
        form.addRow(lbl("Endereço"),                self._endereco)
        form.addRow(lbl("Telefone"),                self._telefone)
        form.addRow(lbl("E-mail"),                  self._email)
        form.addRow(lbl("Obs. padrão no PDF"),      self._obs)
        form.addRow(lbl("Logo da empresa"),         logo_row)
        form.addRow(aviso_logo)
        form.addRow(lbl("Cor do botão"),            self._cor_combo)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._aceitar); bb.rejected.connect(self.reject)
        bb.button(QDialogButtonBox.Ok).setStyleSheet(
            f"background:{RED};color:white;font-weight:bold;"
            f"padding:6px 20px;border-radius:5px;border:none;")
        form.addRow(bb)

    def _obs_maiusculas(self):
                # Mantém o conteúdo do campo Obs. sempre em maiúsculas.
        txt = self._obs.toPlainText()
        upper = txt.upper()
        if txt != upper:
            cur = self._obs.textCursor()
            pos = cur.position()
            self._obs.blockSignals(True)
            self._obs.setPlainText(upper)
            # Restaura posição do cursor
            cur.setPosition(min(pos, len(upper)))
            self._obs.setTextCursor(cur)
            self._obs.blockSignals(False)

    def _escolher_logo(self):
                # Abre seletor de arquivo PNG e mostra preview.
        from PySide6.QtWidgets import QFileDialog
        from PySide6.QtGui import QPixmap
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Logo da Empresa",
            os.path.expanduser("~"),
            "Imagens PNG (*.png);;Todos os arquivos (*.*)"
        )
        if not caminho:
            return
        self._logo_origem = caminho
        nome_curto = os.path.basename(caminho)
        self._lbl_logo.setText(f"✅  {nome_curto}")
        self._lbl_logo.setStyleSheet(
            f"font-size:11px; color:{GREEN}; background:#F0FFF4;"
            f"border:1.5px solid {GREEN}; border-radius:5px; padding:4px 10px;")

        # Mostra preview miniatura
        pix = QPixmap(caminho)
        if not pix.isNull():
            self._preview_logo.setPixmap(
                pix.scaled(48, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self._preview_logo.setVisible(True)

    def _aceitar(self):
        nome  = self._nome.text().strip().upper()
        razao = self._razao.text().strip()
        if not nome:
            QMessageBox.warning(self, "Obrigatório", "Informe a sigla."); return
        if not razao:
            QMessageBox.warning(self, "Obrigatório", "Informe a Razão Social."); return

        hx  = self._cor_combo.currentData()
        h   = hx.lstrip("#")
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        nome_logo = f"logo_{nome.lower().replace(' ','_').replace('&','')}.png"

        # Copia o logo para assets/logos/ se o usuário escolheu um arquivo
        if self._logo_origem and os.path.isfile(self._logo_origem):
            import shutil
            destino_logo = os.path.join(
                os.path.normpath(os.path.join(
                    os.path.dirname(__file__), '..', '..', '..', 'assets', 'logos'
                )),
                nome_logo
            )
            try:
                os.makedirs(os.path.dirname(destino_logo), exist_ok=True)
                shutil.copy2(self._logo_origem, destino_logo)
            except Exception as e:
                QMessageBox.warning(self, "Aviso",
                    f"Não foi possível copiar o logo:\n{e}\n\n"
                    f"Você pode copiar manualmente para:\nassets/logos/{nome_logo}")

        self.resultado = {
            "sigla":        nome,
            "razao_social": razao,
            "endereco":     self._endereco.text().strip(),
            "telefone":     self._telefone.text().strip(),
            "email":        self._email.text().strip(),
            "obs_padrao":   self._obs.toPlainText().strip(),
            "logo":         nome_logo,
            "cor_header":   list(rgb),
            "cor_btn":      hx,
        }
        self.accept()


# ══════════════════════════════════════════════════════════════════════════════
# WIDGET PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class PedidoWidget(QWidget):
    """
    Aba "Pedido de Compra" — formulário completo para emissão de pedidos.

    Seções:
        1. Dados do Pedido  — número, data, prazo, condição/forma de pagamento
        2. Obra             — seleção e dados de entrega
        3. Fornecedor       — seleção e dados de contato
        4. Itens + Desconto — tabela melhorada + campo de desconto % ou R$
        5. Observação       — campo livre para informações extras
        6. Gerar / Limpar   — botões por empresa + botão limpar
    """

    def __init__(self):
        super().__init__()
        self._obras   = _load(_OBR)
        self._forns   = _load(_FOR)
        self._service = PedidoService()
        # Estado interno do desconto
        self._desconto_tipo = "%"   # "%" ou "R$"
        self._arquivo_pedido_atual = None  # caminho do rascunho carregado/salvo
        self._pedido_editando_numero = None  # número do pedido aberto pela tela Pedidos Gerados
        self._fornecedor_pix = ""
        self._fornecedor_favorecido = ""
        self._build()

    # ══════════════════════════════════════════════════════════════════════════
    # CONSTRUÇÃO DA INTERFACE
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        self.setStyleSheet(f"background:{BG};")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        inner = QWidget(); inner.setStyleSheet(f"background:{BG};")
        vl = QVBoxLayout(inner)
        vl.setContentsMargins(20,16,20,24); vl.setSpacing(14)

        titulo = QLabel("Novo Pedido de Compra")
        titulo.setStyleSheet(
            f"font-size:20px;font-weight:bold;color:{GRAY};background:transparent;")
        data_lbl = QLabel(f"Data: {datetime.now().strftime('%d/%m/%Y')}")
        data_lbl.setStyleSheet(f"font-size:12px;color:{TXT_S};background:transparent;")
        th = QHBoxLayout()
        th.addWidget(titulo); th.addStretch(); th.addWidget(data_lbl)
        vl.addLayout(th)

        vl.addWidget(self._sec_dados())
        vl.addWidget(self._sec_obra())
        vl.addWidget(self._sec_fornecedor())
        vl.addWidget(self._sec_itens())
        vl.addWidget(self._sec_obs())
        vl.addWidget(self._sec_faturadora())

        scroll.setWidget(inner)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0); lay.addWidget(scroll)

    # ── Seção 1: Dados do Pedido ──────────────────────────────────────────────

    def _sec_dados(self):
        box = _grp("Dados do Pedido")
        hl  = QHBoxLayout(); hl.setSpacing(12)
        self.e_num = _fld(proximo_numero_pedido())
        self.e_num.setToolTip("Gerado automaticamente. Pode editar manualmente.")
        self.e_num.editingFinished.connect(self._num_digitado_manualmente)
        self.e_data = _fld(datetime.now().strftime("%d/%m/%Y"))
        self.e_prazo = QSpinBox()
        self.e_prazo.setRange(0,365); self.e_prazo.setValue(0)
        self.e_prazo.setSuffix(" dias"); self.e_prazo.setStyleSheet(CSS_INPUT)
        self.e_cond = _combo([""] + list(CONDICOES_PAGAMENTO))
        self.e_cond.setEditable(True); self.e_cond.setInsertPolicy(QComboBox.NoInsert)
        self.e_cond.lineEdit().setStyleSheet(CSS_INPUT)
        self.e_cond.setCurrentIndex(0)
        self.e_cond.lineEdit().setPlaceholderText("Selecione/Digite")
        self.e_cond.setToolTip("Selecione ou digite. Ex: 28/35/42  ou  À VISTA")
        self.e_forma = _combo(FORMAS_PAGAMENTO)
        self.e_forma.setEditable(True); self.e_forma.setInsertPolicy(QComboBox.NoInsert)
        self.e_forma.lineEdit().setStyleSheet(CSS_INPUT)
        # Comprador — botão que abre o seletor
        self._comprador_atual = COMPRADOR_PADRAO
        vl_comp = QVBoxLayout(); vl_comp.setSpacing(4)
        lbl_comp = QLabel("COMPRADOR")
        lbl_comp.setStyleSheet(
            f"font-size:11px;color:{TXT_S};font-weight:600;background:transparent;")
        self.btn_comprador = QPushButton(f"👤  {COMPRADOR_PADRAO}")
        self.btn_comprador.setFixedHeight(32)
        self.btn_comprador.setMinimumWidth(130)
        self.btn_comprador.setCursor(Qt.PointingHandCursor)
        self.btn_comprador.setToolTip("Clique para trocar o comprador")
        self.btn_comprador.setStyleSheet(f"""
            QPushButton {{
                background:{WHITE}; color:{TXT};
                border:1.5px solid {BDR}; border-radius:5px;
                font-size:12px; font-weight:bold;
                padding:0 10px; text-align:left;
            }}
            QPushButton:hover {{
                background:#FEF0EF; border-color:{RED}; color:{RED};
            }}
            QPushButton:pressed {{ background:{SEL}; }}
        """)
        self.btn_comprador.clicked.connect(self._selecionar_comprador)
        vl_comp.addWidget(lbl_comp)
        vl_comp.addWidget(self.btn_comprador)

        hl.addLayout(_col("Nº Pedido",      self.e_num,   110))
        hl.addLayout(_col("Data",           self.e_data,  110))
        hl.addLayout(_col("Prazo entrega",  self.e_prazo, 110))
        hl.addLayout(_col("Condição pagto", self.e_cond,  130))
        hl.addLayout(_col("Forma pagto",    self.e_forma, 120))
        hl.addLayout(vl_comp)
        hl.addStretch()
        box.setLayout(hl); return box

    def _selecionar_comprador(self):
        # Abre o seletor de comprador e atualiza o botão
        from app.ui.dialogs.selecionar_comprador_dialog import SelecionarCompradorDialog
        dlg = SelecionarCompradorDialog(self, titulo_relatorio="Pedido de Compra")
        if dlg.exec() and dlg.comprador_selecionado:
            self._comprador_atual = dlg.comprador_selecionado
            self.btn_comprador.setText(f"👤  {self._comprador_atual}")

    def _num_digitado_manualmente(self):
        """
        Chamado quando o usuário edita o campo Nº Pedido e sai dele.
        Não altera contador aqui: o contador só deve mudar após gerar
        um pedido com sucesso.
        """
        texto = self.e_num.text().strip()
        if not texto:
            self.e_num.setText(proximo_numero_pedido())
            return
        try:
            int(texto)
        except Exception:
            self.e_num.setText(proximo_numero_pedido())

    # ── Seção 2: Obra ─────────────────────────────────────────────────────────

    def _sec_obra(self):
        box = _grp("Obra")
        vl  = QVBoxLayout(); vl.setSpacing(10)
        hl1 = QHBoxLayout(); hl1.setSpacing(10)
        self.e_obra = QComboBox()
        self.e_obra.setEditable(True); self.e_obra.setInsertPolicy(QComboBox.NoInsert)
        self.e_obra.setMinimumWidth(340); self.e_obra.setStyleSheet(CSS_COMBO)
        self.e_obra.view().setStyleSheet(
            f"color:{TXT};background:{WHITE};"
            f"selection-background-color:{SEL};selection-color:{GRAY};")
        self.e_obra.currentTextChanged.connect(self._fill_obra)
        btn_nova = _btn("+ Nova Obra", RED, mini=True)
        btn_nova.clicked.connect(self._cad_obra)
        lbl_o = QLabel("Obra:")
        lbl_o.setStyleSheet(
            f"color:{TXT_S};font-size:11px;font-weight:600;background:transparent;")
        hl1.addWidget(lbl_o); hl1.addWidget(self.e_obra)
        hl1.addWidget(btn_nova); hl1.addStretch()
        vl.addLayout(hl1)
        hl2 = QHBoxLayout(); hl2.setSpacing(10)
        self.e_escola   = _fld()
        self.e_fat      = _combo(list(EMPRESAS_FATURADORAS.keys()))
        self.e_end      = _fld(); self.e_bairro  = _fld()
        self.e_cep      = _fld(); self.e_cidade  = _fld()
        self.e_uf       = _fld("SP"); self.e_contrato = _fld("0")
        self.e_fat.currentIndexChanged.connect(self._atualizar_obs_padrao)
        hl2.addLayout(_col("Escola / Nome",  self.e_escola,  220))
        hl2.addLayout(_col("Faturamento",    self.e_fat,     130))
        hl2.addLayout(_col("Endereço",       self.e_end,     230))
        hl2.addLayout(_col("Bairro",         self.e_bairro,  160))
        hl2.addLayout(_col("CEP",            self.e_cep,      90))
        hl2.addLayout(_col("Cidade",         self.e_cidade,  160))
        hl2.addLayout(_col("UF",             self.e_uf,       46))
        hl2.addLayout(_col("Contrato",       self.e_contrato, 90))
        hl2.addStretch()
        vl.addLayout(hl2)
        self._reload_obras()
        box.setLayout(vl); return box

    # ── Seção 3: Fornecedor ───────────────────────────────────────────────────

    def _sec_fornecedor(self):
        box = _grp("Fornecedor")
        vl  = QVBoxLayout(); vl.setSpacing(10)
        hl1 = QHBoxLayout(); hl1.setSpacing(10)
        self.e_fsel = QComboBox()
        self.e_fsel.setEditable(True); self.e_fsel.setInsertPolicy(QComboBox.NoInsert)
        self.e_fsel.setMinimumWidth(340); self.e_fsel.setStyleSheet(CSS_COMBO)
        self.e_fsel.view().setStyleSheet(
            f"color:{TXT};background:{WHITE};"
            f"selection-background-color:{SEL};selection-color:{GRAY};")
        self.e_fsel.currentTextChanged.connect(self._fill_forn)
        btn_novo = _btn("+ Novo Fornecedor", RED, mini=True)
        btn_novo.clicked.connect(self._cad_forn)
        lbl_f = QLabel("Fornecedor:")
        lbl_f.setStyleSheet(
            f"color:{TXT_S};font-size:11px;font-weight:600;background:transparent;")
        hl1.addWidget(lbl_f); hl1.addWidget(self.e_fsel)
        hl1.addWidget(btn_novo); hl1.addStretch()
        vl.addLayout(hl1)
        hl2 = QHBoxLayout(); hl2.setSpacing(10)
        self.e_fn    = _fld(); self.e_fraz  = _fld()
        self.e_fem   = _fld(); self.e_fvend = _fld(); self.e_ftel  = _fld()
        hl2.addLayout(_col("Fornecedor",   self.e_fn,    180))
        hl2.addLayout(_col("Razão Social", self.e_fraz,  260))
        hl2.addLayout(_col("E-mail",       self.e_fem,   220))
        hl2.addLayout(_col("Vendedor",     self.e_fvend, 160))
        hl2.addLayout(_col("Telefone",     self.e_ftel,  160))
        hl2.addStretch()
        vl.addLayout(hl2)
        self._reload_forns()
        box.setLayout(vl); return box

    # ── Seção 4: Itens + Desconto ─────────────────────────────────────────────

    def _sec_itens(self):
        """
        Tabela de itens com painel de desconto logo abaixo.

        ESTRUTURA VISUAL:
            [+ Adicionar]  [✕ Remover]              Subtotal: R$ X.XXX,XX
            ┌─────────────────────────────────────────────────────────────┐
            │ Descrição │ Qtdade │ Unid. │ Vlr Unit. │ Vlr Total         │
            │ Item A    │  2     │  M3   │  R$ 300   │  R$ 600,00        │
            └─────────────────────────────────────────────────────────────┘
            ╔═════════════════════════════════════════════════════════════╗
            ║ Desconto: [% Porcentagem] [R$ Valor fixo]  [ 10,00 ] %     ║
            ║           Desconto aplicado: − R$ 60,00   TOTAL: R$ 540,00 ║
            ╚═════════════════════════════════════════════════════════════╝
        """
        box = _grp("Itens do Pedido")
        vl  = QVBoxLayout(); vl.setSpacing(10)

        # Barra de botões + subtotal
        hl = QHBoxLayout()
        btn_add = _btn("+ Adicionar item", RED, mini=True)
        btn_rem = _btn("✕  Remover linha", "#555555", mini=True)
        btn_add.clicked.connect(self._add_row)
        btn_rem.clicked.connect(self._rem_row)
        self.lbl_subtotal = QLabel("Subtotal: R$ 0,00")
        self.lbl_subtotal.setStyleSheet(
            f"font-size:13px;font-weight:bold;color:{TXT_S};background:transparent;")
        hl.addWidget(btn_add); hl.addWidget(btn_rem)
        hl.addStretch(); hl.addWidget(self.lbl_subtotal)
        vl.addLayout(hl)

        # Tabela customizada — setColumnCount DEVE vir antes de setHorizontalHeaderLabels
        self.tabela = TabelaItens(self)
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(
            ["Descrição do material","Qtdade","Unid.","Vlr Unitário (R$)","Vlr Total"])
        # Delegate que força maiúsculas em tempo real na coluna de descrição (col 0)
        self.tabela.setItemDelegateForColumn(0, _UpperDelegate(self.tabela))
        hh = self.tabela.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for col, w in [(1,76),(2,76),(3,148),(4,118)]:
            hh.setSectionResizeMode(col, QHeaderView.Fixed)
            self.tabela.setColumnWidth(col, w)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.verticalHeader().setDefaultSectionSize(36)
        self.tabela.setMinimumHeight(220)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setStyleSheet(f"""
            QTableWidget {{
                gridline-color:#EAE0DF; font-size:12px; color:{TXT};
                border:1.5px solid #E0D0CF; border-radius:8px; background:{WHITE};
            }}
            QHeaderView::section {{
                background:{GRAY}; color:white; padding:6px 8px;
                font-size:11px; font-weight:bold; border:none;
            }}
            QHeaderView::section:first {{ border-top-left-radius:6px; }}
            QHeaderView::section:last  {{ border-top-right-radius:6px; }}
            QTableWidget::item {{ padding:3px 8px; color:{TXT}; }}
            QTableWidget::item:selected {{ background:{SEL}; color:{GRAY}; }}
            QTableWidget::item:alternate {{ background:#FAF6F6; }}
        """)
        self.tabela.itemChanged.connect(self._recalc)
        vl.addWidget(self.tabela)

        # Painel de desconto
        vl.addWidget(self._criar_painel_desconto())

        box.setLayout(vl); return box

    def _criar_painel_desconto(self):
        """
        Cria o painel de desconto com botões de alternância % / R$.

        LÓGICA DOS BOTÕES DE ALTERNÂNCIA:
            São dois QPushButton checkable lado a lado.
            O ativo fica vermelho (css_ativo), o inativo fica cinza (css_inativo).
            Ao clicar em um, chama _set_tipo_desconto() que:
                1. Atualiza self._desconto_tipo
                2. Reaplica os estilos
                3. Zera o spin para o usuário digitar o novo valor
                4. Chama _recalc() para atualizar os totais
        """
        painel = QWidget()
        painel.setStyleSheet(f"""
            QWidget {{
                background:#FFF8F8;
                border:1.5px solid #E8D5D3;
                border-radius:8px;
            }}
        """)
        hl = QHBoxLayout(painel)
        hl.setContentsMargins(14,10,14,10); hl.setSpacing(12)

        lbl = QLabel("Desconto:")
        lbl.setStyleSheet(
            f"font-size:12px;font-weight:bold;color:{TXT_S};"
            f"background:transparent;border:none;")
        hl.addWidget(lbl)

        # Estilos dos botões de alternância
        self._css_btn_ativo = f"""
            QPushButton {{
                background:{RED}; color:white;
                font-size:12px; font-weight:bold;
                border-radius:6px; border:none; padding:0 10px;
            }}
        """
        self._css_btn_inativo = f"""
            QPushButton {{
                background:#F0EDED; color:{TXT_S};
                font-size:12px; font-weight:normal;
                border-radius:6px; border:1.5px solid {BDR};
                padding:0 10px;
            }}
            QPushButton:hover {{ background:#E8DEDE; }}
        """

        self.btn_pct = QPushButton("% Porcentagem")
        self.btn_val = QPushButton("R$  Valor fixo")
        for b in (self.btn_pct, self.btn_val):
            b.setFixedHeight(32); b.setFixedWidth(140); b.setCheckable(True)

        # Começa no modo % (porcentagem ativo)
        self.btn_pct.setStyleSheet(self._css_btn_ativo)
        self.btn_val.setStyleSheet(self._css_btn_inativo)
        self.btn_pct.setChecked(True)

        self.btn_pct.clicked.connect(lambda: self._set_tipo_desconto("%"))
        self.btn_val.clicked.connect(lambda: self._set_tipo_desconto("R$"))
        hl.addWidget(self.btn_pct); hl.addWidget(self.btn_val)

        # Spin do valor do desconto
        self.spin_desconto = QDoubleSpinBox()
        self.spin_desconto.setRange(0, 999_999)
        self.spin_desconto.setDecimals(2)
        self.spin_desconto.setValue(0.0)
        self.spin_desconto.setFixedWidth(110); self.spin_desconto.setFixedHeight(32)
        self.spin_desconto.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.spin_desconto.setStyleSheet(CSS_INPUT)
        self.spin_desconto.setToolTip(
            "Modo %: digite 10 para 10% de desconto\n"
            "Modo R$: digite 150 para R$ 150,00 de desconto")
        self.spin_desconto.valueChanged.connect(self._recalc)
        hl.addWidget(self.spin_desconto)

        # Sufixo dinâmico que mostra o modo atual
        self.lbl_sufixo = QLabel("%")
        self.lbl_sufixo.setStyleSheet(
            f"font-size:14px;font-weight:bold;color:{RED};"
            f"background:transparent;border:none;")
        hl.addWidget(self.lbl_sufixo)
        hl.addStretch()

        # Área de resultado: desconto aplicado + total
        info_vl = QVBoxLayout(); info_vl.setSpacing(3)
        self.lbl_desconto_info = QLabel("")
        self.lbl_desconto_info.setAlignment(Qt.AlignRight)
        self.lbl_desconto_info.setVisible(False)
        self.lbl_desconto_info.setStyleSheet(
            f"font-size:11px;color:{GREEN};background:transparent;border:none;")
        self.lbl_total = QLabel("TOTAL: R$ 0,00")
        self.lbl_total.setAlignment(Qt.AlignRight)
        self.lbl_total.setStyleSheet(
            f"font-size:16px;font-weight:bold;color:{RED};"
            f"background:transparent;border:none;")
        info_vl.addWidget(self.lbl_desconto_info)
        info_vl.addWidget(self.lbl_total)
        hl.addLayout(info_vl)

        return painel

    # ── Seção 5: Observação ───────────────────────────────────────────────────

    def _sec_obs(self):
        box = _grp("Observação (opcional)")
        vl  = QVBoxLayout(); vl.setSpacing(6)
        aviso = QLabel("Informações extras para o fornecedor — "
                       "ex.: 'DESCARREGAR NO PORTÃO ATRÁS DA ESCOLA'")
        aviso.setWordWrap(True)
        aviso.setStyleSheet(f"font-size:11px;color:{TXT_S};background:transparent;")
        vl.addWidget(aviso)
        self.e_obs = QTextEdit()
        self.e_obs.setMaximumHeight(68)
        self.e_obs.setPlaceholderText(
            "Ex: DESCARREGAR MATERIAL NO PORTÃO ATRAS DA ESCOLA")
        self.e_obs.setStyleSheet(CSS_TEXTAREA)
        vl.addWidget(self.e_obs)
        # lbl_obs_padrao existe como atributo mas NÃO aparece na tela.
        # O obs_padrao da empresa vai direto para o PDF — não na interface.
        self.lbl_obs_padrao = QLabel("")   # mantido para compatibilidade interna
        self.lbl_obs_padrao.setVisible(False)
        box.setLayout(vl); return box

    # ── Seção 6: Empresa faturadora + Limpar ──────────────────────────────────

    def _sec_faturadora(self):
        box = _grp("Gerar Pedido — Escolha a Empresa Faturadora")
        vl  = QVBoxLayout(); vl.setSpacing(10)
        av = QLabel(
            "A Nota Fiscal será emitida em nome da empresa selecionada. "
            "O PDF é salvo automaticamente em pedidos_gerados/.")
        av.setWordWrap(True)
        av.setStyleSheet(f"font-size:11px;color:{TXT_S};line-height:1.5;")
        vl.addWidget(av)

        br = QHBoxLayout(); br.setSpacing(8)

        # Container dos botões de empresa (recriado ao adicionar/remover)
        self._frame_empresas = QHBoxLayout()
        self._frame_empresas.setSpacing(8)
        self._rebuild_botoes_empresa()
        br.addLayout(self._frame_empresas)
        br.addSpacing(6)

        # Botão "＋" — cadastrar nova empresa
        btn_nova = QPushButton("＋")
        btn_nova.setFixedSize(36, 46)
        btn_nova.setToolTip("Cadastrar nova empresa faturadora")
        btn_nova.setCursor(Qt.PointingHandCursor)
        btn_nova.setStyleSheet(f"""
            QPushButton {{
                background:#ECF0F1; color:{RED}; font-size:18px; font-weight:bold;
                border-radius:8px; border:2px dashed {RED};
            }}
            QPushButton:hover   {{ background:#FDECEA; }}
            QPushButton:pressed {{ background:{SEL}; }}
        """)
        btn_nova.clicked.connect(self._cad_empresa)
        br.addWidget(btn_nova)

        # Botão "🗑" — excluir empresa cadastrada pelo usuário
        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(36, 46)
        btn_del.setToolTip("Excluir empresa cadastrada pelo usuário")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet("""
            QPushButton {
                background:#ECF0F1; color:#888; font-size:16px;
                border-radius:8px; border:1.5px solid #BDC3C7;
            }
            QPushButton:hover   { background:#F5B7B1; color:#C0392B; }
            QPushButton:pressed { background:#FADBD8; }
        """)
        btn_del.clicked.connect(self._excluir_empresa)
        br.addWidget(btn_del)

        br.addStretch()

        btn_salvar_rasc = QPushButton("💾  Salvar Pedido")
        btn_salvar_rasc.setFixedHeight(46); btn_salvar_rasc.setMinimumWidth(150)
        btn_salvar_rasc.setToolTip("Salva o pedido atual como rascunho para continuar depois.")
        btn_salvar_rasc.setStyleSheet("""
            QPushButton {
                background:#1E8449; color:white; font-size:12px;
                font-weight:bold; border-radius:8px;
                border:none; letter-spacing:0.3px;
            }
            QPushButton:hover   { background:#196F3D; }
            QPushButton:pressed { background:#145A32; }
        """)
        btn_salvar_rasc.clicked.connect(self._salvar_pedido_rascunho)
        br.addWidget(btn_salvar_rasc)

        btn_carregar_rasc = QPushButton("📂  Carregar Pedido")
        btn_carregar_rasc.setFixedHeight(46); btn_carregar_rasc.setMinimumWidth(160)
        btn_carregar_rasc.setToolTip("Carrega um pedido salvo anteriormente.")
        btn_carregar_rasc.setStyleSheet("""
            QPushButton {
                background:#2874A6; color:white; font-size:12px;
                font-weight:bold; border-radius:8px;
                border:none; letter-spacing:0.3px;
            }
            QPushButton:hover   { background:#21618C; }
            QPushButton:pressed { background:#1B4F72; }
        """)
        btn_carregar_rasc.clicked.connect(self._carregar_pedido_rascunho)
        br.addWidget(btn_carregar_rasc)

        btn_limpar = QPushButton("🗑  Limpar / Novo Pedido")
        btn_limpar.setFixedHeight(46); btn_limpar.setMinimumWidth(180)
        btn_limpar.setToolTip("Limpa todos os campos para um novo pedido.")
        btn_limpar.setStyleSheet("""
            QPushButton {
                background:#ECF0F1; color:#555555; font-size:12px;
                font-weight:bold; border-radius:8px;
                border:1.5px solid #BDC3C7; letter-spacing:0.3px;
            }
            QPushButton:hover   { background:#D5DBDB; color:#333333; }
            QPushButton:pressed { background:#BFC9CA; }
        """)
        btn_limpar.clicked.connect(self._limpar_formulario)
        br.addWidget(btn_limpar)

        vl.addLayout(br)
        box.setLayout(vl)
        return box

    def _rebuild_botoes_empresa(self):
                # Reconstrói os botões de empresa (base do config + extras do usuário).
        while self._frame_empresas.count():
            item = self._frame_empresas.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for nome, dados in self._get_todas_empresas().items():
            cor_raw = dados.get("cor_header", (80, 80, 80))
            if isinstance(cor_raw, (list, tuple)):
                r, g, b = cor_raw
                cor = f"#{r:02X}{g:02X}{b:02X}"
            else:
                cor = str(cor_raw)
            cor = dados.get("cor_btn", cor)   # extras têm cor_btn diretamente em hex

            b = QPushButton(nome)
            b.setFixedHeight(46); b.setMinimumWidth(90)
            b.setStyleSheet(f"""
                QPushButton {{
                    background:{cor}; color:white; font-size:13px;
                    font-weight:bold; border-radius:8px; border:none;
                    letter-spacing:0.5px; padding:0 10px;
                }}
                QPushButton:hover   {{ background:{cor}CC; }}
                QPushButton:pressed {{ background:{cor}99; }}
            """)
            b.clicked.connect(lambda _, e=nome: self._gerar(e))
            self._frame_empresas.addWidget(b)

    def _get_todas_empresas(self):
                # Mescla empresas do config.py com as extras salvas pelo usuário.
        import config as _cfg
        todas = dict(_cfg.EMPRESAS_FATURADORAS)
        for sigla, dados in _load(_EMP).items():
            if sigla not in todas:
                todas[sigla] = dados
        return todas

    def _cad_empresa(self):
                # Abre diálogo de cadastro e salva a nova empresa em empresas_extra.json.
        dlg = NovaEmpresaDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return
        r     = dlg.resultado
        sigla = r["sigla"]
        if sigla in self._get_todas_empresas():
            QMessageBox.information(self, "Já existe",
                f"A empresa '{sigla}' já está cadastrada."); return

        extras = _load(_EMP)
        extras[sigla] = {k: v for k, v in r.items() if k != "sigla"}
        _save(_EMP, extras)
        self._rebuild_botoes_empresa()
        QMessageBox.information(self, "Empresa cadastrada!",
            f"'{sigla}' adicionada com sucesso.\n\n"
            f"Dica: adicione o logo em  assets/logos/{r['logo']}")

    def _excluir_empresa(self):
                # Permite excluir apenas empresas cadastradas pelo usuário (não as 5 originais).
        from PySide6.QtWidgets import QInputDialog
        extras = _load(_EMP)
        if not extras:
            QMessageBox.information(self, "Nada para excluir",
                "Não há empresas cadastradas pelo usuário.\n\n"
                "As 5 empresas originais não podem ser removidas."); return

        escolha, ok = QInputDialog.getItem(
            self, "Excluir empresa",
            "Selecione a empresa que deseja remover:",
            list(extras.keys()), 0, False)
        if not ok or not escolha:
            return

        resp = QMessageBox.question(
            self, "Confirmar exclusão",
            f"Deseja realmente excluir  '{escolha}'?\n\nEsta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return

        del extras[escolha]
        _save(_EMP, extras)
        self._rebuild_botoes_empresa()
        QMessageBox.information(self, "Removida",
            f"Empresa '{escolha}' removida com sucesso.")

    # ══════════════════════════════════════════════════════════════════════════
    # LÓGICA DE DESCONTO
    # ══════════════════════════════════════════════════════════════════════════

    def _set_tipo_desconto(self, tipo):
        """
        Alterna entre % e R$ CONVERTENDO o valor automaticamente.

        LÓGICA DE CONVERSÃO:
            Quando o usuário digita 10 no modo % e troca para R$, o sistema
            pega o subtotal atual e calcula quanto 10% representa em reais,
            colocando esse valor no spin.

            Exemplo:
                Subtotal = R$ 1.000,00
                Modo % → digita 10
                Clica em "R$ Valor fixo"
                → spin vira 100,00  (porque 10% de 1000 = 100)

            E o inverso também funciona:
                Modo R$ → digita 100
                Subtotal = R$ 1.000,00
                Clica em "% Porcentagem"
                → spin vira 10,00  (porque 100/1000 × 100 = 10%)

            Se o subtotal for zero, zera o spin (não tem como calcular %).
        """
        if self._desconto_tipo == tipo:
            return  # já está no modo correto

        # Calcula o subtotal atual lendo a tabela
        subtotal = sum(
            (self.tabela.cellWidget(r, 1).value() *
             self.tabela.cellWidget(r, 3).value())
            for r in range(self.tabela.rowCount())
            if self.tabela.cellWidget(r, 1) and self.tabela.cellWidget(r, 3)
        )

        valor_atual = self.spin_desconto.value()

        # Bloqueia o sinal para não disparar _recalc durante a conversão
        self.spin_desconto.blockSignals(True)

        if tipo == "R$":
            # Vinha de % → converte para R$
            if subtotal > 0:
                novo_valor = round(subtotal * valor_atual / 100, 2)
            else:
                novo_valor = 0.0
            self.spin_desconto.setValue(novo_valor)
            self.lbl_sufixo.setText("R$")
            self.btn_val.setStyleSheet(self._css_btn_ativo)
            self.btn_pct.setStyleSheet(self._css_btn_inativo)
            self.btn_val.setChecked(True); self.btn_pct.setChecked(False)
        else:
            # Vinha de R$ → converte para %
            if subtotal > 0:
                novo_valor = round(valor_atual / subtotal * 100, 2)
            else:
                novo_valor = 0.0
            self.spin_desconto.setValue(novo_valor)
            self.lbl_sufixo.setText("%")
            self.btn_pct.setStyleSheet(self._css_btn_ativo)
            self.btn_val.setStyleSheet(self._css_btn_inativo)
            self.btn_pct.setChecked(True); self.btn_val.setChecked(False)

        self.spin_desconto.blockSignals(False)
        self._desconto_tipo = tipo
        self._recalc()  # atualiza os labels com o novo valor convertido

    def _calcular_desconto_reais(self, subtotal):
        """
        Converte o valor digitado no spin para R$ conforme o modo:
            %  → desconto = subtotal × valor ÷ 100
            R$ → desconto = valor digitado

        Limita o desconto ao subtotal (total nunca fica negativo).
        """
        valor = self.spin_desconto.value()
        if self._desconto_tipo == "%":
            desconto = round(subtotal * valor / 100, 2)
        else:
            desconto = round(valor, 2)
        return min(desconto, subtotal)

    # ══════════════════════════════════════════════════════════════════════════
    # LÓGICA DA TABELA
    # ══════════════════════════════════════════════════════════════════════════

    def _add_row(self):
        """
        Insere linha na tabela.

        MELHORIAS NOS SPINBOXES:
            - Começam com valor 0 (em vez de 1 / R$ 0,00 fixo)
            - Ao receber foco (clique ou Tab), selecionam TODO o conteúdo
              automaticamente — assim o usuário digita por cima sem precisar
              apagar o valor anterior manualmente
            - Sem setas laterais (NoButtons) — mais espaço para digitar
            - Sem prefixo "R$ " fixo — o campo mostra só o número limpo

        POR QUE SELECIONAR TUDO AO FOCAR?
            O comportamento padrão do QDoubleSpinBox coloca o cursor no fim
            do texto. Se já tem "1,000" lá e o usuário clica, ele vê
            "1,000|" e precisa apagar tudo antes de digitar.
            Com selectAll() no focusInEvent, ele clica, vê "1,000" selecionado
            e é só digitar o novo valor.
        """
        r = self.tabela.rowCount()
        self.tabela.blockSignals(True)
        self.tabela.insertRow(r)

        # Col 0: descrição (editável com 1 clique)
        item_desc = QTableWidgetItem("")
        item_desc.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
        self.tabela.setItem(r, 0, item_desc)

        # Col 1: quantidade — começa ZERADA, seleciona tudo ao focar
        sq = _SpinFoco(decimais=3)
        sq.setRange(0, 999_999)
        sq.setValue(0.0)
        sq.setStyleSheet(CSS_INPUT)
        sq.valueChanged.connect(self._recalc)
        self.tabela.setCellWidget(r, 1, sq)

        # Col 2: unidade
        cu = QComboBox(); cu.addItems(UNIDADES); cu.setStyleSheet(CSS_COMBO)
        cu.view().setStyleSheet(
            f"color:{TXT};background:{WHITE};"
            f"selection-background-color:{SEL};selection-color:{GRAY};")
        self.tabela.setCellWidget(r, 2, cu)

        # Col 3: valor unitário — começa ZERADO, seleciona tudo ao focar
        sv = _SpinFoco(decimais=2)
        sv.setRange(0, 9_999_999)
        sv.setValue(0.0)
        sv.setStyleSheet(CSS_INPUT)
        sv.valueChanged.connect(self._recalc)
        self.tabela.setCellWidget(r, 3, sv)

        # Col 4: total calculado (somente leitura)
        it = QTableWidgetItem("0,00")
        it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        it.setForeground(QColor(RED)); it.setBackground(QColor("#FEF0EF"))
        self.tabela.setItem(r, 4, it)

        self.tabela.blockSignals(False)
        self.tabela.setCurrentCell(r, 0)
        self.tabela.editItem(self.tabela.item(r, 0))

    def _rem_row(self):
        r = self.tabela.currentRow()
        if r >= 0: self.tabela.removeRow(r); self._recalc()

    def _recalc(self):
        """
        Recalcula subtotal, desconto e total.
        Chamado automaticamente quando qualquer valor ou desconto muda.
        """
        subtotal = 0.0
        self.tabela.blockSignals(True)
        for r in range(self.tabela.rowCount()):
            wq = self.tabela.cellWidget(r, 1)
            wv = self.tabela.cellWidget(r, 3)
            if wq and wv:
                vl = round(wq.value() * wv.value(), 2); subtotal += vl
                it = self.tabela.item(r, 4)
                if it: it.setText(self._fmt(vl))
        self.tabela.blockSignals(False)

        desconto_reais = self._calcular_desconto_reais(subtotal)
        total = round(subtotal - desconto_reais, 2)

        self.lbl_subtotal.setText(f"Subtotal: R$ {self._fmt(subtotal)}")

        if desconto_reais > 0:
            info = f"Desconto aplicado: − R$ {self._fmt(desconto_reais)}"
            if self._desconto_tipo == "%":
                info += f"  ({self.spin_desconto.value():.2f}%)"
            self.lbl_desconto_info.setText(info)
            self.lbl_desconto_info.setVisible(True)
        else:
            self.lbl_desconto_info.setVisible(False)

        self.lbl_total.setText(f"TOTAL: R$ {self._fmt(total)}")

    # ══════════════════════════════════════════════════════════════════════════
    # LÓGICA DE OBRAS / FORNECEDORES
    # ══════════════════════════════════════════════════════════════════════════

    def _reload_obras(self):
        lst = sorted(self._obras.keys())
        self.e_obra.blockSignals(True)
        self.e_obra.clear()
        self.e_obra.addItem("-- Selecione ou digite a obra --")
        self.e_obra.addItems(lst)
        self.e_obra.setCompleter(_make_completer(lst, self))
        self.e_obra.blockSignals(False)

    def _reload_forns(self):
        lst = sorted(self._forns.keys())
        self.e_fsel.blockSignals(True)
        self.e_fsel.clear()
        self.e_fsel.addItem("-- Selecione ou digite o fornecedor --")
        self.e_fsel.addItems(lst)
        self.e_fsel.setCompleter(_make_completer(lst, self))
        self.e_fsel.blockSignals(False)

    def _fill_obra(self, txt):
        d = self._obras.get(txt, {})
        if not d: return
        self.e_escola.setText(d.get('escola',''))
        idx = self.e_fat.findText(d.get('faturamento','BRASUL'))
        if idx >= 0: self.e_fat.setCurrentIndex(idx)
        self.e_end.setText(d.get('endereco',''))
        self.e_bairro.setText(d.get('bairro',''))
        self.e_cep.setText(d.get('cep',''))
        self.e_cidade.setText(d.get('cidade',''))
        self.e_uf.setText(d.get('uf','SP'))
        self.e_contrato.setText(d.get('contrato','0'))

    def _fill_forn(self, txt):
        d = self._forns.get(txt, {})
        if not d:
            self._fornecedor_pix = ""
            self._fornecedor_favorecido = ""
            return
        self.e_fn.setText(txt)
        self.e_fraz.setText(d.get('razao',''))
        self.e_fem.setText(d.get('email',''))
        self.e_fvend.setText(d.get('vendedor',''))
        self.e_ftel.setText(d.get('telefone',''))
        self._fornecedor_pix = (
            d.get('pix') or d.get('PIX') or d.get('cnpj_pix') or d.get('chave_pix') or ""
        )
        self._fornecedor_favorecido = (
            d.get('favorecido') or d.get('dados_bancarios') or d.get('dados bancários') or d.get('banco') or ""
        )

    def _atualizar_obs_padrao(self):
        """
        Mantido apenas para compatibilidade com o sinal conectado em _sec_obra().
        O obs_padrao da empresa vai direto para o PDF — não aparece na tela.
        """
        pass  # nada a fazer na interface

    def _cad_obra(self):
        dlg = NovaObraDialog(self)
        if dlg.exec() != QDialog.Accepted: return
        r = dlg.resultado; nome = r['nome']
        if nome in self._obras:
            QMessageBox.information(self,"Já existe",f"Obra '{nome}' já cadastrada."); return
        self._obras[nome] = {k:v for k,v in r.items() if k != 'nome'}
        _save(_OBR, self._obras); self._reload_obras()
        idx = self.e_obra.findText(nome)
        if idx >= 0: self.e_obra.setCurrentIndex(idx)
        QMessageBox.information(self,"Salvo!",f"'{nome}' cadastrada com sucesso.")

    def _cad_forn(self):
        dlg = NovoFornecedorDialog(self)
        if dlg.exec() != QDialog.Accepted: return
        r = dlg.resultado; nome = r['nome']
        if nome in self._forns:
            QMessageBox.information(self,"Já existe",
                f"Fornecedor '{nome}' já cadastrado."); return
        self._forns[nome] = {k:v for k,v in r.items() if k != 'nome'}
        _save(_FOR, self._forns); self._reload_forns()
        idx = self.e_fsel.findText(nome)
        if idx >= 0: self.e_fsel.setCurrentIndex(idx)
        QMessageBox.information(self,"Salvo!",f"'{nome}' cadastrado com sucesso.")

    # ══════════════════════════════════════════════════════════════════════════
    # SALVAR / CARREGAR RASCUNHO DO PEDIDO
    # ══════════════════════════════════════════════════════════════════════════

    def _nome_rascunho_padrao(self):
        """Gera um nome amigável para o arquivo JSON do rascunho."""
        obra = (self.e_obra.currentText() or "SEM_OBRA").strip()
        fornecedor = (self.e_fn.text() or self.e_fsel.currentText() or "SEM_FORNECEDOR").strip()
        numero = (self.e_num.text() or "SEM_NUMERO").strip()

        bruto = f"PEDIDO_{numero}_{obra}_{fornecedor}".upper()
        permitido = []
        for ch in bruto:
            if ch.isalnum() or ch in (" ", "_", "-"):
                permitido.append(ch)
            else:
                permitido.append("_")
        nome = "".join(permitido).replace(" ", "_")
        while "__" in nome:
            nome = nome.replace("__", "_")
        return f"{nome}.json"

    def _coletar_rascunho_pedido(self):
        """Coleta todos os campos da tela em um dicionário serializável."""
        itens = []
        for r in range(self.tabela.rowCount()):
            desc_item = self.tabela.item(r, 0)
            wq = self.tabela.cellWidget(r, 1)
            wu = self.tabela.cellWidget(r, 2)
            wv = self.tabela.cellWidget(r, 3)

            descricao = desc_item.text().strip() if desc_item else ""
            quantidade = wq.value() if wq else 0.0
            unidade = wu.currentText() if wu else "UNID."
            valor_unitario = wv.value() if wv else 0.0

            # Salva também linhas vazias parcialmente preenchidas.
            if descricao or quantidade or valor_unitario:
                itens.append({
                    "descricao": descricao,
                    "quantidade": quantidade,
                    "unidade": unidade,
                    "valor_unitario": valor_unitario,
                })

        return {
            "versao": 1,
            "salvo_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "numero": self.e_num.text().strip(),
            "data_pedido": self.e_data.text().strip(),
            "prazo_entrega": self.e_prazo.value(),
            "condicao_pagamento": self.e_cond.currentText(),
            "forma_pagamento": self.e_forma.currentText(),
            "comprador": self._comprador_atual,

            "obra": self.e_obra.currentText(),
            "empresa_faturamento": self.e_fat.currentText(),
            "escola": self.e_escola.text(),
            "endereco": self.e_end.text(),
            "bairro": self.e_bairro.text(),
            "cep": self.e_cep.text(),
            "cidade": self.e_cidade.text(),
            "uf": self.e_uf.text(),
            "contrato": self.e_contrato.text(),

            "fornecedor_combo": self.e_fsel.currentText(),
            "fornecedor_nome": self.e_fn.text(),
            "fornecedor_razao": self.e_fraz.text(),
            "fornecedor_email": self.e_fem.text(),
            "fornecedor_vendedor": self.e_fvend.text(),
            "fornecedor_telefone": self.e_ftel.text(),

            "desconto_tipo": self._desconto_tipo,
            "desconto_valor": self.spin_desconto.value(),
            "observacao": self.e_obs.toPlainText(),

            "itens": itens,
        }

    def _salvar_pedido_rascunho(self):
        """Salva o pedido atual em JSON para continuar depois."""
        os.makedirs(_PED_RASC, exist_ok=True)

        caminho_padrao = self._arquivo_pedido_atual
        if not caminho_padrao:
            caminho_padrao = os.path.join(_PED_RASC, self._nome_rascunho_padrao())

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar pedido para continuar depois",
            caminho_padrao,
            "Pedidos salvos (*.json)"
        )
        if not caminho:
            return

        if not caminho.lower().endswith(".json"):
            caminho += ".json"

        try:
            dados = self._coletar_rascunho_pedido()
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)

            self._arquivo_pedido_atual = caminho
            QMessageBox.information(
                self,
                "Pedido salvo",
                f"✅ Pedido salvo com sucesso para continuar depois.\n\n{caminho}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao salvar",
                f"Não foi possível salvar o pedido.\n\n{e}"
            )

    def _carregar_pedido_rascunho(self):
        """Carrega um pedido salvo em JSON."""
        os.makedirs(_PED_RASC, exist_ok=True)

        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Carregar pedido salvo",
            self._arquivo_pedido_atual or _PED_RASC,
            "Pedidos salvos (*.json)"
        )
        if not caminho:
            return

        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)

            self._aplicar_rascunho_pedido(dados)
            self._arquivo_pedido_atual = caminho

            QMessageBox.information(
                self,
                "Pedido carregado",
                f"✅ Pedido carregado com sucesso.\n\n{caminho}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao carregar",
                f"Não foi possível carregar o pedido salvo.\n\n{e}"
            )

    def _set_combo_text(self, combo, texto):
        """Seleciona texto existente ou define texto digitável em combo editável."""
        texto = "" if texto is None else str(texto)
        idx = combo.findText(texto)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        else:
            combo.setCurrentText(texto)

    def _aplicar_rascunho_pedido(self, dados):
        """Aplica na tela os dados carregados do JSON."""
        # Dados do pedido
        self.e_num.setText(str(dados.get("numero", proximo_numero_pedido())))
        self.e_data.setText(str(dados.get("data_pedido", datetime.now().strftime("%d/%m/%Y"))))
        self.e_prazo.setValue(int(dados.get("prazo_entrega", 5) or 5))

        self._set_combo_text(self.e_cond, dados.get("condicao_pagamento", ""))
        self._set_combo_text(self.e_forma, dados.get("forma_pagamento", ""))

        self._comprador_atual = str(dados.get("comprador", COMPRADOR_PADRAO) or COMPRADOR_PADRAO)
        self.btn_comprador.setText(f"👤  {self._comprador_atual}")

        # Obra e dados de entrega
        self.e_obra.blockSignals(True)
        self._set_combo_text(self.e_obra, dados.get("obra", ""))
        self.e_obra.blockSignals(False)

        self._set_combo_text(self.e_fat, dados.get("empresa_faturamento", ""))
        self.e_escola.setText(str(dados.get("escola", "")))
        self.e_end.setText(str(dados.get("endereco", "")))
        self.e_bairro.setText(str(dados.get("bairro", "")))
        self.e_cep.setText(str(dados.get("cep", "")))
        self.e_cidade.setText(str(dados.get("cidade", "")))
        self.e_uf.setText(str(dados.get("uf", "SP")))
        self.e_contrato.setText(str(dados.get("contrato", "0")))

        # Fornecedor
        self.e_fsel.blockSignals(True)
        self._set_combo_text(self.e_fsel, dados.get("fornecedor_combo", ""))
        self.e_fsel.blockSignals(False)

        self.e_fn.setText(str(dados.get("fornecedor_nome", "")))
        self.e_fraz.setText(str(dados.get("fornecedor_razao", "")))
        self.e_fem.setText(str(dados.get("fornecedor_email", "")))
        self.e_fvend.setText(str(dados.get("fornecedor_vendedor", "")))
        self.e_ftel.setText(str(dados.get("fornecedor_telefone", "")))

        # Itens
        self.tabela.setRowCount(0)
        for item in dados.get("itens", []):
            self._add_row()
            r = self.tabela.rowCount() - 1

            it_desc = self.tabela.item(r, 0)
            if it_desc:
                it_desc.setText(str(item.get("descricao", "")).upper())

            wq = self.tabela.cellWidget(r, 1)
            wu = self.tabela.cellWidget(r, 2)
            wv = self.tabela.cellWidget(r, 3)

            if wq:
                wq.setValue(float(item.get("quantidade", 0) or 0))
            if wu:
                unidade = str(item.get("unidade", "UNID."))
                idx_u = wu.findText(unidade)
                if idx_u >= 0:
                    wu.setCurrentIndex(idx_u)
                else:
                    wu.setCurrentText(unidade)
            if wv:
                wv.setValue(float(item.get("valor_unitario", 0) or 0))

        # Desconto e observação
        tipo = str(dados.get("desconto_tipo", "%") or "%")
        valor = float(dados.get("desconto_valor", 0) or 0)

        if tipo != self._desconto_tipo:
            self._set_tipo_desconto(tipo)

        self.spin_desconto.blockSignals(True)
        self.spin_desconto.setValue(valor)
        self.spin_desconto.blockSignals(False)
        self._desconto_tipo = tipo
        self.lbl_sufixo.setText("R$" if tipo == "R$" else "%")
        if tipo == "R$":
            self.btn_val.setStyleSheet(self._css_btn_ativo)
            self.btn_pct.setStyleSheet(self._css_btn_inativo)
            self.btn_val.setChecked(True)
            self.btn_pct.setChecked(False)
        else:
            self.btn_pct.setStyleSheet(self._css_btn_ativo)
            self.btn_val.setStyleSheet(self._css_btn_inativo)
            self.btn_pct.setChecked(True)
            self.btn_val.setChecked(False)

        self.e_obs.setPlainText(str(dados.get("observacao", "")))
        self._recalc()


    # ══════════════════════════════════════════════════════════════════════════
    # EDITAR PEDIDO EXISTENTE
    # ══════════════════════════════════════════════════════════════════════════

    def carregar_pedido_existente(self, pedido, itens):
        """
        Carrega um pedido já salvo no banco para edição na tela Pedido de Compra.

        Observação:
        - Ao gerar novamente usando o mesmo número, o PedidoService atualiza
          o registro existente e recria os itens daquele pedido.
        - Campos que não existem no banco antigo são preenchidos pelo cadastro
          da obra/fornecedor quando possível.
        """
        try:
            self._pedido_editando_numero = str(pedido["numero"])

            # Dados principais
            self.e_num.setText(str(pedido["numero"] or ""))
            self.e_data.setText(str(pedido["data_pedido"] or datetime.now().strftime("%d/%m/%Y")))
            self.e_prazo.setValue(int(pedido["prazo_entrega"] or 0))

            self._set_combo_text(self.e_cond, str(pedido["condicao_pagamento"] or ""))
            self._set_combo_text(self.e_forma, str(pedido["forma_pagamento"] or ""))

            comprador = str(pedido["comprador"] or COMPRADOR_PADRAO)
            self._comprador_atual = comprador
            self.btn_comprador.setText(f"👤  {comprador}")

            # Obra
            obra = str(pedido["obra_nome"] or "")
            self.e_obra.blockSignals(True)
            self._set_combo_text(self.e_obra, obra)
            self.e_obra.blockSignals(False)
            self._fill_obra(obra)

            if pedido["escola"]:
                self.e_escola.setText(str(pedido["escola"] or ""))

            empresa = str(pedido["empresa_faturadora"] or "")
            if empresa:
                self._set_combo_text(self.e_fat, empresa)
                self._atualizar_obs_padrao()

            # Fornecedor
            fornecedor = str(pedido["fornecedor_nome"] or "")
            self.e_fsel.blockSignals(True)
            self._set_combo_text(self.e_fsel, fornecedor)
            self.e_fsel.blockSignals(False)
            self._fill_forn(fornecedor)

            self.e_fn.setText(fornecedor)
            self.e_fraz.setText(str(pedido["fornecedor_razao"] or ""))

            # Itens
            self.tabela.setRowCount(0)

            for item in itens:
                self._add_row()
                row = self.tabela.rowCount() - 1

                desc = self.tabela.item(row, 0)
                if desc:
                    desc.setText(str(item["descricao"] or "").upper())

                qtd = self.tabela.cellWidget(row, 1)
                if qtd:
                    qtd.setValue(float(item["quantidade"] or 0))

                un = self.tabela.cellWidget(row, 2)
                if un:
                    unidade = str(item["unidade"] or "UNID.")
                    idx = un.findText(unidade)
                    if idx >= 0:
                        un.setCurrentIndex(idx)
                    else:
                        un.setCurrentText(unidade)

                vl = self.tabela.cellWidget(row, 3)
                if vl:
                    vl.setValue(float(item["valor_unitario"] or 0))

            # Desconto e observações não existem em todos os bancos antigos.
            self._desconto_tipo = "%"
            self.spin_desconto.setValue(0.0)
            self._set_tipo_desconto("%")

            self._arquivo_pedido_atual = None
            self._recalc()

            QMessageBox.information(
                self,
                "Modo edição",
                f"Pedido Nº {self._pedido_editando_numero} carregado para edição.\n\n"
                "Após alterar, clique no botão da empresa para gerar novamente."
            )

        except Exception as e:
            QMessageBox.critical(self, "Erro ao carregar pedido", str(e))


    # ══════════════════════════════════════════════════════════════════════════
    # GERAR PDF
    # ══════════════════════════════════════════════════════════════════════════

    def _gerar(self, empresa):
        try:
            prazo = int(self.e_prazo.value())
            cond = (self.e_cond.currentText() or "").strip()
            if prazo <= 0:
                raise ValueError("Informe o prazo de entrega maior que 0 dias.")
            if not cond:
                raise ValueError("Informe a condição de pagamento antes de gerar o pedido.")

            dto = self._montar_dto(empresa)
            path = self._service.gerar_pdf(dto)

            numero_gerado = str(dto.numero).strip()
            numero_em_edicao = str(self._pedido_editando_numero or "").strip()

            # Trava de edição:
            # - Se estiver regravando o mesmo pedido carregado para edição,
            #   não altera a sequência global.
            # - Se mudou o número (ou não está em modo edição), atualiza o contador.
            if not numero_em_edicao or numero_gerado != numero_em_edicao:
                atualizar_numero_pedido(numero_gerado)

            msg = QMessageBox(self)
            msg.setWindowTitle("Pedido gerado!")
            msg.setText(
                f"<b>Pedido Nº {dto.numero} — {empresa}</b><br><br>"
                f"Salvo em:<br><code>{path}</code>"
            )
            msg.setIcon(QMessageBox.Information)
            b_open = msg.addButton(" Abrir PDF ", QMessageBox.ActionRole)
            msg.addButton("OK", QMessageBox.AcceptRole)
            msg.exec()

            if msg.clickedButton() == b_open:
                self._abrir_arquivo(path)

            self._arquivo_pedido_atual = None
            self._pedido_editando_numero = None
            self.e_num.setText(proximo_numero_pedido())

        except ValueError as e:
            QMessageBox.warning(self, "Campos obrigatórios", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _montar_dto(self, empresa):
        """
        Lê os campos e monta o PedidoDTO para o gerador de PDF.
        O desconto é calculado em R$ antes de passar ao DTO.
        """
        itens = []
        for r in range(self.tabela.rowCount()):
            di = self.tabela.item(r, 0)
            wq = self.tabela.cellWidget(r, 1)
            wu = self.tabela.cellWidget(r, 2)
            wv = self.tabela.cellWidget(r, 3)
            if not di or not di.text().strip(): continue
            itens.append(ItemPedidoDTO(
                descricao=di.text().strip(),
                quantidade=wq.value() if wq else 1.0,
                unidade=wu.currentText() if wu else "UNID.",
                valor_unitario=wv.value() if wv else 0.0,
            ))
        subtotal = sum(i.valor_total for i in itens)
        desconto_reais = self._calcular_desconto_reais(subtotal)

        fornecedor_chave = self.e_fsel.currentText().strip()
        fornecedor_dados = self._forns.get(fornecedor_chave, {})
        fornecedor_pix = (
            self._fornecedor_pix
            or fornecedor_dados.get('pix')
            or fornecedor_dados.get('PIX')
            or fornecedor_dados.get('cnpj_pix')
            or fornecedor_dados.get('chave_pix')
            or ""
        )
        fornecedor_favorecido = (
            self._fornecedor_favorecido
            or fornecedor_dados.get('favorecido')
            or fornecedor_dados.get('dados_bancarios')
            or fornecedor_dados.get('dados bancários')
            or fornecedor_dados.get('banco')
            or ""
        )

        return PedidoDTO(
            numero=self.e_num.text().strip(),
            data_pedido=self.e_data.text(),
            empresa_faturadora=empresa,
            comprador=self._comprador_atual,
            obra=self.e_obra.currentText(),
            escola=self.e_escola.text(),
            endereco_entrega=self.e_end.text(),
            bairro_entrega=self.e_bairro.text(),
            cep_entrega=self.e_cep.text(),
            cidade_entrega=self.e_cidade.text(),
            uf_entrega=self.e_uf.text(),
            contrato_obra=self.e_contrato.text(),
            fornecedor_nome=self.e_fn.text(),
            fornecedor_razao=self.e_fraz.text(),
            fornecedor_email=self.e_fem.text(),
            fornecedor_vendedor=self.e_fvend.text(),
            fornecedor_telefone=self.e_ftel.text(),
            fornecedor_pix=fornecedor_pix,
            fornecedor_favorecido=fornecedor_favorecido,
            prazo_entrega=self.e_prazo.value(),
            condicao_pagamento=self.e_cond.currentText(),
            forma_pagamento=self.e_forma.currentText(),
            observacao_extra=self.e_obs.toPlainText().strip(),
            desconto=desconto_reais,
            itens=itens,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # LIMPAR FORMULÁRIO
    # ══════════════════════════════════════════════════════════════════════════

    def _limpar_formulario(self):
                # Reseta todos os campos. Pede confirmação antes.
        resp = QMessageBox.question(
            self,"Limpar formulário",
            "Deseja limpar todos os campos e começar um novo pedido?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes: return

        self.e_num.setText(proximo_numero_pedido())
        self.e_data.setText(datetime.now().strftime("%d/%m/%Y"))
        self.e_prazo.setValue(0)
        self.e_cond.setCurrentIndex(0); self.e_forma.setCurrentIndex(0)
        self._comprador_atual = COMPRADOR_PADRAO
        self.btn_comprador.setText(f"👤  {COMPRADOR_PADRAO}")

        self.e_obra.blockSignals(True); self.e_obra.setCurrentIndex(0)
        self.e_obra.blockSignals(False)
        for w in (self.e_escola,self.e_end,self.e_bairro,self.e_cep,self.e_cidade):
            w.clear()
        self.e_fat.setCurrentIndex(0); self.e_uf.setText("SP")
        self.e_contrato.setText("0")

        self.e_fsel.blockSignals(True); self.e_fsel.setCurrentIndex(0)
        self.e_fsel.blockSignals(False)
        for w in (self.e_fn,self.e_fraz,self.e_fem,self.e_fvend,self.e_ftel):
            w.clear()

        self.tabela.setRowCount(0)
        self.lbl_subtotal.setText("Subtotal: R$ 0,00")
        self.lbl_desconto_info.setVisible(False)
        self.lbl_total.setText("TOTAL: R$ 0,00")

        self._desconto_tipo = "%"
        self.spin_desconto.setValue(0.0)
        self._set_tipo_desconto("%")

        self.e_obs.clear(); self.lbl_obs_padrao.setVisible(False)
        self._pedido_editando_numero = None

    # ══════════════════════════════════════════════════════════════════════════
    # INTEGRAÇÃO COTAÇÃO → PEDIDO (Sprint 3)
    # ══════════════════════════════════════════════════════════════════════════

    def preencher_de_cotacao(self, dados):
                # Preenche o formulário a partir de uma cotação vencedora (Sprint 3).
        idx = self.e_obra.findText(dados.get("obra",""))
        if idx >= 0: self.e_obra.setCurrentIndex(idx)
        idx = self.e_fsel.findText(dados.get("fornecedor",""))
        if idx >= 0: self.e_fsel.setCurrentIndex(idx)
        idx = self.e_cond.findText(dados.get("condicao_pagamento",""))
        if idx >= 0: self.e_cond.setCurrentIndex(idx)
        idx = self.e_forma.findText(dados.get("forma_pagamento",""))
        if idx >= 0: self.e_forma.setCurrentIndex(idx)
        self.e_prazo.setValue(int(dados.get("prazo_entrega",5)))
        self.tabela.setRowCount(0)
        for item in dados.get("itens",[]):
            self._add_row()
            r = self.tabela.rowCount() - 1
            self.tabela.item(r,0).setText(item.get("descricao",""))
            wq = self.tabela.cellWidget(r,1); wu = self.tabela.cellWidget(r,2)
            wv = self.tabela.cellWidget(r,3)
            if wq: wq.setValue(float(item.get("quantidade",1)))
            if wu:
                idx = wu.findText(item.get("unidade","UNID."))
                if idx >= 0: wu.setCurrentIndex(idx)
            if wv: wv.setValue(float(item.get("preco_vencedor",0)))
        self._recalc()

    def preencher_da_cotacao(self, fornecedor: str, obra: str,
                              empresa: str, itens: list):
        """
        Preenche o formulário a partir da aba Cotacao.
        Chamado pelo cotacao_widget apos clicar em Gerar Pedido.

        Parametros:
            fornecedor : nome do fornecedor vencedor
            obra       : nome da obra selecionada na cotacao
            empresa    : empresa faturadora selecionada na cotacao
            itens      : lista de dicts com chaves:
                         descricao, quantidade, unidade,
                         valor_unitario, valor_total
        """
        # Limpa tabela sem confirmacao
        self.tabela.setRowCount(0)
        self.lbl_subtotal.setText("Subtotal: R$ 0,00")
        self.lbl_desconto_info.setVisible(False)
        self.lbl_total.setText("TOTAL: R$ 0,00")
        self._desconto_tipo = "%"
        self.spin_desconto.blockSignals(True)
        self.spin_desconto.setValue(0.0)
        self.spin_desconto.blockSignals(False)

        # Numero e data atualizados
        self.e_num.setText(proximo_numero_pedido())
        self.e_data.setText(datetime.now().strftime("%d/%m/%Y"))
        # Mantém o comprador atual selecionado

        # Obra
        self.e_obra.blockSignals(True)
        idx = self.e_obra.findText(obra)
        if idx >= 0:
            self.e_obra.setCurrentIndex(idx)
            self._fill_obra(obra)
        elif obra:
            self.e_obra.setCurrentText(obra)
        self.e_obra.blockSignals(False)

        # Empresa faturadora
        idx_emp = self.e_fat.findText(empresa)
        if idx_emp >= 0:
            self.e_fat.setCurrentIndex(idx_emp)

        # Fornecedor
        self.e_fsel.blockSignals(True)
        forn_upper = fornecedor.upper()
        idx_f = self.e_fsel.findText(forn_upper)
        if idx_f >= 0:
            self.e_fsel.setCurrentIndex(idx_f)
            self._fill_forn(forn_upper)
        else:
            self.e_fn.setText(forn_upper)
        self.e_fsel.blockSignals(False)

        # Itens
        for item in itens:
            self._add_row()
            r = self.tabela.rowCount() - 1
            desc = str(item.get("descricao", "")).strip().upper()
            it_desc = self.tabela.item(r, 0)
            if it_desc:
                it_desc.setText(desc)
            wq = self.tabela.cellWidget(r, 1)
            wu = self.tabela.cellWidget(r, 2)
            wv = self.tabela.cellWidget(r, 3)
            if wq:
                wq.setValue(float(item.get("quantidade") or 1))
            if wu:
                unid = str(item.get("unidade", "UNID.")).strip().upper()
                idx_u = wu.findText(unid)
                if idx_u >= 0:
                    wu.setCurrentIndex(idx_u)
            if wv:
                wv.setValue(float(item.get("valor_unitario") or 0))

        self._recalc()

    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _abrir_arquivo(path):
        try:
            if sys.platform == "win32": os.startfile(path)
            elif sys.platform == "darwin": subprocess.run(["open", path])
            else: subprocess.run(["xdg-open", path])
        except Exception: pass

    @staticmethod
    def _fmt(v):
                # Formata R$: 1234.5 → '1.234,50'
        return f"{v:,.2f}".replace(",","X").replace(".",",").replace("X",".")