# app/ui/widgets/pedidos_gerados_widget.py
# Aba simples que lista todos os pedidos gerados e permite abrir o PDF.

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox,
)
from PySide6.QtCore import Qt
import os

from app.ui.style import btn_solid


class PedidosGeradosWidget(QWidget):

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        titulo = QLabel("Pedidos Gerados")
        titulo.setAlignment(Qt.AlignLeft)
        titulo.setStyleSheet("font-size:18px;font-weight:bold;color:#2c3e50;")
        layout.addWidget(titulo)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels([
            "Número", "Data", "Obra", "Fornecedor", "Valor Total", "Ação"
        ])
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)

        hh = self.tabela.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        layout.addWidget(self.tabela)
        self.carregar_dados()

    def carregar_dados(self):
        try:
            from app.data.database import get_connection

            with get_connection() as conn:
                rows = conn.execute("""
                    SELECT id, numero, data_pedido, obra_nome,
                           fornecedor_nome, valor_total, caminho_pdf
                    FROM pedidos
                    ORDER BY id DESC
                """).fetchall()

            self.tabela.setRowCount(len(rows))

            for i, row in enumerate(rows):
                pedido_id   = int(row["id"])
                numero      = str(row["numero"] or "")
                data        = str(row["data_pedido"] or "")
                obra        = str(row["obra_nome"] or "")
                fornecedor  = str(row["fornecedor_nome"] or "")
                valor       = float(row["valor_total"] or 0)
                caminho_pdf = str(row["caminho_pdf"] or "")

                valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

                self.tabela.setItem(i, 0, QTableWidgetItem(numero))
                self.tabela.setItem(i, 1, QTableWidgetItem(data))
                self.tabela.setItem(i, 2, QTableWidgetItem(obra))
                self.tabela.setItem(i, 3, QTableWidgetItem(fornecedor))
                self.tabela.setItem(i, 4, QTableWidgetItem(valor_fmt))

                acoes = QWidget()
                hl = QHBoxLayout(acoes)
                hl.setContentsMargins(4, 2, 4, 2)
                hl.setSpacing(6)

                btn_pdf = QPushButton("Abrir PDF")
                btn_pdf.setFixedHeight(30)
                btn_pdf.clicked.connect(lambda _, p=caminho_pdf: self.abrir_pdf(p))

                btn_prazo = btn_solid("Prazo obra", "#25D366", h=30)
                btn_prazo.setToolTip(
                    "Gera imagem com prazo e itens para colar no WhatsApp da obra."
                )
                btn_prazo.clicked.connect(lambda _, pid=pedido_id: self._gerar_imagem_prazo(pid))

                hl.addWidget(btn_pdf)
                hl.addWidget(btn_prazo)
                self.tabela.setCellWidget(i, 5, acoes)

        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível carregar os pedidos.\n\n{e}")

    def _gerar_imagem_prazo(self, pedido_id: int):
        from app.infrastructure.prazo_entrega_imagem import gerar_imagem_prazo_entrega

        gerar_imagem_prazo_entrega(self, pedido_id)

    def abrir_pdf(self, caminho_pdf):
        if not caminho_pdf:
            QMessageBox.information(self, "PDF", "Este pedido não possui PDF registrado.")
            return
        if not os.path.exists(caminho_pdf):
            QMessageBox.warning(self, "PDF não encontrado", f"Arquivo não encontrado:\n{caminho_pdf}")
            return
        try:
            os.startfile(caminho_pdf)
        except Exception as e:
            QMessageBox.warning(self, "Erro ao abrir PDF", str(e))
