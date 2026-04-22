# main.py
# Ponto de entrada do sistema.
# Rode com: python main.py

import sys
import os

# Adiciona a pasta raiz ao path para os imports funcionarem
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.data.database import init_db
from app.ui.main_window import MainWindow

# CSS global: garante texto legível independente do tema do Windows
GLOBAL_CSS = """
    QWidget                { color: #111827; }
    QLineEdit              { color: #111827; background: #FFFFFF;
                             selection-background-color: #BFDBFE;
                             selection-color: #1E3A5F; }
    QLineEdit:read-only    { color: #6B7280; background: #F3F4F6; }
    QComboBox              { color: #111827; background: #FFFFFF; }
    QSpinBox               { color: #111827; background: #FFFFFF; }
    QDoubleSpinBox         { color: #111827; background: #FFFFFF; }
    QTextEdit              { color: #111827; background: #FFFFFF; }
    QLabel                 { color: #111827; background: transparent; }
    QGroupBox              { color: #111827; }
    QTableWidget           { color: #111827; }
    QTableWidget::item     { color: #111827; }
    QHeaderView::section   { color: #FFFFFF; }
    QMessageBox QLabel     { color: #111827; }
    QComboBox QAbstractItemView {
        color: #111827; background: #FFFFFF;
        selection-background-color: #DBEAFE;
        selection-color: #1E3A5F;
    }
"""


def main():
    init_db()

    try:
        from PySide6.QtWidgets import QApplication

        app = QApplication(sys.argv)
        app.setApplicationName("Sistema de Cotação - Brasul")
        app.setOrganizationName("Brasul Construtora")
        app.setStyle("Fusion")
        app.setStyleSheet(GLOBAL_CSS)

        window = MainWindow()
        window.show()

        sys.exit(app.exec())

    except ImportError:
        print("PySide6 não instalado. Rodando demo CLI...")
        _demo_cli()


def _demo_cli():
    # Modo de teste sem interface gráfica
    from app.core.services.pedido_service import PedidoService
    from app.core.dto.pedido_dto import PedidoDTO, ItemPedidoDTO

    dto = PedidoDTO(
        numero="2549", data_pedido="09/04/2026",
        empresa_faturadora="BRASUL", comprador="IURY",
        obra="MARIA RITA ARAÚJO", escola="E.E Maria Rita Araújo",
        endereco_entrega="R. Ernesto Bergamasco, 665",
        bairro_entrega="Vila São Pedro", cep_entrega="13183-080",
        cidade_entrega="Hortolândia", uf_entrega="SP",
        fornecedor_nome="AZEFER MATERIAIS",
        fornecedor_razao="AZEFER MATERIAIS PARA CONSTRUÇÃO EIRELI",
        fornecedor_email="vendas@azevedoconstrucao.com.br",
        fornecedor_vendedor="Cleber", fornecedor_telefone="19 98745-3060",
        prazo_entrega=5, condicao_pagamento="14", forma_pagamento="BOLETO",
        itens=[
            ItemPedidoDTO("AREIA GROSSA MD MT", 2.0, "M3", 153.09),
            ItemPedidoDTO("CIMENTO 50KG VOTORAN CPII", 10.0, "SACO", 39.90),
            ItemPedidoDTO("TABUA PINUS BRUTA 20CM X 3.00MT", 10.0, "UNID.", 15.50),
            ItemPedidoDTO("PREGO GERDAU 17X21 COM CABECA", 1.0, "KG", 15.50),
            ItemPedidoDTO("TABUA PINUS BRUTA 05CM X 3.00MT", 10.0, "UNID.", 4.24),
            ItemPedidoDTO("MEIO METRO PEDRA I MT", 0.5, "M3", 130.80),
        ]
    )
    service = PedidoService()
    print("PDF gerado em:", service.gerar_pdf(dto))


if __name__ == "__main__":
    main()
