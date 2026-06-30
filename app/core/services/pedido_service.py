# app/core/services/pedido_service.py
# Responsável por validar, gerar o PDF e salvar no banco.

import os

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
        except ValueError:
            try:
                os.remove(caminho)
            except OSError:
                pass
            raise
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
        self._validar_numero_disponivel(dto)

    def _validar_numero_disponivel(self, dto):
        """
        Em edição: se o utilizador mudar o Nº para um já usado por outro pedido, bloqueia.
        Em pedido novo: bloqueia se o Nº já existir.
        Corre antes de gerar o PDF para feedback imediato.
        """
        from app.data.database import get_connection

        numero = str(getattr(dto, "numero", "") or "").strip()
        if not numero:
            return
        editar_id = getattr(dto, "pedido_existente_id", None)
        with get_connection() as conn:
            if editar_id is not None:
                try:
                    eid = int(editar_id)
                except (TypeError, ValueError):
                    return
                row = conn.execute(
                    "SELECT numero FROM pedidos WHERE id = ?",
                    (eid,),
                ).fetchone()
                if not row:
                    return
                num_atual = str(row["numero"] or "").strip()
                if numero == num_atual:
                    return
                outro = conn.execute(
                    "SELECT id FROM pedidos WHERE numero = ? AND id != ?",
                    (numero, eid),
                ).fetchone()
                if outro:
                    raise ValueError(
                        f"O Nº {numero} já está em uso por outro pedido.\n"
                        "Informe um número de pedido ainda não utilizado no banco."
                    )
            else:
                ocupado = conn.execute(
                    "SELECT id FROM pedidos WHERE numero = ?",
                    (numero,),
                ).fetchone()
                if ocupado:
                    raise ValueError(
                        f"O Nº {numero} já está registrado no banco.\n"
                        "Informe um número de pedido ainda não utilizado "
                        "(pode usar o próximo sugerido na caixa «Nº»)."
                    )

    def _calcular_total_seguro(self, dto):
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

    def _desconto_do_dto(self, dto) -> tuple[float, str, float]:
        try:
            desconto = round(float(getattr(dto, "desconto", 0) or 0), 2)
        except Exception:
            desconto = 0.0
        tipo = str(getattr(dto, "desconto_tipo", "%") or "%").strip() or "%"
        try:
            valor_digitado = float(getattr(dto, "desconto_valor_digitado", 0) or 0)
        except Exception:
            valor_digitado = 0.0
        return desconto, tipo, valor_digitado

    def _salvar_no_banco(self, dto, caminho_pdf):
        from app.data.database import get_connection
        from config import COMPRADOR_PADRAO

        numero = str(getattr(dto, "numero", "")).strip()
        comprador = str(getattr(dto, "comprador", "") or COMPRADOR_PADRAO).strip().upper()
        total = self._calcular_total_seguro(dto)
        desconto, desconto_tipo, desconto_valor = self._desconto_do_dto(dto)
        editar_id = getattr(dto, "pedido_existente_id", None)

        with get_connection() as conn:
            existente = None
            if editar_id is not None:
                existente = conn.execute(
                    "SELECT id FROM pedidos WHERE id = ?",
                    (int(editar_id),),
                ).fetchone()

            if editar_id is not None and not existente:
                raise ValueError(
                    "Pedido em edição não foi encontrado no banco (pode ter sido removido). "
                    "Feche e abra de novo em «Pedidos gerados»."
                )

            if existente:
                pedido_id = existente["id"]

                row_atual = conn.execute(
                    "SELECT numero FROM pedidos WHERE id = ?",
                    (pedido_id,),
                ).fetchone()
                num_antigo = str(row_atual["numero"] or "").strip() if row_atual else ""
                if numero != num_antigo:
                    outro = conn.execute(
                        "SELECT id FROM pedidos WHERE numero = ? AND id != ?",
                        (numero, pedido_id),
                    ).fetchone()
                    if outro:
                        raise ValueError(
                            f"O Nº {numero} já está em uso por outro pedido.\n"
                            "Informe um número de pedido ainda não utilizado no banco."
                        )

                conn.execute("""
                    UPDATE pedidos SET
                        numero             = ?,
                        data_pedido        = ?,
                        obra_nome          = ?,
                        escola             = ?,
                        fornecedor_nome    = ?,
                        fornecedor_razao   = ?,
                        empresa_faturadora = ?,
                        condicao_pagamento = ?,
                        forma_pagamento    = ?,
                        pagamento_etapas_ativo = ?,
                        percentual_entrada = ?,
                        percentual_final   = ?,
                        marco_percentual_final = ?,
                        prazo_entrega      = ?,
                        comprador          = ?,
                        material_solicitado_por = ?,
                        valor_total        = ?,
                        desconto           = ?,
                        desconto_tipo      = ?,
                        desconto_valor_digitado = ?,
                        caminho_pdf        = ?,
                        emitido_em         = datetime('now'),
                        status             = 'emitido'
                    WHERE id = ?
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
                    1 if getattr(dto, "pagamento_etapas_ativo", False) else 0,
                    int(getattr(dto, "percentual_entrada", 0) or 0),
                    int(getattr(dto, "percentual_final", 0) or 0),
                    getattr(dto, "marco_percentual_final", "") or "",
                    int(getattr(dto, "prazo_entrega", 0) or 0),
                    comprador,
                    (getattr(dto, "material_solicitado_por", "") or "").strip(),
                    total,
                    desconto,
                    desconto_tipo,
                    desconto_valor,
                    caminho_pdf,
                    pedido_id,
                ))

                conn.execute("DELETE FROM itens_pedido WHERE pedido_id = ?", (pedido_id,))

            else:
                ocupado = conn.execute(
                    "SELECT id FROM pedidos WHERE numero = ?",
                    (numero,),
                ).fetchone()
                if ocupado:
                    raise ValueError(
                        f"O Nº {numero} já está registrado no banco.\n"
                        "Informe um número de pedido ainda não utilizado "
                        "(pode usar o próximo sugerido na caixa «Nº»)."
                    )
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
                        pagamento_etapas_ativo,
                        percentual_entrada,
                        percentual_final,
                        marco_percentual_final,
                        prazo_entrega,
                        comprador,
                        material_solicitado_por,
                        valor_total,
                        desconto,
                        desconto_tipo,
                        desconto_valor_digitado,
                        caminho_pdf,
                        status
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'emitido')
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
                    1 if getattr(dto, "pagamento_etapas_ativo", False) else 0,
                    int(getattr(dto, "percentual_entrada", 0) or 0),
                    int(getattr(dto, "percentual_final", 0) or 0),
                    getattr(dto, "marco_percentual_final", "") or "",
                    getattr(dto, "prazo_entrega", 0),
                    comprador,
                    (getattr(dto, "material_solicitado_por", "") or "").strip(),
                    total,
                    desconto,
                    desconto_tipo,
                    desconto_valor,
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
        try:
            from app.data.cotacao_rede_sync import sync_pedido_atual_para_cotacao_rede

            sync_pedido_atual_para_cotacao_rede(numero)
        except Exception as e:
            print(f"[REDE] Aviso ao atualizar cotacao_rede.db: {e}")