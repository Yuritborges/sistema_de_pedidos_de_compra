# app/core/services/pedido_service.py
# Responsável por validar o pedido, gerar o PDF e salvar no banco.

from app.core.dto.pedido_dto import PedidoDTO
from app.infrastructure.pdf_generator import PedidoCompraGenerator


class PedidoService:

    def __init__(self):
        self._generator = PedidoCompraGenerator()

    def gerar_pdf(self, dto):
        # Valida, gera PDF e registra no banco. Retorna o caminho do arquivo.
        self._validar(dto)
        caminho = self._generator.gerar(dto)
        self._salvar_no_banco(dto, caminho)
        return caminho

    def _validar(self, dto):
        erros = []
        if not str(dto.numero).strip():
            erros.append("Número do pedido é obrigatório.")
        if not str(dto.fornecedor_nome).strip():
            erros.append("Fornecedor é obrigatório.")
        if not str(dto.obra).strip():
            erros.append("Obra é obrigatória.")
        if not dto.itens:
            erros.append("Adicione ao menos um item ao pedido.")
        if erros:
            raise ValueError("\n".join(erros))

    def _salvar_no_banco(self, dto, caminho_pdf):
        # Se o pedido já existe (reimpressão), atualiza. Senão, insere novo.
        try:
            from app.data.database import get_connection

            with get_connection() as conn:
                existente = conn.execute(
                    "SELECT id FROM pedidos WHERE numero = ?", (dto.numero,)
                ).fetchone()

                total = getattr(dto, "total_liquido", getattr(dto, "total", 0.0))

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
                        dto.data_pedido, dto.obra, dto.escola,
                        dto.fornecedor_nome, dto.fornecedor_razao,
                        dto.empresa_faturadora, dto.condicao_pagamento,
                        dto.forma_pagamento, dto.prazo_entrega,
                        dto.comprador, total, caminho_pdf, dto.numero
                    ))
                    pedido_id = existente["id"]
                    conn.execute("DELETE FROM itens_pedido WHERE pedido_id = ?", (pedido_id,))

                else:
                    cursor = conn.execute("""
                        INSERT INTO pedidos (
                            numero, data_pedido, obra_nome, escola,
                            fornecedor_nome, fornecedor_razao, empresa_faturadora,
                            condicao_pagamento, forma_pagamento, prazo_entrega,
                            comprador, valor_total, caminho_pdf, status
                        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'emitido')
                    """, (
                        dto.numero, dto.data_pedido, dto.obra, dto.escola,
                        dto.fornecedor_nome, dto.fornecedor_razao,
                        dto.empresa_faturadora, dto.condicao_pagamento,
                        dto.forma_pagamento, dto.prazo_entrega,
                        dto.comprador, total, caminho_pdf
                    ))
                    pedido_id = cursor.lastrowid

                # Insere os itens do pedido
                for item in dto.itens:
                    val_total = getattr(
                        item, "valor_total",
                        round(float(item.quantidade) * float(item.valor_unitario), 2)
                    )
                    conn.execute("""
                        INSERT INTO itens_pedido (
                            pedido_id, descricao, quantidade,
                            unidade, valor_unitario, valor_total
                        ) VALUES (?,?,?,?,?,?)
                    """, (
                        pedido_id, item.descricao, item.quantidade,
                        item.unidade, item.valor_unitario, val_total
                    ))

        except Exception as e:
            # Não cancela o PDF por erro no banco
            print(f"[DB] Aviso ao salvar pedido: {e}")
