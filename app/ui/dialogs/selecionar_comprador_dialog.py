# app/ui/dialogs/selecionar_comprador_dialog.py
# Diálogo para escolher o comprador antes de gerar a Relação de Pedidos.


import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QFrame,
    QMessageBox, QStackedWidget, QWidget, QSizePolicy,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor

from app.ui.style import (
    RED, GRAY, WHITE, BG, BDR, TXT, TXT_S, SEL, HOV, GREEN, BLUE,
    btn_solid, btn_outline,
)
from app.core import funcionarios as func_svc


class SelecionarCompradorDialog(QDialog):

    def __init__(self, parent=None, titulo_relatorio: str = "Relação de Pedidos"):
        super().__init__(parent)
        self.setWindowTitle("Comprador responsável")
        self.setMinimumWidth(400)
        self.setMinimumHeight(460)
        self.setStyleSheet(f"background:{WHITE}; color:{TXT};")
        self.comprador_selecionado: str | None = None
        self._titulo_relatorio = titulo_relatorio
        self._modo_gerenciar = False
        self._build()
        self._atualizar_lista()

    # ══════════════════════════════════════════════════════════════════════════
    # CONSTRUÇÃO
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        vl = QVBoxLayout(self)
        vl.setContentsMargins(24, 20, 24, 20)
        vl.setSpacing(14)

        # ── Cabeçalho ─────────────────────────────────────────────────────────
        lbl_titulo = QLabel("Selecionar Comprador")
        lbl_titulo.setStyleSheet(
            f"font-size:16px; font-weight:bold; color:{GRAY}; background:transparent;")
        vl.addWidget(lbl_titulo)

        self._lbl_sub = QLabel(f"Para: {self._titulo_relatorio}")
        self._lbl_sub.setStyleSheet(
            f"font-size:11px; color:{TXT_S}; background:transparent;")
        vl.addWidget(self._lbl_sub)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:#E8DEDE;"); sep.setFixedHeight(1)
        vl.addWidget(sep)

        # ── Stack: seleção | gerenciamento ────────────────────────────────────
        self._stack = QStackedWidget()
        vl.addWidget(self._stack, 1)

        self._stack.addWidget(self._build_pagina_selecao())
        self._stack.addWidget(self._build_pagina_gerenciar())
        self._stack.setCurrentIndex(0)

        # ── Rodapé de botões ──────────────────────────────────────────────────
        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"background:#E8DEDE;"); sep2.setFixedHeight(1)
        vl.addWidget(sep2)

        hl_btns = QHBoxLayout(); hl_btns.setSpacing(10)

        self._btn_gerenciar = btn_outline("⚙  Gerenciar funcionários")
        self._btn_gerenciar.clicked.connect(self._toggle_gerenciar)
        hl_btns.addWidget(self._btn_gerenciar)

        hl_btns.addStretch()

        self._btn_cancelar = btn_outline("Cancelar")
        self._btn_cancelar.clicked.connect(self.reject)
        hl_btns.addWidget(self._btn_cancelar)

        self._btn_confirmar = btn_solid("🖨  Gerar Relatório", RED)
        self._btn_confirmar.clicked.connect(self._confirmar)
        hl_btns.addWidget(self._btn_confirmar)

        vl.addLayout(hl_btns)

    # ── Página 1: seleção ─────────────────────────────────────────────────────

    def _build_pagina_selecao(self) -> QWidget:
        pg = QWidget()
        pg.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(pg); vl.setContentsMargins(0,0,0,0); vl.setSpacing(10)

        lbl = QLabel("Escolha o comprador responsável pelo relatório:")
        lbl.setStyleSheet(f"font-size:12px; color:{TXT}; background:transparent;")
        lbl.setWordWrap(True)
        vl.addWidget(lbl)

        self._lista = QListWidget()
        self._lista.setStyleSheet(f"""
            QListWidget {{
                background:{WHITE}; border:1.5px solid {BDR};
                border-radius:8px; font-size:13px; color:{TXT};
                outline:none; padding:4px;
            }}
            QListWidget::item {{
                padding:10px 14px;
                border-radius:6px;
                margin:2px 0;
            }}
            QListWidget::item:hover {{
                background:{HOV}; color:{RED};
            }}
            QListWidget::item:selected {{
                background:{SEL}; color:{GRAY};
                font-weight:bold;
            }}
        """)
        self._lista.setSpacing(2)
        self._lista.itemDoubleClicked.connect(self._confirmar)
        vl.addWidget(self._lista, 1)

        lbl_dica = QLabel("💡  Clique duplo para confirmar rapidamente")
        lbl_dica.setStyleSheet(f"font-size:10px; color:{TXT_S}; background:transparent;")
        vl.addWidget(lbl_dica)
        return pg

    # ── Página 2: gerenciar ───────────────────────────────────────────────────

    def _build_pagina_gerenciar(self) -> QWidget:
        pg = QWidget()
        pg.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(pg); vl.setContentsMargins(0,0,0,0); vl.setSpacing(10)

        lbl = QLabel("Gerenciar funcionários / compradores:")
        lbl.setStyleSheet(f"font-size:12px; color:{TXT}; background:transparent;")
        vl.addWidget(lbl)

        # Lista de gerenciamento
        self._lista_ger = QListWidget()
        self._lista_ger.setStyleSheet(self._lista.styleSheet() if hasattr(self, '_lista') else f"""
            QListWidget {{
                background:{WHITE}; border:1.5px solid {BDR};
                border-radius:8px; font-size:13px; color:{TXT};
                outline:none; padding:4px;
            }}
            QListWidget::item {{
                padding:10px 14px; border-radius:6px; margin:2px 0;
            }}
            QListWidget::item:hover {{ background:{HOV}; }}
            QListWidget::item:selected {{ background:{SEL}; color:{GRAY}; font-weight:bold; }}
        """)
        self._lista_ger.setSpacing(2)
        vl.addWidget(self._lista_ger, 1)

        # Campo de adição
        sep_add = QFrame(); sep_add.setFrameShape(QFrame.HLine)
        sep_add.setStyleSheet(f"background:#E8DEDE;"); sep_add.setFixedHeight(1)
        vl.addWidget(sep_add)

        lbl_add = QLabel("Adicionar novo funcionário:")
        lbl_add.setStyleSheet(f"font-size:11px; font-weight:600; color:{TXT}; background:transparent;")
        vl.addWidget(lbl_add)

        hl_add = QHBoxLayout(); hl_add.setSpacing(8)
        self._input_novo = QLineEdit()
        self._input_novo.setPlaceholderText("Nome do funcionário (ex: CARLOS)")
        self._input_novo.setStyleSheet(f"""
            QLineEdit {{
                color:{TXT}; background:{WHITE};
                border:1.5px solid {BDR}; border-radius:6px;
                padding:6px 10px; font-size:12px; min-height:32px;
            }}
            QLineEdit:focus {{ border:1.5px solid {RED}; }}
        """)
        self._input_novo.returnPressed.connect(self._adicionar_funcionario)
        hl_add.addWidget(self._input_novo, 1)

        btn_add = btn_solid("＋  Adicionar", GREEN, h=36)
        btn_add.clicked.connect(self._adicionar_funcionario)
        hl_add.addWidget(btn_add)
        vl.addLayout(hl_add)

        # Botão remover
        btn_rem = btn_solid("🗑  Remover selecionado", "#E74C3C", h=34)
        btn_rem.clicked.connect(self._remover_funcionario)
        vl.addWidget(btn_rem)

        return pg

    # ══════════════════════════════════════════════════════════════════════════
    # LÓGICA
    # ══════════════════════════════════════════════════════════════════════════

    def _atualizar_lista(self):
        """Recarrega ambas as listas a partir do arquivo JSON."""
        nomes = func_svc.listar()

        # Lista de seleção
        self._lista.clear()
        for nome in nomes:
            item = QListWidgetItem(f"  👤  {nome}")
            item.setData(Qt.UserRole, nome)
            item.setSizeHint(QSize(0, 44))
            self._lista.addItem(item)
        if self._lista.count() > 0:
            self._lista.setCurrentRow(0)

        # Lista de gerenciamento
        self._lista_ger.clear()
        for nome in nomes:
            item = QListWidgetItem(f"  👤  {nome}")
            item.setData(Qt.UserRole, nome)
            item.setSizeHint(QSize(0, 44))
            self._lista_ger.addItem(item)

    def _toggle_gerenciar(self):
        self._modo_gerenciar = not self._modo_gerenciar
        if self._modo_gerenciar:
            self._stack.setCurrentIndex(1)
            self._btn_gerenciar.setText("← Voltar para seleção")
            self._btn_confirmar.setEnabled(False)
            self._lbl_sub.setText("Gerenciando funcionários")
        else:
            self._stack.setCurrentIndex(0)
            self._btn_gerenciar.setText("⚙  Gerenciar funcionários")
            self._btn_confirmar.setEnabled(True)
            self._lbl_sub.setText(f"Para: {self._titulo_relatorio}")
            self._atualizar_lista()

    def _adicionar_funcionario(self):
        nome = self._input_novo.text().strip().upper()
        if not nome:
            return
        ok = func_svc.adicionar(nome)
        if ok:
            self._input_novo.clear()
            self._atualizar_lista()
            # Seleciona o recém-adicionado
            for i in range(self._lista_ger.count()):
                if self._lista_ger.item(i).data(Qt.UserRole) == nome:
                    self._lista_ger.setCurrentRow(i)
                    break
        else:
            QMessageBox.information(
                self, "Já existe",
                f"O funcionário '{nome}' já está cadastrado."
            )

    def _remover_funcionario(self):
        item = self._lista_ger.currentItem()
        if not item:
            QMessageBox.information(self, "Atenção", "Selecione um funcionário para remover.")
            return
        nome = item.data(Qt.UserRole)
        total = func_svc.listar()
        if len(total) <= 1:
            QMessageBox.warning(
                self, "Não permitido",
                "É necessário manter pelo menos um funcionário cadastrado."
            )
            return
        resp = QMessageBox.question(
            self, "Confirmar remoção",
            f"Deseja remover o funcionário:\n\n'{nome}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        # Traduz botões para contexto (padrão do SO — mas a pergunta é clara)
        if resp != QMessageBox.Yes:
            return
        func_svc.remover(nome)
        self._atualizar_lista()

    def _confirmar(self, *_):
        """Captura a seleção e fecha o diálogo."""
        if self._modo_gerenciar:
            self._toggle_gerenciar()
            return
        item = self._lista.currentItem()
        if not item:
            QMessageBox.information(self, "Atenção", "Selecione um comprador para continuar.")
            return
        self.comprador_selecionado = item.data(Qt.UserRole)
        self.accept()
