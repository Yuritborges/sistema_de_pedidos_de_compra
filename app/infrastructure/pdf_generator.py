import os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas

from config import EMPRESAS_FATURADORAS, PEDIDOS_DIR
from app.core.dto.pedido_dto import PedidoDTO

# ── Dimensões da página A4 ────────────────────────────────────────────────────
W, H = A4          # largura ≈ 595pt | altura ≈ 842pt
M    = 14 * mm     # margem lateral esquerda e direita
CW   = W - 2 * M  # largura útil (conteúdo entre as margens)

# ── Paleta de cores (tons de cinza — aspecto profissional para impressão) ──────
C_PRETO  = colors.HexColor("#111111")
C_ESCURO = colors.HexColor("#333333")
C_MEDIO  = colors.HexColor("#666666")
C_CLARO  = colors.HexColor("#AAAAAA")
C_LINHA  = colors.HexColor("#CCCCCC")
C_FUNDO  = colors.HexColor("#F5F5F5")
C_BRANCO = colors.white
C_HDR    = colors.HexColor("#222222")

# ── Diretório das logos ───────────────────────────────────────────────────────
_LOGOS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'logos')
)
_LOGO_NOMES = {
    "BRASUL":      "logo_brasul.png",
    "JB":          "logo_jb.png",
    "B&B":         "logo_bb.png",
    "INTERIORANA": "logo_interiorana.png",
    "INTERBRAS":   "logo_interbras.png",
}


def _logo_path(empresa: str):
    """Retorna o caminho da logo ou None se o arquivo não existir."""
    nome = _LOGO_NOMES.get(empresa, "")
    p    = os.path.join(_LOGOS_DIR, nome)
    return p if (nome and os.path.exists(p)) else None


def _montar_observacao(emp: dict, obs_usuario: str) -> str:
    """
    Monta o texto do bloco de Observação (campo extra, abaixo dos itens).
    Agora contém APENAS o texto digitado pelo usuário.
    A obs_padrao da empresa vai para o bloco de faturamento (_bloco_fat).
    """
    return (obs_usuario or "").strip()


def _cep_empresa(emp: dict) -> str:
    """Extrai o CEP do endereço da empresa (último token com 8-9 dígitos)."""
    end = emp.get("endereco", "")
    for token in reversed(end.replace(",", " ").split()):
        t = token.strip()
        if len(t) in (8, 9) and any(c.isdigit() for c in t):
            return t
    return ""


def _cidade_uf_empresa(emp: dict):
    """
    Tenta extrair cidade e UF do endereço da empresa.
    Suporta formatos: 'Cidade, UF - CEP', 'Cidade/UF', 'Cidade, UF'
    """
    # Primeiro verifica se a empresa tem campos diretos
    cidade = emp.get("cidade", "").strip()
    uf     = emp.get("uf", "").strip()
    if cidade and uf:
        return cidade, uf

    end = emp.get("endereco", "")
    try:
        # Formato: Cidade/UF (ex: São Paulo/SP)
        m = re.search(r'([A-Za-zÀ-ÿ\s]+)/([A-Z]{2})', end)
        if m:
            return m.group(1).strip(), m.group(2).strip()

        # Formato: Cidade, UF - ou Cidade, UF (fim)
        m = re.search(r'([A-Za-zÀ-ÿ\s]+),\s*([A-Z]{2})(?:\s*[-–]|$)', end)
        if m:
            return m.group(1).strip(), m.group(2).strip()
    except Exception:
        pass
    return "", ""


class PedidoCompraGenerator:
    """
    Gera o arquivo PDF de um pedido de compra.

    Uso:
        gen = PedidoCompraGenerator()
        path = gen.gerar(dto)   # dto é um PedidoDTO
    """

    def __init__(self):
        os.makedirs(PEDIDOS_DIR, exist_ok=True)

    def gerar(self, dto: PedidoDTO) -> str:
        emp     = EMPRESAS_FATURADORAS.get(dto.empresa_faturadora,
                                           EMPRESAS_FATURADORAS["BRASUL"])
        caminho = os.path.join(PEDIDOS_DIR, self._nome_arquivo(dto))
        c = rl_canvas.Canvas(caminho, pagesize=A4)
        self._gerar_paginas(c, dto, emp)
        c.save()
        return caminho

    # ══════════════════════════════════════════════════════════════════════════
    # PAGINAÇÃO AUTOMÁTICA
    # Calcula quantos itens cabem por página e divide em fatias.
    # ══════════════════════════════════════════════════════════════════════════

    def _gerar_paginas(self, c, dto, emp):
        """
        Gera páginas com ajuste automático inteligente de escala.

        MODO PADRÃO (≤ 15 itens):
            Blocos normais, ROW_H = 6mm, fonte 7.5pt — layout idêntico ao atual.

        MODO COMPACTO (16–31 itens):
            Blocos fixos levemente comprimidos + ROW_H reduzido automaticamente
            para encaixar TODOS os itens em uma única página.
            ROW_H mínimo: 3.5mm (ainda legível para impressão).

        MODO MULTI-PÁGINA (> 31 itens):
            Usa o modo compacto e pagina normalmente quando não cabe.
        """
        obs_padrao = (emp.get("obs_padrao") or "").strip()
        obs_txt    = _montar_observacao(emp, dto.observacao_extra)
        n_itens    = len(dto.itens)

        def _calc_blocos(escala):
            """Calcula alturas de todos os blocos com fator de escala (1.0=normal, <1=compacto)."""
            e = escala
            ht      = 28*mm*e
            hdf     = 7*mm*e
            hf      = 28*mm*e
            hcob    = 14*mm*e
            hrod    = max(18*mm, 22*mm*e)
            hfat    = 14*mm*e
            hent    = 18*mm*e
            hdr_h   = max(5*mm, 7*mm*e)
            tot_h   = max(14*mm, 18*mm*e)

            hobs_emp = 0
            if obs_padrao:
                nl = max(1, (len(obs_padrao)//100) + obs_padrao.count('\n') + 1)
                hobs_emp = (8*e + nl * 4.5*e) * mm

            hobs = 0
            if obs_txt:
                nl2 = max(1, (len(obs_txt)//110) + obs_txt.count('\n') + 1)
                hobs = (8*e + nl2 * 4.5*e) * mm

            blocos = ht + hdf + hf + hcob + hfat + hobs_emp + hent + hobs + hdr_h + tot_h + hrod
            espaco = H - 2*M - blocos
            return dict(
                H_TOPO=ht, H_DATAFAIXA=hdf, H_FORN=hf, H_COB=hcob,
                H_ROD=hrod, H_FAT=hfat, H_ENT=hent, H_OBS_EMP=hobs_emp,
                H_OBS=hobs, HDR_H=hdr_h, TOT_H=tot_h,
                espaco=espaco
            )

        ROW_H_MIN = 3.5 * mm   # mínimo absolutamente legível para impressão

        # 1. Tenta encaixar tudo em 1 página com escala normal (1.0)
        b = _calc_blocos(1.0)
        linhas_normal = int(b["espaco"] / (6*mm))

        if n_itens <= linhas_normal:
            # Modo padrão — cabe sem comprimir nada
            escala  = 1.0
            ROW_H   = 6 * mm
        else:
            # 2. Tenta comprimir os blocos (escala 0.85) para ganhar espaço
            b85 = _calc_blocos(0.85)
            row_h_85 = b85["espaco"] / n_itens
            if row_h_85 >= ROW_H_MIN:
                escala = 0.85
                ROW_H  = max(ROW_H_MIN, row_h_85)
            else:
                # 3. Comprime ao máximo (escala 0.78) e usa ROW_H mínimo
                escala = 0.78
                b = _calc_blocos(0.78)
                ROW_H = ROW_H_MIN

        b = _calc_blocos(escala)

        # Fonte e cabeçalho da tabela escalam com ROW_H
        self._fonte_tabela = max(5.5, round(7.5 * (ROW_H / (6*mm)), 1))
        self._hdr_tabela   = max(4.5*mm, b["HDR_H"])

        linhas_p1 = max(1, int(b["espaco"] / ROW_H))
        blocos_pn = b["H_TOPO"] + b["H_DATAFAIXA"] + b["HDR_H"] + b["TOT_H"] + b["H_ROD"]
        linhas_pn = max(1, int((H - 2*M - blocos_pn) / ROW_H))

        itens  = dto.itens
        fatias = []
        if n_itens <= linhas_p1:
            fatias.append((itens, n_itens))
        else:
            fatias.append((itens[:linhas_p1], linhas_p1))
            restante = itens[linhas_p1:]
            while restante:
                fatia = restante[:linhas_pn]
                fatias.append((fatia, len(fatia)))
                restante = restante[linhas_pn:]

        for idx, (fatia_itens, n_linhas) in enumerate(fatias):
            primeira = (idx == 0)
            ultima   = (idx == len(fatias) - 1)
            self._desenhar_pagina(
                c, dto, emp, fatia_itens, n_linhas,
                primeira, ultima, idx+1, len(fatias),
                b["H_TOPO"], b["H_DATAFAIXA"], b["H_FORN"], b["H_COB"],
                b["H_FAT"], b["H_OBS_EMP"], b["H_ENT"], b["H_OBS"], b["H_ROD"],
                self._hdr_tabela, ROW_H, b["TOT_H"],
                obs_txt, obs_padrao
            )
            if not ultima:
                c.showPage()

    def _desenhar_pagina(
        self, c, dto, emp, itens_pagina, n_linhas,
        primeira, ultima, num_pag, total_pag,
        H_TOPO, H_DATAFAIXA, H_FORN, H_COB,
        H_FAT, H_OBS_EMP, H_ENT, H_OBS, H_ROD,
        HDR_H, ROW_H, TOT_H, obs_txt, obs_padrao
    ):
        """
        Desenha uma página completa do PDF.

        ORDEM DOS BLOCOS NA PRIMEIRA PÁGINA:
            Topo → Faixa data → Fornecedor → Cobrança →
            Faturamento → [Obs empresa] → Entrega → [Obs usuário] → Tabela
        """
        y = H - M

        y = self._bloco_topo(c, dto, emp, y, H_TOPO, num_pag, total_pag)
        y = self._faixa_data(c, dto, y, H_DATAFAIXA)

        if primeira:
            y = self._bloco_forn(c, dto, y, H_FORN)
            y = self._bloco_cob(c, dto, emp, y, H_COB)
            y = self._bloco_fat(c, dto, emp, y, H_FAT)
            # Bloco separado para obs_padrao da empresa (quadrado próprio)
            if obs_padrao:
                y = self._bloco_obs_empresa(c, obs_padrao, y, H_OBS_EMP)
            y = self._bloco_ent(c, dto, y, H_ENT)
            if obs_txt:
                y = self._bloco_obs(c, obs_txt, y, H_OBS)

        self._tabela_itens(
            c, dto, itens_pagina, y, n_linhas,
            HDR_H, ROW_H, TOT_H,
            mostrar_totais=ultima
        )
        self._rodape(c, emp)

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 1 — Topo
    # ══════════════════════════════════════════════════════════════════════════

    def _bloco_topo(self, c, dto, emp, y, alt, num_pag=1, total_pag=1):
        """Logo + dados da empresa + número do pedido."""
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.5)
        c.rect(M, y-alt, CW, alt, fill=0, stroke=1)

        LOGO_W = 44*mm; LOGO_H = 22*mm
        logo = _logo_path(dto.empresa_faturadora)
        if logo:
            try:
                c.drawImage(logo, M+3*mm, y-alt+3*mm,
                            width=LOGO_W, height=LOGO_H,
                            preserveAspectRatio=True, mask='auto')
            except Exception:
                c.setFont("Helvetica-Bold", 10); c.setFillColor(C_PRETO)
                c.drawString(M+3*mm, y-alt/2, dto.empresa_faturadora)

        cx = M + LOGO_W + 4*mm
        c.setFont("Helvetica-Bold", 11); c.setFillColor(C_PRETO)
        c.drawString(cx, y-8*mm, emp["razao_social"])
        c.setFont("Helvetica", 7.5); c.setFillColor(C_ESCURO)
        c.drawString(cx, y-13*mm, emp["endereco"][:80])
        c.drawString(cx, y-17.5*mm, f"Tel: {emp['telefone']}   |   {emp['email']}")

        c.setFont("Helvetica-Bold", 22); c.setFillColor(C_PRETO)
        c.drawRightString(W-M-2*mm, y-11*mm, f"#{dto.numero}")
        c.setFont("Helvetica", 8); c.setFillColor(C_MEDIO)
        c.drawRightString(W-M-2*mm, y-16.5*mm, "PEDIDO DE COMPRA")
        c.drawRightString(W-M-2*mm, y-21*mm, dto.comprador)

        if total_pag > 1:
            c.setFont("Helvetica", 7); c.setFillColor(C_MEDIO)
            c.drawRightString(W-M-2*mm, y-26*mm, f"Pág {num_pag}/{total_pag}")

        return y - alt

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 2 — Faixa de data
    # ══════════════════════════════════════════════════════════════════════════

    def _faixa_data(self, c, dto, y, alt):
        """Faixa cinza com data, prazo e vencimento."""
        c.setFillColor(C_FUNDO)
        c.rect(M, y-alt, CW, alt, fill=1, stroke=0)
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.3)
        c.rect(M, y-alt, CW, alt, fill=0, stroke=1)
        c.setFont("Helvetica-Bold", 8); c.setFillColor(C_ESCURO)
        c.drawString(M+3*mm, y-alt/2-2, f"Data: {dto.data_pedido}")
        c.setFont("Helvetica", 8)
        c.drawCentredString(W/2, y-alt/2-2,
            f"Prazo: {dto.prazo_entrega} dias   |   "
            f"Vencimento: {dto.estimativa_vencimento}   |   "
            f"Entrega prevista: {dto.data_prevista_entrega}")
        return y - alt - 1*mm

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 3 — Fornecedor (CORRIGIDO)
    # ══════════════════════════════════════════════════════════════════════════

    def _bloco_forn(self, c, dto, y, alt):
        """
        Dados do fornecedor — cada campo com label acima e valor abaixo.
        Resolve a sobreposição do layout anterior.
        """
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.5)
        c.rect(M, y-alt, CW, alt, fill=0, stroke=1)

        c.setFillColor(C_FUNDO)
        c.rect(M, y-6*mm, CW, 6*mm, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 7.5); c.setFillColor(C_ESCURO)
        c.drawString(M+3*mm, y-4.5*mm, "FORNECEDOR")

        col2 = M + CW*0.5
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.3)
        c.line(col2, y-6*mm, col2, y-alt)

        def campo(label, valor, x, y_base):
            # Label menor em cinza (acima)
            c.setFont("Helvetica-Bold", 6.5); c.setFillColor(C_MEDIO)
            c.drawString(x, y_base+4.5*mm, label.upper())
            # Valor em preto (abaixo)
            c.setFont("Helvetica", 8); c.setFillColor(C_PRETO)
            c.drawString(x, y_base, str(valor or "—")[:45])

        y1 = y - 14*mm
        campo("Razão Social", dto.fornecedor_razao, M+3*mm,     y1)
        campo("Fornecedor",   dto.fornecedor_nome,  col2+3*mm,  y1)

        y2 = y - 24*mm
        campo("E-mail",   dto.fornecedor_email,    M+3*mm,      y2)
        campo("Vendedor", dto.fornecedor_vendedor, col2+3*mm,   y2)
        campo("Telefone", dto.fornecedor_telefone, col2+60*mm,  y2)

        return y - alt - 1*mm

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 4 — Endereço de cobrança (CORRIGIDO)
    # ══════════════════════════════════════════════════════════════════════════

    def _bloco_cob(self, c, dto, emp, y, alt):
        """Endereço de cobrança — lê cidade/UF do config.py."""
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.5)
        c.rect(M, y-alt, CW, alt, fill=0, stroke=1)

        # Endereço de cobrança = endereço da empresa faturadora (config.py)
        end_cob = emp.get("endereco", "")
        cep_cob = emp.get("cep", "") or _cep_empresa(emp)

        # Extrai cidade e UF do config.py diretamente se disponível,
        # senão tenta parsear do campo endereco
        cidade = emp.get("cidade", "")
        uf     = emp.get("uf", "")
        if not cidade or not uf:
            cidade_p, uf_p = _cidade_uf_empresa(emp)
            if not cidade: cidade = cidade_p
            if not uf:     uf     = uf_p

        def par(lbl, val, x, yy):
            c.setFont("Helvetica-Bold", 7.5); c.setFillColor(C_ESCURO)
            c.drawString(x, yy, lbl)
            c.setFont("Helvetica", 7.5); c.setFillColor(C_PRETO)
            off = c.stringWidth(lbl, "Helvetica-Bold", 7.5) + 2
            c.drawString(x+off, yy, str(val or "—")[:50])

        par("Endereço de Cobrança:", end_cob[:52], M+3*mm,    y-5*mm)
        par("CEP:",      cep_cob,   M+CW*0.75,                y-5*mm)
        par("Cidade:",   cidade,    M+3*mm,                    y-11*mm)
        par("UF:",       uf,        M+CW*0.5,                  y-11*mm)
        par("Comprador:", dto.comprador, M+CW*0.72,            y-11*mm)

        return y - alt - 1*mm

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 5 — Faturamento (ATUALIZADO: data em destaque + obs_padrao embaixo)
    # ══════════════════════════════════════════════════════════════════════════

    def _bloco_fat(self, c, dto, emp, y, alt):
        """
        Bloco de faturamento — condição, forma, prazo e data prevista.
        A obs_padrao da empresa agora fica em _bloco_obs_empresa (quadrado próprio).
        """
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.5)
        c.rect(M, y-alt, CW, alt, fill=0, stroke=1)

        cond  = dto.condicao_pagamento or "—"
        forma = dto.forma_pagamento or "—"

        # Linha 1: Faturamento + Estimativa de vencimento
        c.setFont("Helvetica-Bold", 8); c.setFillColor(C_ESCURO)
        c.drawString(M+3*mm, y-5.5*mm, "Faturamento:")
        c.setFont("Helvetica-Bold", 9); c.setFillColor(C_PRETO)
        c.drawString(M+32*mm, y-5.5*mm, f"{cond} dias   {forma}")
        c.setFont("Helvetica-Bold", 8); c.setFillColor(C_ESCURO)
        c.drawRightString(W-M-3*mm, y-5.5*mm,
                          f"Estimativa de vencimento: {dto.estimativa_vencimento}")

        # Linha 2: Prazo + Data Prevista centralizada e em fonte maior
        c.setFont("Helvetica-Bold", 8); c.setFillColor(C_ESCURO)
        c.drawString(M+3*mm, y-11*mm, "PRAZO  ENTREGA")
        c.setFont("Helvetica-Bold", 9); c.setFillColor(C_PRETO)
        c.drawString(M+42*mm, y-11*mm, f"{dto.prazo_entrega} dias")

        c.setFont("Helvetica-Bold", 8); c.setFillColor(C_ESCURO)
        c.drawRightString(W-M-30*mm, y-11*mm, "DATA PREVISTA DA ENTREGA")

        # Caixinha: fundo cinza, data centralizada em 10pt bold
        c.setStrokeColor(C_LINHA); c.setFillColor(C_FUNDO)
        c.rect(W-M-28*mm, y-14*mm, 25*mm, 6.5*mm, fill=1, stroke=1)
        c.setFont("Helvetica-Bold", 10); c.setFillColor(C_PRETO)
        cx_data = W - M - 28*mm + 12.5*mm
        c.drawCentredString(cx_data, y-11*mm, dto.data_prevista_entrega)

        return y - alt - 1*mm

    def _bloco_obs_empresa(self, c, obs_padrao: str, y, alt):
        """
        Bloco separado para a observação padrão da empresa.

        VISUAL:
            Fundo cinza levemente diferente do bloco de faturamento.
            Título em bold pequeno: 'NOTA FISCAL'
            Texto do obs_padrao em bold 7.5pt, preto.

        POSIÇÃO:
            Logo abaixo do bloco de faturamento, acima do bloco de entrega.
            Cada empresa tem seu próprio texto no config.py (obs_padrao).

        EXEMPLO para JB:
            ┌─────────────────────────────────────────────────────┐
            │ NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA    │
            │ JB CONSTRUÇÕES E EMPREENDIMENTOS LTDA               │
            │ OBS: CONTAR FATURAMENTO A PARTIR DO DIA 27/12/24... │
            └─────────────────────────────────────────────────────┘
        """
        # Fundo levemente amarelado para diferenciar dos outros blocos
        c.setFillColor(colors.HexColor("#FDFAF0"))
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.5)
        c.rect(M, y-alt, CW, alt, fill=1, stroke=1)

        # Renderiza o texto do obs_padrao, linha por linha
        c.setFont("Helvetica-Bold", 7.5); c.setFillColor(C_PRETO)
        yi = y - 5*mm

        for paragrafo in obs_padrao.split('\n'):
            if not paragrafo.strip():
                yi -= 3.5*mm
                continue
            palavras = paragrafo.split(); linha = ""
            for p in palavras:
                teste = (linha + " " + p).strip()
                if c.stringWidth(teste, "Helvetica-Bold", 7.5) > CW - 6*mm:
                    c.drawString(M+3*mm, yi, linha)
                    yi -= 4.5*mm; linha = p
                else:
                    linha = teste
            if linha:
                c.drawString(M+3*mm, yi, linha)
                yi -= 4.5*mm

        return y - alt - 1*mm

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 6 — Local de entrega
    # ══════════════════════════════════════════════════════════════════════════

    def _bloco_ent(self, c, dto, y, alt):
        """Endereço de entrega (obra)."""
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.5)
        c.rect(M, y-alt, CW, alt, fill=0, stroke=1)

        def par(lbl, val, x, yy):
            c.setFont("Helvetica-Bold", 7.5); c.setFillColor(C_ESCURO)
            c.drawString(x, yy, lbl)
            c.setFont("Helvetica", 7.5); c.setFillColor(C_PRETO)
            off = c.stringWidth(lbl, "Helvetica-Bold", 7.5) + 2
            c.drawString(x+off, yy, str(val or "—")[:44])

        # Distribui as 3 linhas proporcionalmente dentro do bloco
        l1 = y - alt * 0.22   # linha 1 — Endereço / Bairro
        l2 = y - alt * 0.55   # linha 2 — Obra / Contrato
        l3 = y - alt * 0.88   # linha 3 — CEP / Cidade / UF

        par("Local de Entrega:", dto.endereco_entrega, M+3*mm,    l1)
        par("Bairro:",           dto.bairro_entrega,   M+CW*0.5,  l1)
        par("OBRA:",             dto.obra.upper(),      M+3*mm,    l2)
        par("Contrato Obra:",    dto.contrato_obra,     M+CW*0.5,  l2)
        par("CEP:",              dto.cep_entrega,       M+3*mm,    l3)
        par("Cidade:",           dto.cidade_entrega,    M+CW*0.3,  l3)
        par("UF:",               dto.uf_entrega,        M+CW*0.65, l3)

        return y - alt - 1*mm

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 7 — Observação extra (só o texto do usuário)
    # ══════════════════════════════════════════════════════════════════════════

    def _bloco_obs(self, c, obs_txt, y, alt):
        """
        Observação extra digitada pelo usuário.
        A obs_padrao da empresa agora fica no bloco de faturamento (_bloco_fat).
        """
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.5)
        c.setFillColor(C_FUNDO)
        c.rect(M, y-alt, CW, alt, fill=1, stroke=1)

        c.setFont("Helvetica-Bold", 7.5); c.setFillColor(C_ESCURO)
        c.drawString(M+3*mm, y-4.5*mm, "OBSERVAÇÃO:")
        c.setFont("Helvetica", 7.5); c.setFillColor(C_PRETO)

        yi = y - 9*mm
        for paragrafo in obs_txt.split('\n'):
            if not paragrafo.strip():
                yi -= 4.5*mm; continue
            palavras = paragrafo.split(); linha = ""
            for p in palavras:
                teste = (linha + " " + p).strip()
                if c.stringWidth(teste, "Helvetica", 7.5) > CW - 6*mm:
                    c.drawString(M+3*mm, yi, linha); yi -= 4.5*mm; linha = p
                else:
                    linha = teste
            if linha:
                c.drawString(M+3*mm, yi, linha); yi -= 4.5*mm

        return y - alt - 1*mm

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 8 — Tabela de itens + totais
    # ══════════════════════════════════════════════════════════════════════════

    def _tabela_itens(self, c, dto, itens_pagina, y, n_linhas,
                      HDR_H, ROW_H, TOT_H, mostrar_totais=True):
        """
        Tabela de itens para UMA página.
        mostrar_totais=True apenas na última página.
        """
        cols = [
            {"h": "ITEM",                  "w": 10*mm, "a": "c"},
            {"h": "DESCRIÇÃO DO MATERIAL", "w": 84*mm, "a": "l"},
            {"h": "QTDADE",                "w": 16*mm, "a": "c"},
            {"h": "UNID.",                 "w": 14*mm, "a": "c"},
            {"h": "VLR UNITÁRIO",          "w": 30*mm, "a": "r"},
            {"h": "VLR TOTAL",             "w": 0,     "a": "r"},
        ]
        cols[-1]["w"] = CW - sum(col["w"] for col in cols[:-1])

        # Fonte escalonada conforme ROW_H calculado em _gerar_paginas
        fnt = getattr(self, '_fonte_tabela', 7.5)

        # Cabeçalho da tabela
        c.setFillColor(C_HDR)
        c.rect(M, y-HDR_H, CW, HDR_H, fill=1, stroke=0)
        c.setFillColor(C_BRANCO); c.setFont("Helvetica-Bold", max(6, fnt-0.5))
        x = M
        for col in cols:
            if   col["a"] == "c": c.drawCentredString(x+col["w"]/2, y-HDR_H/2-2, col["h"])
            elif col["a"] == "r": c.drawRightString(x+col["w"]-2*mm, y-HDR_H/2-2, col["h"])
            else:                 c.drawString(x+2*mm, y-HDR_H/2-2, col["h"])
            x += col["w"]
        y -= HDR_H
        y_tab_topo = y

        for i in range(n_linhas):
            if i % 2 == 0:
                c.setFillColor(colors.HexColor("#FAFAFA"))
                c.rect(M, y-ROW_H, CW, ROW_H, fill=1, stroke=0)
            c.setStrokeColor(C_LINHA); c.setLineWidth(0.3)
            c.line(M, y-ROW_H, M+CW, y-ROW_H)

            if i < len(itens_pagina):
                item = itens_pagina[i]
                yt = y - ROW_H/2 - 2
                x  = M
                dados = [
                    (str(i+1),                       "c", True ),
                    (item.descricao[:56],             "l", False),
                    (self._fmt_num(item.quantidade),  "c", False),
                    (item.unidade,                    "c", False),
                    (self._fmt_val(item.valor_unitario), "r", False),
                    (self._fmt_val(item.valor_total),    "r", False),
                ]
                for j, (val, alg, bold) in enumerate(dados):
                    w = cols[j]["w"]
                    c.setFont("Helvetica-Bold" if bold else "Helvetica", fnt)
                    c.setFillColor(C_PRETO)
                    if   alg == "c": c.drawCentredString(x+w/2, yt, val)
                    elif alg == "r": c.drawRightString(x+w-2*mm, yt, val)
                    else:            c.drawString(x+2*mm, yt, val)
                    x += w
            else:
                c.setFont("Helvetica", max(5.5, fnt-1)); c.setFillColor(C_CLARO)
                c.drawCentredString(M+cols[0]["w"]/2, y-ROW_H/2-2, str(i+1))
            y -= ROW_H

        # Borda externa e divisórias verticais
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.5)
        c.rect(M, y, CW, y_tab_topo-y, fill=0, stroke=1)
        x = M
        for col in cols[:-1]:
            x += col["w"]
            c.line(x, y_tab_topo, x, y)

        # Totais (SUB TOTAL, DESCONTO, TOTAL)
        if mostrar_totais:
            desconto    = float(getattr(dto, 'desconto', 0) or 0)
            total_final = round(dto.subtotal - desconto, 2)
            larg_tot    = 62*mm
            for lbl, val, negrito in [
                ("SUB TOTAL", dto.subtotal, False),
                ("DESCONTO",  desconto,     False),
                ("TOTAL",     total_final,  True ),
            ]:
                if negrito:
                    c.setFillColor(C_HDR)
                    c.rect(M+CW-larg_tot, y-6*mm, larg_tot, 6*mm, fill=1, stroke=0)
                    c.setFillColor(C_BRANCO); c.setFont("Helvetica-Bold", 9)
                else:
                    c.setFillColor(C_PRETO); c.setFont("Helvetica", 8)
                c.drawRightString(W-M-33*mm, y-4*mm, lbl)
                c.drawRightString(W-M-2*mm,  y-4*mm, f"R$ {self._fmt_val(val)}")
                c.setStrokeColor(C_LINHA); c.setLineWidth(0.3)
                c.rect(M+CW-larg_tot, y-6*mm, larg_tot, 6*mm, fill=0, stroke=1)
                y -= 6*mm

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 9 — Rodapé fixo na base
    # ══════════════════════════════════════════════════════════════════════════

    def _rodape(self, c, emp):
        """Rodapé com instruções, e-mails e horários de recebimento."""
        y = 20*mm
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.5)
        c.line(M, y, W-M, y)

        c.setFont("Helvetica-Oblique", 7); c.setFillColor(C_ESCURO)
        c.drawString(M, y-4*mm,
            "Destacar o endereço e o Nome da obra com o Nº de meu pedido "
            "no campo de Observações.")
        c.setFont("Helvetica-Bold", 7); c.setFillColor(C_ESCURO)
        c.drawString(M, y-8.5*mm, "Notas e Boletos encaminha para:")
        c.setFont("Helvetica", 7); c.setFillColor(colors.HexColor("#0055AA"))
        c.drawString(M, y-12.5*mm, "notafiscal@brasulconstrutora.com.br")
        c.drawString(M, y-16.5*mm, "viviane@brasulconstrutora.com.br")

        c.setFont("Helvetica-Bold", 7); c.setFillColor(C_ESCURO)
        c.drawRightString(W-M, y-4*mm, "Horário de RECEBIMENTO NA OBRA")
        c.setFont("Helvetica", 7)
        c.drawRightString(W-M, y-8.5*mm,
            "Segunda a Quinta-feira das 07:30h às 11:30h e das 13:00h às 15:30h")
        c.drawRightString(W-M, y-12.5*mm,
            "Sexta-feira das 07:30h às 11:30h e das 13:00h às 14:30h")

    # ══════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _fmt_val(v: float) -> str:
        """Formata R$: 1234.5 → '1.234,50'"""
        return f"{v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

    @staticmethod
    def _fmt_num(v: float) -> str:
        """Formata quantidade: 2.0 → '2' | 2.5 → '2,5'"""
        try:
            if float(v) == int(float(v)): return str(int(v))
            return f"{float(v):.2f}".replace(".", ",")
        except Exception:
            return str(v)

    @staticmethod
    def _nome_arquivo(dto: PedidoDTO) -> str:
        """Gera nome do arquivo: PC-2582-BRASUL-NOME_DA_OBRA.pdf"""
        obra = "".join(
            ch for ch in dto.obra if ch.isalnum() or ch in " _-"
        )[:28].strip().replace(" ", "_")
        return f"PC-{dto.numero}-{dto.empresa_faturadora}-{obra}.pdf"
