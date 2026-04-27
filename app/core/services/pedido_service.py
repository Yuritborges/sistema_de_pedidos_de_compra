# app/core/services/pedido_service.py
# Responsável por validar o pedido, gerar o PDF e salvar no banco.

from app.core.dto.pedido_dto import PedidoDTO
from app.infrastructure.pdf_generator import PedidoCompraGenerator


class PedidoService:

    def __init__(self):
        self._generator = PedidoCompraGenerator()

    def gerar_pdf(self, dto):
        """
        Valida, gera PDF e registra no banco.
        Retorna o caminho do arquivo gerado.
        """
        self._validar(dto)
        caminho = self._generator.gerar(dto)
        self._salvar_no_banco(dto, caminho)
        return caminho

    def _validar(self, dto):
        erros = []

        if not str(getattr(dto, "numero", "")).strip():
            erros.append("Número do pedido é obrigatório.")

        if not str(getattr(dto, "fornecedor_nome", "")).strip():
            erros.append("Fornecedor é obrigatório.")

        if not str(getattr(dto, "obra", "")).strip():
            erros.append("Obra é obrigatória.")

        if not getattr(dto, "itens", None):
            erros.append("Adicione ao menos um item ao pedido.")

        if erros:
            raise ValueError("\n".join(erros))

    def _calcular_total_seguro(self, dto):
        """
        Calcula o total do pedido de forma blindada.
        Evita salvar R$ 0,00 no banco quando o DTO vier incompleto.
        """
        try:
            total_liquido = getattr(dto, "total_liquido", None)
            if total_liquido not in (None, ""):
                return round(float(total_liquido), 2)
        except Exception:
            pass

        try:
            total = getattr(dto, "total", None)
            if total not in (None, ""):
                return round(float(total), 2)
        except Exception:
            pass

        total_itens = 0.0
        for item in getattr(dto, "itens", []) or []:
            try:
                quantidade = float(getattr(item, "quantidade", 0) or 0)
                valor_unitario = float(getattr(item, "valor_unitario", 0) or 0)
                total_itens += quantidade * valor_unitario
            except Exception:
                continue

        try:
            desconto = float(getattr(dto, "desconto", 0) or 0)
        except Exception:
            desconto = 0.0

        return round(total_itens - desconto, 2)

    def _salvar_no_banco(self, dto, caminho_pdf):
        """
        Se o pedido já existe, atualiza.
        Se não existe, insere novo.
        Depois recria os itens vinculados ao pedido.
        """
        try:
            from app.data.database import get_connection

            with get_connection() as conn:
                existente = conn.execute(
                    "SELECT id FROM pedidos WHERE numero = ?",
                    (dto.numero,)
                ).fetchone()

                total = self._calcular_total_seguro(dto)

                print(
                    f"[PEDIDO] Salvando pedido {dto.numero} | "
                    f"Fornecedor: {dto.fornecedor_nome} | "
                    f"Obra: {dto.obra} | "
                    f"Total: {total}"
                )

                if existente:
                    conn.execute("""
                        UPDATE pedidos SET
                            data_pedido        = ?,
                            obra_nome          = ?,
                            escola             = ?,
                            fornecedor_nome    = ?,
                            fornecedor_razao   = ?,
                            empresa_faturadora = ?,
                            condicao_pagamento = ?,
                            forma_pagamento    = ?,
                            prazo_entrega      = ?,
                            comprador          = ?,
                            valor_total        = ?,
                            caminho_pdf        = ?,
                            status             = 'emitido'
                        WHERE numero = ?
                    """, (
                        dto.data_pedido,
                        dto.obra,
                        dto.escola,
                        dto.fornecedor_nome,
                        dto.fornecedor_razao,
                        dto.empresa_faturadora,
                        dto.condicao_pagamento,
                        dto.forma_pagamento,
                        dto.prazo_entrega,
                        dto.comprador,
                        total,
                        caminho_pdf,
                        dto.numero,
                    ))

                    pedido_id = existente["id"]
                    conn.execute(
                        "DELETE FROM itens_pedido WHERE pedido_id = ?",
                        (pedido_id,)
                    )

                else:
                    cursor = conn.execute("""
                        INSERT INTO pedidos (
                            numero,
                            data_pedido,
                            obra_nome,
                            escola,
                            fornecedor_nome,
                            fornecedor_razao,
                            empresa_faturadora,
                            condicao_pagamento,
                            forma_pagamento,
                            prazo_entrega,
                            comprador,
                            valor_total,
                            caminho_pdf,
                            status
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'emitido')
                    """, (
                        dto.numero,
                        dto.data_pedido,
                        dto.obra,
                        dto.escola,
                        dto.fornecedor_nome,
                        dto.fornecedor_razao,
                        dto.empresa_faturadora,
                        dto.condicao_pagamento,
                        dto.forma_pagamento,
                        dto.prazo_entrega,
                        dto.comprador,
                        total,
                        caminho_pdf,
                    ))

                    pedido_id = cursor.lastrowid

                for item in dto.itens:
                    try:
                        quantidade = float(getattr(item, "quantidade", 0) or 0)
                        valor_unitario = float(getattr(item, "valor_unitario", 0) or 0)
                        valor_total = round(quantidade * valor_unitario, 2)
                    except Exception:
                        quantidade = 0.0
                        valor_unitario = 0.0
                        valor_total = 0.0

                    conn.execute("""
                        INSERT INTO itens_pedido (
                            pedido_id,
                            descricao,
                            quantidade,
                            unidade,
                            valor_unitario,
                            valor_total
                        ) VALUES (?,?,?,?,?,?)
                    """, (
                        pedido_id,
                        getattr(item, "descricao", ""),
                        quantidade,
                        getattr(item, "unidade", ""),
                        valor_unitario,
                        valor_total,
                    ))

        except Exception as e:
            raise RuntimeError(f"Erro ao salvar pedido no banco: {e}")

        try:
            from app.data.database import sincronizar_com_rede
            sincronizar_com_rede(silencioso=True)
        except Exception as e:
            print(f"[REDE] Aviso ao sincronizar pedido: {e}")