# app/infrastructure/relacao_pedidos_pdf.py
# Gera o PDF da Relação de Pedidos para o financeiro.
import os
from datetime import date, datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Paleta ────────────────────────────────────────────────────────────────────
C_VERMELHO  = colors.HexColor("#C0392B")
C_ESCURO    = colors.HexColor("#1A1A1A")
C_MEDIO     = colors.HexColor("#555555")
C_CLARO     = colors.HexColor("#888888")
C_FUNDO_HDR = colors.HexColor("#1A1A1A")
C_LINHA     = colors.HexColor("#E8DEDE")
C_BRANCO    = colors.white
C_ALT       = colors.HexColor("#FBF7F7")

CORES_EMP = {
    "BRASUL":      colors.HexColor("#C0392B"),
    "JB":          colors.HexColor("#A93226"),
    "B&B":         colors.HexColor("#1E8449"),
    "INTERIORANA": colors.HexColor("#784212"),
    "INTERBRAS":   colors.HexColor("#1A5276"),
}

_LOGOS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'logos')
)


def _logo_path():
    p = os.path.join(_LOGOS_DIR, "logo_brasul.png")
    return p if os.path.exists(p) else None


def _fmt_val(v):
    try:
        return f"R$ {float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _fmt_val_num(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def gerar_relacao_pdf(caminho: str, pedidos: list, data_ref: date,
                      comprador: str = "",
                      agrupar_por_empresa: bool = True) -> str:
    """
    Gera o PDF da Relação de Pedidos.

    Args:
        caminho:             Caminho completo do arquivo .pdf a ser gerado.
        pedidos:             Lista de dicts com chaves:
                             numero, fornecedor, obra, condicao_pagamento,
                             forma_pagamento, valor_total, empresa_faturadora
        data_ref:            Data de referência do relatório.
        comprador:           Nome do comprador responsável (exibido no cabeçalho).
        agrupar_por_empresa: Se True, agrupa os pedidos por empresa faturadora.

    Returns:
        Caminho do arquivo gerado.
    """
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    doc = SimpleDocTemplate(
        caminho,
        pagesize=landscape(A4),
        leftMargin=14 * mm, rightMargin=14 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Relação de Pedidos — {data_ref.strftime('%d/%m/%Y')}",
    )

    story = []
    story += _cabecalho(data_ref, len(pedidos), comprador)
    story.append(Spacer(1, 4 * mm))

    if not pedidos:
        story.append(Paragraph(
            "Nenhum pedido encontrado para esta data.",
            ParagraphStyle("vazio", fontSize=11, textColor=C_CLARO,
                           alignment=TA_CENTER)
        ))
        doc.build(story)
        return caminho

    if agrupar_por_empresa:
        story += _tabela_agrupada(pedidos)
    else:
        story += _tabela_simples(pedidos)

    # Rodapé de emissão
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=C_LINHA, spaceAfter=3 * mm))
    comp_str = f" | Comprador: {comprador}" if comprador else ""
    story.append(Paragraph(
        f"Emitido em {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
        f"{comp_str} — Sistema de Pedidos Brasul Construtora",
        ParagraphStyle("rodape", fontSize=7, textColor=C_CLARO,
                       alignment=TA_CENTER)
    ))

    doc.build(story, onFirstPage=_numerar_pagina, onLaterPages=_numerar_pagina)
    return caminho


# ── Cabeçalho ─────────────────────────────────────────────────────────────────

def _cabecalho(data_ref: date, total: int, comprador: str = "") -> list:
    elems = []
    W_PAGE = landscape(A4)[0] - 28 * mm

    titulo_style = ParagraphStyle(
        "titulo", fontSize=16, textColor=C_ESCURO,
        fontName="Helvetica-Bold", leading=20
    )
    sub_style = ParagraphStyle(
        "sub", fontSize=9, textColor=C_CLARO,
        fontName="Helvetica", leading=12
    )
    info_style = ParagraphStyle(
        "info", fontSize=10, textColor=C_ESCURO,
        fontName="Helvetica-Bold", alignment=TA_RIGHT, leading=14
    )
    info_sub_style = ParagraphStyle(
        "info_sub", fontSize=8, textColor=C_CLARO,
        fontName="Helvetica", alignment=TA_RIGHT, leading=11
    )
    comp_style = ParagraphStyle(
        "comp", fontSize=9, textColor=C_VERMELHO,
        fontName="Helvetica-Bold", alignment=TA_RIGHT, leading=12
    )

    data_str   = data_ref.strftime("%d/%m/%Y")
    dia_semana = ["Segunda", "Terça", "Quarta", "Quinta",
                  "Sexta", "Sábado", "Domingo"][data_ref.weekday()]

    titulo_p = Paragraph("RELAÇÃO DE PEDIDOS EMITIDOS", titulo_style)
    sub_p    = Paragraph(
        "Brasul Construtora &amp; Empresas — Para o Financeiro", sub_style)

    data_p  = Paragraph(f"{dia_semana}, {data_str}", info_style)
    total_p = Paragraph(
        f"{total} pedido{'s' if total != 1 else ''} emitido{'s' if total != 1 else ''}",
        info_sub_style
    )

    # Coluna direita: data + total + comprador (se houver)
    col_dir = [data_p, total_p]
    if comprador:
        col_dir.append(Paragraph(f"Comprador: {comprador}", comp_style))

    logo    = _logo_path()
    col_logo = 35 * mm

    if logo:
        from reportlab.platypus import Image as RLImage
        logo_img = RLImage(logo, width=30 * mm, height=20 * mm, kind="proportional")
        hdr_data = [[logo_img, [titulo_p, sub_p], col_dir]]
        col_w = [col_logo, W_PAGE - col_logo - 52 * mm, 52 * mm]
    else:
        hdr_data = [[[titulo_p, sub_p], col_dir]]
        col_w = [W_PAGE - 52 * mm, 52 * mm]

    hdr_tbl = Table(hdr_data, colWidths=col_w)
    hdr_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
    ]))
    elems.append(hdr_tbl)
    elems.append(Spacer(1, 3 * mm))
    elems.append(HRFlowable(width="100%", thickness=2,
                             color=C_VERMELHO, spaceAfter=2 * mm))
    return elems


# ── Tabela agrupada por empresa ────────────────────────────────────────────────

def _tabela_agrupada(pedidos: list) -> list:
    elems = []
    grupos = {}
    for p in pedidos:
        emp = (p.get("empresa_faturadora") or "—").upper()
        grupos.setdefault(emp, []).append(p)

    total_geral = sum(_fmt_val_num(p.get("valor_total")) for p in pedidos)

    for emp, itens in grupos.items():
        cor_emp = CORES_EMP.get(emp, C_ESCURO)
        grp_style = ParagraphStyle(
            f"grp_{emp}", fontSize=9, textColor=cor_emp,
            fontName="Helvetica-Bold", leading=12
        )
        subtotal = sum(_fmt_val_num(p.get("valor_total")) for p in itens)
        grp_label = Paragraph(
            f"{emp}  —  {len(itens)} pedido{'s' if len(itens)!=1 else ''}"
            f"  |  Subtotal: {_fmt_val(subtotal)}",
            grp_style
        )
        elems.append(grp_label)
        elems.append(Spacer(1, 1.5 * mm))
        elems += _montar_tabela(itens, cor_emp)
        elems.append(Spacer(1, 5 * mm))

    # Total geral
    elems.append(HRFlowable(width="100%", thickness=1,
                             color=C_VERMELHO, spaceAfter=2 * mm))
    elems.append(Paragraph(
        f"TOTAL GERAL: {_fmt_val(total_geral)}",
        ParagraphStyle("total_g", fontSize=11, textColor=C_VERMELHO,
                       fontName="Helvetica-Bold", alignment=TA_RIGHT)
    ))
    return elems


def _tabela_simples(pedidos: list) -> list:
    total = sum(_fmt_val_num(p.get("valor_total")) for p in pedidos)
    elems = _montar_tabela(pedidos, C_VERMELHO)
    elems.append(Spacer(1, 3 * mm))
    elems.append(HRFlowable(width="100%", thickness=1,
                             color=C_VERMELHO, spaceAfter=2 * mm))
    elems.append(Paragraph(
        f"TOTAL GERAL: {_fmt_val(total)}",
        ParagraphStyle("total_s", fontSize=11, textColor=C_VERMELHO,
                       fontName="Helvetica-Bold", alignment=TA_RIGHT)
    ))
    return elems


def _montar_tabela(pedidos: list, cor_grupo) -> list:
    W_PAGE = landscape(A4)[0] - 28 * mm
    cabecalho = ["Nº PEDIDO", "FORNECEDOR", "OBRA",
                 "COND. PGTO", "FORMA PGTO", "EMPRESA", "VALOR TOTAL"]
    col_w = [
        18 * mm,
        W_PAGE * 0.22,
        W_PAGE * 0.28,
        22 * mm,
        22 * mm,
        25 * mm,
        28 * mm,
    ]

    s_hdr = ParagraphStyle("th",  fontSize=8,  textColor=C_BRANCO,
                            fontName="Helvetica-Bold", alignment=TA_CENTER, leading=10)
    s_num = ParagraphStyle("num", fontSize=9,  textColor=cor_grupo,
                            fontName="Helvetica-Bold", alignment=TA_CENTER, leading=11)
    s_txt = ParagraphStyle("txt", fontSize=8,  textColor=C_ESCURO,
                            fontName="Helvetica", leading=10)
    s_ctr = ParagraphStyle("ctr", fontSize=8,  textColor=C_MEDIO,
                            fontName="Helvetica", alignment=TA_CENTER, leading=10)
    s_val = ParagraphStyle("val", fontSize=9,  textColor=C_ESCURO,
                            fontName="Helvetica-Bold", alignment=TA_RIGHT, leading=11)

    rows = [[Paragraph(h, s_hdr) for h in cabecalho]]

    for i, p in enumerate(pedidos):
        emp   = (p.get("empresa_faturadora") or "—").upper()
        cor_e = CORES_EMP.get(emp, C_ESCURO)
        s_emp_row = ParagraphStyle(
            f"emp_{i}", fontSize=8, fontName="Helvetica-Bold",
            alignment=TA_CENTER, leading=10, textColor=cor_e
        )
        rows.append([
            Paragraph(f"#{p.get('numero','—')}", s_num),
            Paragraph(str(p.get("fornecedor_nome") or p.get("fornecedor") or "—")[:50], s_txt),
            Paragraph(str(p.get("obra_nome")      or p.get("obra")       or "—")[:60], s_txt),
            Paragraph(str(p.get("condicao_pagamento") or "—"), s_ctr),
            Paragraph(str(p.get("forma_pagamento")    or "—"), s_ctr),
            Paragraph(emp, s_emp_row),
            Paragraph(_fmt_val(p.get("valor_total")), s_val),
        ])

    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  C_FUNDO_HDR),
        ("ROWBACKGROUNDS",(0,1), (-1, -1), [C_BRANCO, C_ALT]),
        ("GRID",         (0, 0), (-1, -1), 0.3, C_LINHA),
        ("LINEBELOW",    (0, 0), (-1, 0),  1.5, cor_grupo),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return [tbl]


def _numerar_pagina(canvas, doc):
    canvas.saveState()
    W, H = landscape(A4)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_CLARO)
    canvas.drawRightString(W - 14 * mm, 8 * mm, f"Página {doc.page}")
    canvas.restoreState()
