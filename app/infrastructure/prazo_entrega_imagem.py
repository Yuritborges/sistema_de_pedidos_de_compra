# app/infrastructure/prazo_entrega_imagem.py
# Gera um PNG do card de prazo de entrega (Qt, sem dependências extras).

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


def prazo_entrega_dias_efetivo(val) -> int:
    """Dias para data prevista: NULL no banco → 5 (padrão PedidoDTO). Zero explícito mantém 0."""
    if val is None:
        return 5
    try:
        return max(0, int(val))
    except (TypeError, ValueError):
        return 5


def _parse_datetime_data_pedido(data_pedido: str) -> datetime | None:
    """Interpreta data_pedido nos mesmos formatos que a lista Pedidos Gerados (`_parse_data`)."""
    s = (data_pedido or "").strip()
    if not s:
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    try:
        raw = s.replace("Z", "+00:00").split("+", 1)[0].strip()
        return datetime.fromisoformat(raw)
    except Exception:
        return None


def data_prevista_entrega_como_date(data_pedido: str, prazo_dias) -> date | None:
    """Data do pedido + prazo em dias (mesma base do card Prazo obra e da lista)."""
    dt = _parse_datetime_data_pedido(data_pedido)
    if dt is None:
        return None
    dias = prazo_entrega_dias_efetivo(prazo_dias)
    return dt.date() + timedelta(days=dias)


def _data_prevista_entrega(data_pedido: str, prazo_dias: int) -> str:
    d = data_prevista_entrega_como_date(data_pedido, prazo_dias)
    if d is None:
        return "—"
    return d.strftime("%d/%m/%y")


@dataclass
class ItemPrazoCard:
    descricao: str
    quantidade: float
    unidade: str


@dataclass
class DadosPrazoCard:
    numero_pedido: str
    obra: str
    fornecedor: str
    data_pedido: str
    prazo_dias: int
    itens: List[ItemPrazoCard]


def _fmt_qtd(q: float) -> str:
    if q == int(q):
        return str(int(q))
    return f"{q:.2f}".rstrip("0").rstrip(".")


def _montar_tabela_materiais(itens: List[ItemPrazoCard]) -> QTableWidget:
    tbl = QTableWidget()
    n = len(itens)
    tbl.setRowCount(n)
    tbl.setColumnCount(3)
    tbl.setHorizontalHeaderLabels(["DESCRIÇÃO DO MATERIAL", "QTDADE", "UNID."])
    tbl.verticalHeader().setVisible(False)
    tbl.setShowGrid(True)
    tbl.setEditTriggers(QTableWidget.NoEditTriggers)
    tbl.setSelectionMode(QTableWidget.NoSelection)
    tbl.setFocusPolicy(Qt.NoFocus)
    tbl.horizontalHeader().setStretchLastSection(True)
    tbl.setColumnWidth(0, 420)
    tbl.setColumnWidth(1, 90)
    tbl.setColumnWidth(2, 80)
    tbl.setStyleSheet(
        """
        QTableWidget {
            background: #FFFFFF;
            border: 1px solid #CCCCCC;
            gridline-color: #DDDDDD;
            font-size: 12px;
            color: #1A1A1A;
        }
        QTableWidget::item { padding: 8px 10px; }
        QHeaderView::section {
            background: #000000;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 10px;
            padding: 10px 8px;
            border: none;
        }
        """
    )
    for r, it in enumerate(itens):
        d = QTableWidgetItem((it.descricao or "").upper())
        q = QTableWidgetItem(_fmt_qtd(it.quantidade))
        u = QTableWidgetItem((it.unidade or "").upper())
        for c, item in enumerate((d, q, u)):
            item.setFlags(Qt.ItemIsEnabled)
            tbl.setItem(r, c, item)
    tbl.resizeRowsToContents()
    tbl.setMaximumHeight(
        min(520, tbl.horizontalHeader().height() + sum(tbl.rowHeight(i) for i in range(n)) + 8)
    )
    return tbl


def construir_widget_card(dados: DadosPrazoCard) -> QWidget:
    """Monta o widget (não mostrado); use grab() no pai para exportar PNG."""
    dias = max(0, int(dados.prazo_dias))
    data_prev = _data_prevista_entrega(dados.data_pedido, dias)
    sufixo = "dia" if dias == 1 else "dias"

    root = QWidget()
    root.setFixedWidth(780)
    root.setStyleSheet("background:#FFFFFF;")

    vl = QVBoxLayout(root)
    vl.setContentsMargins(20, 18, 20, 18)
    vl.setSpacing(14)

    linha_ctx = f"Pedido nº <b>{dados.numero_pedido}</b>"
    if dados.obra:
        linha_ctx += f" &nbsp;·&nbsp; Obra: <b>{dados.obra}</b>"
    if dados.fornecedor:
        linha_ctx += f" &nbsp;·&nbsp; {dados.fornecedor}"

    lbl_ctx = QLabel(linha_ctx)
    lbl_ctx.setTextFormat(Qt.RichText)
    lbl_ctx.setStyleSheet("font-size:11px; color:#555; background:transparent;")
    lbl_ctx.setWordWrap(True)
    vl.addWidget(lbl_ctx)

    row_prazo = QHBoxLayout()
    row_prazo.setSpacing(12)

    lb_pe = QLabel("PRAZO ENTREGA")
    lb_pe.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
    lb_pe.setStyleSheet("color:#1A1A1A; background:transparent;")

    lb_nd = QLabel(f"{dias} {sufixo}")
    lb_nd.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
    lb_nd.setStyleSheet("color:#1A1A1A; background:transparent;")

    row_prazo.addWidget(lb_pe)
    row_prazo.addWidget(lb_nd)
    row_prazo.addStretch(1)

    lb_dp = QLabel("DATA PREVISTA DA ENTREGA")
    lb_dp.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
    lb_dp.setStyleSheet("color:#1A1A1A; background:transparent;")

    box_data = QFrame()
    box_data.setStyleSheet(
        "QFrame { background:#EEEEEE; border:1px solid #333; border-radius:2px; padding:4px 12px; }"
    )
    hl_b = QHBoxLayout(box_data)
    hl_b.setContentsMargins(10, 6, 10, 6)
    lb_dt = QLabel(data_prev)
    lb_dt.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
    lb_dt.setStyleSheet("color:#1A1A1A; background:transparent;")
    hl_b.addWidget(lb_dt)

    row_prazo.addWidget(lb_dp)
    row_prazo.addWidget(box_data)
    vl.addLayout(row_prazo)

    vl.addWidget(_montar_tabela_materiais(dados.itens))

    root.adjustSize()
    return root


def widget_para_pixmap(widget: QWidget) -> QPixmap:
    widget.adjustSize()
    return widget.grab()


def gerar_imagem_prazo_entrega(parent: QWidget, pedido_id: int) -> None:
    """Carrega o pedido no banco, monta o card, salva PNG no temp e copia para o clipboard."""
    import os
    import tempfile

    from PySide6.QtWidgets import QApplication, QMessageBox

    from app.data.database import get_connection

    try:
        with get_connection() as conn:
            p = conn.execute(
                """
                SELECT numero, data_pedido, obra_nome, escola, fornecedor_nome, prazo_entrega
                FROM pedidos WHERE id = ?
                """,
                (pedido_id,),
            ).fetchone()
            if not p:
                QMessageBox.warning(parent, "Pedido", "Pedido não encontrado.")
                return
            itens_rows = conn.execute(
                """
                SELECT descricao, quantidade, unidade
                FROM itens_pedido WHERE pedido_id = ? ORDER BY id
                """,
                (pedido_id,),
            ).fetchall()

        if not itens_rows:
            QMessageBox.information(
                parent,
                "Itens",
                "Este pedido não possui itens no banco. Gere o pedido novamente se necessário.",
            )
            return

        itens = [
            ItemPrazoCard(
                descricao=str(r["descricao"] or ""),
                quantidade=float(r["quantidade"] or 0),
                unidade=str(r["unidade"] or ""),
            )
            for r in itens_rows
        ]

        dados = DadosPrazoCard(
            numero_pedido=str(p["numero"] or ""),
            obra=str((p["escola"] or "").strip() or p["obra_nome"] or ""),
            fornecedor=str(p["fornecedor_nome"] or ""),
            data_pedido=str(p["data_pedido"] or ""),
            prazo_dias=prazo_entrega_dias_efetivo(p["prazo_entrega"]),
            itens=itens,
        )

        w = construir_widget_card(dados)
        pix = widget_para_pixmap(w)

        nome_arq = f"brasul_prazo_pedido_{dados.numero_pedido}.png".replace("/", "-")
        path = os.path.join(tempfile.gettempdir(), nome_arq)
        if not pix.save(path, "PNG"):
            QMessageBox.warning(parent, "Imagem", "Não foi possível salvar a imagem.")
            return

        QApplication.clipboard().setPixmap(pix)

        QMessageBox.information(
            parent,
            "Prazo de entrega",
            "Imagem copiada para a área de transferência (Ctrl+V no WhatsApp).\n\n"
            f"Também salva em:\n{path}",
        )
    except Exception as e:
        QMessageBox.warning(parent, "Erro", f"Não foi possível gerar a imagem.\n\n{e}")
