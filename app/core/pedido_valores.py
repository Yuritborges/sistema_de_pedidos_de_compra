# Valor líquido do pedido (itens − desconto) para relatórios e listagens.


def valor_liquido_pedido(
    valor_total,
    soma_itens=None,
    desconto=0,
) -> float:
    """
    Retorna o total líquido para relação de pedidos / cards.

    - valor_total no banco deve ser líquido; quando ficou igual à soma dos itens
      mas há desconto salvo, aplica o desconto.
    - Quando valor_total já é menor que a soma dos itens, assume líquido correto.
    """
    vt = float(valor_total or 0)
    soma = float(soma_itens if soma_itens is not None else vt)
    desc = float(desconto or 0)

    if desc > 0.009:
        if abs(vt - soma) < 0.02:
            return round(soma - desc, 2)
        if vt <= soma - desc + 0.02:
            return round(vt, 2)

    return round(vt, 2)
