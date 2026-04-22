# app/core/dto/pedido_dto.py
# Estruturas de dados que trafegam entre a interface e os serviços.
# Sem lógica de negócio, sem banco. Só organiza os dados.

from dataclasses import dataclass, field
from typing import List


@dataclass
class ItemPedidoDTO:
    descricao:      str
    quantidade:     float
    unidade:        str
    valor_unitario: float

    @property
    def valor_total(self):
        return round(self.quantidade * self.valor_unitario, 2)

    def __post_init__(self):
        self.descricao      = self.descricao.upper().strip()
        self.unidade        = self.unidade.upper().strip()
        self.quantidade     = float(self.quantidade)
        self.valor_unitario = float(self.valor_unitario)


@dataclass
class PedidoDTO:
    # Identificação
    numero:             str
    data_pedido:        str
    empresa_faturadora: str
    comprador:          str

    # Obra
    obra:             str
    escola:           str
    endereco_entrega: str
    bairro_entrega:   str
    cep_entrega:      str
    cidade_entrega:   str
    uf_entrega:       str
    contrato_obra:    str = "0"

    # Fornecedor
    fornecedor_nome:     str = ""
    fornecedor_razao:    str = ""
    fornecedor_email:    str = ""
    fornecedor_vendedor: str = ""
    fornecedor_telefone: str = ""

    # Condições comerciais
    prazo_entrega:      int   = 5
    condicao_pagamento: str   = "14"
    forma_pagamento:    str   = "BOLETO"
    observacao_extra:   str   = ""
    desconto:           float = 0.0

    # Itens do pedido
    itens: List[ItemPedidoDTO] = field(default_factory=list)

    @property
    def subtotal(self):
        return round(sum(i.valor_total for i in self.itens), 2)

    @property
    def total(self):
        return round(self.subtotal - self.desconto, 2)

    @property
    def data_prevista_entrega(self):
        from datetime import datetime, timedelta
        try:
            dt = datetime.strptime(self.data_pedido, "%d/%m/%Y")
            return (dt + timedelta(days=self.prazo_entrega)).strftime("%d/%m/%y")
        except Exception:
            return ""

    @property
    def estimativa_vencimento(self):
        from datetime import datetime, timedelta
        try:
            primeiro = int(self.condicao_pagamento.split("/")[0])
            dt = datetime.strptime(self.data_pedido, "%d/%m/%Y")
            return (dt + timedelta(days=primeiro)).strftime("%d/%m/%y")
        except Exception:
            return ""
