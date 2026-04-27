# app/core/services/pedido_service.py
# Responsável por validar o pedido, gerar o PDF e salvar no banco.

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

        try:
            self._salvar_no_banco(dto, caminho)
        except Exception as e:
            raise RuntimeError(
                f"O PDF foi gerado, mas o pedido NÃO foi salvo no banco.\n\n"
                f"Pedido: {getattr(dto, 'numero', '')}\n"
                f"PDF: {caminho}\n\n"
                f"Erro real:\n{e}"
            )

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
        from app.data.database import get_connection
        from config import COMPRADOR_PADRAO

        numero = str(getattr(dto, "numero", "")).strip()
        comprador = str(getattr(dto, "comprador", "") or COMPRADOR_PADRAO).strip().upper()
        total = self._calcular_total_seguro(dto)

        with get_connection() as conn:
            existente = conn.execute(
                "SELECT id FROM pedidos WHERE numero = ?",
                (numero,)
            ).fetchone()

            if existente:
                pedido_id = existente["id"]

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
                    WHERE id = ?
                """, (
                    getattr(dto, "data_pedido", ""),
                    getattr(dto, "obra", ""),
                    getattr(dto, "escola", ""),
                    getattr(dto, "fornecedor_nome", ""),
                    getattr(dto, "fornecedor_razao", ""),
                    getattr(dto, "empresa_faturadora", ""),
                    getattr(dto, "condicao_pagamento", ""),
                    getattr(dto, "forma_pagamento", ""),
                    getattr(dto, "prazo_entrega", 0),
                    comprador,
                    total,
                    caminho_pdf,
                    pedido_id,
                ))

                conn.execute("DELETE FROM itens_pedido WHERE pedido_id = ?", (pedido_id,))

            else:
                cur = conn.execute("""
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
                    numero,
                    getattr(dto, "data_pedido", ""),
                    getattr(dto, "obra", ""),
                    getattr(dto, "escola", ""),
                    getattr(dto, "fornecedor_nome", ""),
                    getattr(dto, "fornecedor_razao", ""),
                    getattr(dto, "empresa_faturadora", ""),
                    getattr(dto, "condicao_pagamento", ""),
                    getattr(dto, "forma_pagamento", ""),
                    getattr(dto, "prazo_entrega", 0),
                    comprador,
                    total,
                    caminho_pdf,
                ))

                pedido_id = cur.lastrowid

            for item in getattr(dto, "itens", []) or []:
                quantidade = float(getattr(item, "quantidade", 0) or 0)
                valor_unitario = float(getattr(item, "valor_unitario", 0) or 0)
                valor_total = round(quantidade * valor_unitario, 2)

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

            conn.commit()

            conferido = conn.execute(
                "SELECT id FROM pedidos WHERE numero = ? AND UPPER(TRIM(comprador)) = UPPER(TRIM(?))",
                (numero, comprador)
            ).fetchone()

            if not conferido:
                raise RuntimeError(
                    f"Falha crítica: pedido {numero} não apareceu no banco após salvar."
                )

        try:
            from app.data.database import sincronizar_com_rede
            sincronizar_com_rede(silencioso=True)
        except Exception as e:
            print(f"[REDE] Aviso ao sincronizar pedido: {e}")