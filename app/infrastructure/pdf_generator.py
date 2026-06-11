import os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas
from app.data.database import copiar_arquivo_para_rede
from app.data.usuarios_store import obter_email_comprador
from config import EMPRESAS_FATURADORAS, PEDIDOS_DIR
from app.config.settings import OBS_FATURAMENTO_DATA_ENTREGA
from app.core.dto.pedido_dto import PedidoDTO


# Nomes antigos/errados gravados no banco → chave em EMPRESAS_FATURADORAS
_ALIASES_EMPRESA_FATURADORA = {
    "INTERIORANA CONSTRUTORA LTDA": "INTERIORANA",
}


def _resolver_empresa_faturadora(empresa_faturadora: str) -> dict:
    """
    Retorna o bloco de EMPRESAS_FATURADORAS para o nome gravado no pedido.
    Evita cair na Brasul quando o texto vem como nome longo (ex.: CONSTRUTORA INTERIORANA LTDA).
    """
    raw = str(empresa_faturadora or "").strip()
    if not raw:
        return EMPRESAS_FATURADORAS["BRASUL"]
    if raw in EMPRESAS_FATURADORAS:
        return EMPRESAS_FATURADORAS[raw]
    up = raw.upper()
    alias_key = _ALIASES_EMPRESA_FATURADORA.get(up)
    if alias_key and alias_key in EMPRESAS_FATURADORAS:
        return EMPRESAS_FATURADORAS[alias_key]
    if up in EMPRESAS_FATURADORAS:
        return EMPRESAS_FATURADORAS[up]
    if ("B&B" in raw or "B & B" in up) and "B&B" in EMPRESAS_FATURADORAS:
        return EMPRESAS_FATURADORAS["B&B"]
    for key in ("INTERIORANA", "INTERBRAS", "JB", "BRASUL"):
        if key in EMPRESAS_FATURADORAS and key in up:
            return EMPRESAS_FATURADORAS[key]
    return EMPRESAS_FATURADORAS["BRASUL"]


def _empresa_sem_email_cabecalho(empresa_faturadora: str) -> bool:
    """Empresas que exibem só telefone/CNPJ no topo (sem e-mail do comprador)."""
    return "INTERBRAS" in str(empresa_faturadora or "").upper()


def _email_cabecalho_pdf(dto: PedidoDTO, emp: dict) -> str:
    """
    E-mail no topo do PDF: do comprador logado/cadastrado.
    Interbras: sem e-mail por enquanto. Demais: fallback no config da empresa.
    """
    if _empresa_sem_email_cabecalho(dto.empresa_faturadora):
        return ""
    email = obter_email_comprador(dto.comprador)
    if email:
        return email
    return str(emp.get("email") or "").strip()


# ── Dimensões da página A4 ────────────────────────────────────────────────────
W, H = A4          # largura ≈ 595pt | altura ≈ 842pt
M    = 14 * mm     # margem lateral esquerda e direita
CW   = W - 2 * M  # largura útil (conteúdo entre as margens)

# Paleta otimizada para impressão em P&B — contraste máximo
C_PRETO  = colors.HexColor("#000000")   # texto principal — preto puro
C_ESCURO = colors.HexColor("#111111")   # labels e títulos
C_MEDIO  = colors.HexColor("#444444")   # texto secundário
C_CLARO  = colors.HexColor("#777777")   # numeração linhas vazias
C_LINHA  = colors.HexColor("#888888")   # bordas das células — mais escuro
C_FUNDO  = colors.HexColor("#EEEEEE")   # fundo alternado — mais visível
C_BRANCO = colors.white
C_HDR    = colors.HexColor("#000000")   # cabeçalho tabela — preto sólido
# Caixa "DATA PREVISTA DA ENTREGA" (alinhado à tela Pedidos Gerados)
C_PREVISTA_SEM_OK = colors.HexColor("#FFEBEE")   # vermelho claro — falta OK na obra
C_PREVISTA_COM_OK = colors.HexColor("#C8E6C9")  # verde claro — OK na obra confirmado
# Rodapé — instruções para o fornecedor (vermelho negrito, fundo igual ao resto do PDF)
C_RODAPE_TXT = colors.HexColor("#C0392B")
_RODAPE_ALT_MM = 24
_RODAPE_FONT_TITULO = 9.5
_RODAPE_FONT_TEXTO = 8.5
_HORARIO_RECEBIMENTO = (
    "Segunda a Quinta-feira das 07:30h às 11:30h e das 13:00h às 15:30h",
    "Sexta-feira das 07:30h às 11:30h e das 13:00h às 14:30h",
)
# Até 20 itens: tenta uma página com layout padrão (compressão leve se preciso).
# Acima de 20: pagina com ROW_H normal (~20 itens por folha de continuação).
_MAX_ITENS_FORCAR_UMA_PAGINA = 20
_ITENS_ALVO_POR_PAGINA = 20
_MARGEM_INFERIOR_TABELA = 2 * mm

# ── Diretório das logos ───────────────────────────────────────────────────────
_LOGOS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'logos')
)
_LOGO_NOMES = {
    "BRASUL":      "logo_brasul.png",
    "B&B":         "logo_bb.png",
    "INTERIORANA": "logo_interiorana.png",
    "INTERBRAS":   "logo_interbras.png",
}


def _logo_path(empresa: str):
    """Retorna o caminho da logo ou None se o arquivo não existir."""
    nome = _LOGO_NOMES.get(empresa, "")
    p    = os.path.join(_LOGOS_DIR, nome)
    return p if (nome and os.path.exists(p)) else None


_OBS_EMP_FONTE = "Helvetica-Bold"
_OBS_EMP_TAMANHO_PT = 7.5


def _montar_obs_empresa_pdf(obs_padrao: str) -> str:
    """
    Texto do bloco NOTA FISCAL: cabeçalho da empresa + regra de emissão na entrega.
    """
    cabecalho = [p.strip() for p in (obs_padrao or "").split("\n") if p.strip()]
    if cabecalho:
        return "\n".join(cabecalho) + "\n" + OBS_FATURAMENTO_DATA_ENTREGA
    return OBS_FATURAMENTO_DATA_ENTREGA


def _linhas_bloco_obs_empresa(c, texto: str, escala: float = 1.0) -> list[str]:
    """Quebra o texto do bloco NOTA FISCAL na largura útil do PDF."""
    if not (texto or "").strip():
        return []
    tamanho = max(7.0, _OBS_EMP_TAMANHO_PT * escala)
    largura = CW - 6 * mm
    linhas: list[str] = []
    for paragrafo in texto.split("\n"):
        p = paragrafo.strip()
        if not p:
            continue
        linhas.extend(
            PedidoCompraGenerator._quebrar_texto(c, p, largura, _OBS_EMP_FONTE, tamanho)
        )
    return linhas


def _medir_altura_bloco_obs_empresa(c, texto: str, escala: float = 1.0) -> float:
    """Altura exata do bloco conforme quebra de linha real (sem espaço vazio)."""
    linhas = _linhas_bloco_obs_empresa(c, texto, escala)
    if not linhas:
        return 0.0
    lh = 4.2 * mm
    pad = (4 * mm + 2.5 * mm) * escala
    return pad + len(linhas) * lh


def _montar_observacao(emp: dict, obs_usuario: str, material_solicitado: str = "") -> str:
    """
    Monta o texto do bloco de Observação (campo extra, abaixo dos itens).
    A obs_padrao da empresa vai para o bloco de faturamento (_bloco_fat).
    """
    partes = []
    sol = (material_solicitado or "").strip()
    if sol:
        partes.append(f"MATERIAL SOLICITADO POR: {sol.upper()}")
    obs = (obs_usuario or "").strip()
    if obs:
        partes.append(obs)
    return "\n".join(partes)


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
        emp = _resolver_empresa_faturadora(dto.empresa_faturadora)
        caminho = os.path.join(PEDIDOS_DIR, self._nome_arquivo(dto))
        c = rl_canvas.Canvas(caminho, pagesize=A4)
        self._gerar_paginas(c, dto, emp)
        c.save()
        copiar_arquivo_para_rede(caminho, "pdfs de pedidos")
        return caminho

    # ══════════════════════════════════════════════════════════════════════════
    # PAGINAÇÃO AUTOMÁTICA
    # Calcula quantos itens cabem por página e divide em fatias.
    # ══════════════════════════════════════════════════════════════════════════

    def _forma_pagamento_tem_pix(self, dto) -> bool:
        forma = str(getattr(dto, "forma_pagamento", "") or "").upper()
        cond = str(getattr(dto, "condicao_pagamento", "") or "").upper()
        return "PIX" in forma or "PIX" in cond

    def _medir_bloco_fornecedor(self, c, dto, escala: float) -> float:
        """Altura dinâmica do bloco fornecedor conforme tamanho da razão social."""
        col_w = CW * 0.5 - 6 * mm
        fs = max(7.0, 8.0 * escala)
        lh = 3.6 * mm
        label_h = 4.5 * mm

        razao = self._quebrar_texto(c, dto.fornecedor_razao, col_w, "Helvetica", fs)
        nome = self._quebrar_texto(c, dto.fornecedor_nome, col_w, "Helvetica", fs)
        linha1 = max(len(razao), len(nome), 1)

        cabecalho = 6 * mm * escala
        row1 = label_h + linha1 * lh
        row2 = label_h + lh
        padding = 3 * mm * escala
        return max(24 * mm * escala, cabecalho + row1 + row2 + padding)

    def _calc_blocos_layout(self, c, dto, obs_empresa_txt: str, obs_txt: str, escala: float) -> dict:
        e = escala
        ht = 28 * mm * e
        hdf = 7 * mm * e
        hf = self._medir_bloco_fornecedor(c, dto, e)
        hcob = 14 * mm * e
        hrod = max(_RODAPE_ALT_MM * mm, 26 * mm * e)
        tem_pix = self._forma_pagamento_tem_pix(dto)
        tem_chave = bool(str(getattr(dto, "fornecedor_pix", "") or "").strip())
        tem_fav = bool(str(getattr(dto, "fornecedor_favorecido", "") or "").strip())
        hfat = (22 * mm * e if (tem_pix and (tem_chave or tem_fav)) else 14 * mm * e)
        hent = 18 * mm * e
        hdr_h = max(5 * mm, 7 * mm * e)
        tot_h = max(14 * mm, 18 * mm * e)
        hobs_emp = _medir_altura_bloco_obs_empresa(c, obs_empresa_txt, e)
        hobs = 0
        if obs_txt:
            nl2 = max(1, (len(obs_txt) // 110) + obs_txt.count("\n") + 1)
            hobs = (8 * e + nl2 * 4.5 * e) * mm
        gap = 1 * mm
        cab_p1 = ht + hdf + hf + hcob + hfat + hobs_emp + hent + hobs + gap * 6
        cab_cont = ht + hdf + gap
        reserva_inf = hrod + _MARGEM_INFERIOR_TABELA + hdr_h + tot_h
        return dict(
            H_TOPO=ht, H_DATAFAIXA=hdf, H_FORN=hf, H_COB=hcob,
            H_ROD=hrod, H_FAT=hfat, H_ENT=hent, H_OBS_EMP=hobs_emp,
            H_OBS=hobs, HDR_H=hdr_h, TOT_H=tot_h,
            area_linhas_p1=max(20 * mm, H - M - cab_p1 - reserva_inf),
            area_linhas_cont=max(20 * mm, H - M - cab_cont - reserva_inf),
        )

    def _gerar_paginas(self, c, dto, emp):
        """
        Gera páginas com ajuste automático inteligente de escala.

        MODO PADRÃO (≤ 20 itens):
            Blocos normais, ROW_H = 6mm, fonte 7.5pt.
            Compressão leve só se a área útil não couber.

        MODO MULTI-PÁGINA (> 20 itens):
            Layout padrão; divide em páginas com até ~20 itens cada.
        """
        obs_padrao = (emp.get("obs_padrao") or "").strip()
        obs_empresa_txt = _montar_obs_empresa_pdf(obs_padrao)
        obs_txt    = _montar_observacao(
            emp, dto.observacao_extra, getattr(dto, "material_solicitado_por", "") or ""
        )
        n_itens    = len(dto.itens)

        def _calc_blocos(escala):
            """Calcula alturas de todos os blocos com fator de escala (1.0=normal, <1=compacto)."""
            e = escala
            ht      = 28*mm*e
            hdf     = 7*mm*e
            hf      = self._medir_bloco_fornecedor(c, dto, e)
            hcob    = 14*mm*e
            hrod    = max(_RODAPE_ALT_MM * mm, 26 * mm * e)
            forma_pix = self._forma_pagamento_tem_pix(dto)
            tem_pix = bool(str(getattr(dto, "fornecedor_pix", "")).strip())
            tem_fav = bool(str(getattr(dto, "fornecedor_favorecido", "")).strip())
            hfat    = (22*mm*e if (forma_pix and (tem_pix or tem_fav)) else 14*mm*e)
            hent    = 18*mm*e
            hdr_h   = max(5*mm, 7*mm*e)
            tot_h   = max(14*mm, 18*mm*e)

            hobs_emp = _medir_altura_bloco_obs_empresa(c, obs_empresa_txt, e)

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

        ROW_H_MIN = 4.0 * mm   # mínimo em página única (16–20 itens); legível na impressão
        paginar = n_itens > _MAX_ITENS_FORCAR_UMA_PAGINA

        if paginar:
            # Várias páginas: mantém layout padrão (não comprime para caber tudo numa folha).
            escala = 1.0
            ROW_H = 6 * mm
            b = _calc_blocos(escala)
        else:
            # Uma página (até 20 itens): tenta escala normal, depois compressão leve.
            b = _calc_blocos(1.0)
            linhas_normal = int(b["espaco"] / (6 * mm))

            if n_itens <= linhas_normal:
                escala = 1.0
                ROW_H = 6 * mm
            else:
                b85 = _calc_blocos(0.85)
                row_h_85 = b85["espaco"] / max(n_itens, 1)
                if row_h_85 >= ROW_H_MIN:
                    escala = 0.85
                    ROW_H = max(ROW_H_MIN, row_h_85)
                else:
                    escala = 0.80
                    b = _calc_blocos(0.80)
                    ROW_H = max(ROW_H_MIN, b["espaco"] / max(n_itens, 1))

            b = _calc_blocos(escala)

        # Fonte e cabeçalho da tabela escalam com ROW_H
        self._fonte_tabela = max(5.5, round(7.5 * (ROW_H / (6*mm)), 1))
        self._hdr_tabela   = max(4.5*mm, b["HDR_H"])

        itens = dto.itens
        col_desc_w = 84 * mm
        margem_desc = 2 * mm
        largura_desc = max(10, col_desc_w - (margem_desc * 2))
        line_h = max(self._fonte_tabela + 1, 6)
        row_padding = 4

        def _altura_item(item_desc):
            linhas = self._quebrar_texto(
                c, item_desc, largura_desc, "Helvetica", self._fonte_tabela
            )
            return max(ROW_H, row_padding + (len(linhas) * line_h))

        b_layout = self._calc_blocos_layout(c, dto, obs_empresa_txt, obs_txt, escala)

        def _recalc_alturas():
            nonlocal b_layout
            self._fonte_tabela = max(5.5, round(7.5 * (ROW_H / (6 * mm)), 1))
            self._hdr_tabela = max(4.5 * mm, b_layout["HDR_H"])
            lh = max(self._fonte_tabela + 1, 6)

            def _h(desc):
                n = self._quebrar_texto(
                    c, desc, largura_desc, "Helvetica", self._fonte_tabela
                )
                return max(ROW_H, row_padding + len(n) * lh)

            return [_h(getattr(it, "descricao", "")) for it in itens]

        alturas = _recalc_alturas()

        if n_itens <= _MAX_ITENS_FORCAR_UMA_PAGINA:
            for _ in range(40):
                total = sum(alturas)
                if total <= b_layout["area_linhas_p1"]:
                    break
                if ROW_H > ROW_H_MIN:
                    ROW_H = max(ROW_H_MIN, ROW_H * min(0.95, b_layout["area_linhas_p1"] / max(total, 1)))
                    alturas = _recalc_alturas()
                    continue
                if escala > 0.72:
                    escala = round(escala - 0.04, 2)
                    b_layout = self._calc_blocos_layout(c, dto, obs_empresa_txt, obs_txt, escala)
                    alturas = _recalc_alturas()
                    continue
                break
            fatias = [(itens, alturas)]
            b = b_layout
        else:
            fatias = []
            idx = 0
            while idx < n_itens:
                primeira_pag = not fatias
                cap = (
                    b_layout["area_linhas_p1"]
                    if primeira_pag
                    else b_layout["area_linhas_cont"]
                )
                limite_itens = _ITENS_ALVO_POR_PAGINA
                usados = 0.0
                itens_pag, alturas_pag = [], []
                while idx < n_itens:
                    h = alturas[idx]
                    if itens_pag and (
                        usados + h > cap or len(itens_pag) >= limite_itens
                    ):
                        break
                    itens_pag.append(itens[idx])
                    alturas_pag.append(h)
                    usados += h
                    idx += 1
                if not itens_pag:
                    itens_pag = [itens[idx]]
                    alturas_pag = [alturas[idx]]
                    idx += 1
                fatias.append((itens_pag, alturas_pag))
            b = b_layout

        offset = 0
        for pag_i, (fatia_itens, alturas_linhas) in enumerate(fatias):
            primeira = pag_i == 0
            ultima = pag_i == len(fatias) - 1
            self._desenhar_pagina(
                c, dto, emp, fatia_itens, alturas_linhas,
                primeira, ultima, pag_i + 1, len(fatias),
                b["H_TOPO"], b["H_DATAFAIXA"], b["H_FORN"], b["H_COB"],
                b["H_FAT"], b["H_OBS_EMP"], b["H_ENT"], b["H_OBS"], b["H_ROD"],
                self._hdr_tabela, ROW_H, b["TOT_H"],
                obs_txt, obs_empresa_txt,
                item_offset=offset,
            )
            offset += len(fatia_itens)
            if not ultima:
                c.showPage()

    def _desenhar_pagina(
        self, c, dto, emp, itens_pagina, alturas_linhas,
        primeira, ultima, num_pag, total_pag,
        H_TOPO, H_DATAFAIXA, H_FORN, H_COB,
        H_FAT, H_OBS_EMP, H_ENT, H_OBS, H_ROD,
        HDR_H, ROW_H, TOT_H, obs_txt, obs_empresa_txt,
        item_offset=0,
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

        if not primeira:
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(C_ESCURO)
            c.drawString(M + 3 * mm, y - 4 * mm, f"CONTINUAÇÃO — Pedido #{dto.numero}")
            y -= 6 * mm

        if primeira:
            y = self._bloco_forn(c, dto, y, H_FORN)
            y = self._bloco_cob(c, dto, emp, y, H_COB)
            y = self._bloco_fat(c, dto, emp, y, H_FAT)
            # Bloco separado para obs_padrao da empresa (quadrado próprio)
            if obs_empresa_txt:
                y = self._bloco_obs_empresa(c, obs_empresa_txt, y, H_OBS_EMP)
            y = self._bloco_ent(c, dto, y, H_ENT)
            if obs_txt:
                y = self._bloco_obs(c, obs_txt, y, H_OBS)

        self._tabela_itens(
            c, dto, itens_pagina, y, alturas_linhas,
            HDR_H, ROW_H, TOT_H,
            mostrar_totais=ultima,
            item_offset=item_offset,
        )
        self._rodape(c, dto.empresa_faturadora)

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 1 — Topo
    # ══════════════════════════════════════════════════════════════════════════

    def _bloco_topo(self, c, dto, emp, y, alt, num_pag=1, total_pag=1):
        """Logo + dados da empresa + número do pedido."""
        y0 = y - alt
        LOGO_W = 40 * mm
        LOGO_H = 20 * mm
        LOGO_PAD = 4 * mm
        sep_x = M + LOGO_W + 2 * LOGO_PAD

        c.setStrokeColor(C_LINHA)
        c.setLineWidth(0.8)
        c.rect(M, y0, CW, alt, fill=0, stroke=1)
        c.setLineWidth(0.5)
        c.line(sep_x, y0, sep_x, y)

        logo_fn = (emp.get("logo") or "").strip()
        logo = os.path.join(_LOGOS_DIR, logo_fn) if logo_fn else ""
        if not (logo and os.path.exists(logo)):
            logo = _logo_path(dto.empresa_faturadora) or ""

        if logo and os.path.exists(logo):
            try:
                logo_y = y0 + max(LOGO_PAD, (alt - LOGO_H) / 2)
                c.drawImage(
                    logo, M + LOGO_PAD, logo_y,
                    width=LOGO_W, height=LOGO_H,
                    preserveAspectRatio=True, mask="auto",
                )
            except Exception:
                c.setFont("Helvetica-Bold", 10)
                c.setFillColor(C_PRETO)
                c.drawString(M + LOGO_PAD, y0 + alt / 2 - 2, dto.empresa_faturadora)
        else:
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(C_PRETO)
            c.drawString(M + LOGO_PAD, y0 + alt / 2 - 2, dto.empresa_faturadora)

        cx = sep_x + 2 * mm
        c.setFont("Helvetica-Bold", 11); c.setFillColor(C_PRETO)
        c.drawString(cx, y-8*mm, emp["razao_social"])
        c.setFont("Helvetica", 7.5); c.setFillColor(C_ESCURO)
        c.drawString(cx, y-13*mm, emp["endereco"][:80])
        tel = str(emp.get("telefone") or "").strip()
        email_cab = _email_cabecalho_pdf(dto, emp)
        if email_cab:
            c.drawString(cx, y-17.5*mm, f"Tel: {tel}   |   {email_cab}")
        else:
            c.drawString(cx, y-17.5*mm, f"Tel: {tel}")
        cnpj = str(emp.get("cnpj", "") or "").strip()
        if cnpj:
            c.drawString(cx, y-22*mm, f"CNPJ: {cnpj}")

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
        Dados do fornecedor com quebra de linha automática (razão social longa).
        """
        c.setStrokeColor(C_LINHA)
        c.setLineWidth(0.8)
        c.rect(M, y - alt, CW, alt, fill=0, stroke=1)

        c.setFillColor(C_FUNDO)
        c.rect(M, y - 6 * mm, CW, 6 * mm, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(C_ESCURO)
        c.drawString(M + 3 * mm, y - 4.5 * mm, "FORNECEDOR")

        col2 = M + CW * 0.5
        col_w = CW * 0.5 - 6 * mm
        c.setStrokeColor(C_LINHA)
        c.setLineWidth(0.3)
        c.line(col2, y - 6 * mm, col2, y - alt)

        fs = 8
        lh = 3.6 * mm

        def desenhar_campo(label: str, valor, x: float, y_topo: float, largura: float):
            c.setFont("Helvetica-Bold", 6.5)
            c.setFillColor(C_MEDIO)
            c.drawString(x, y_topo, label.upper())
            linhas = self._quebrar_texto(c, valor, largura, "Helvetica", fs)
            c.setFont("Helvetica", fs)
            c.setFillColor(C_PRETO)
            yi = y_topo - 3.8 * mm
            for linha in linhas:
                c.drawString(x, yi, linha)
                yi -= lh
            return yi

        y_cursor = y - 8 * mm
        y_apos_razao = desenhar_campo(
            "Razão Social", dto.fornecedor_razao, M + 3 * mm, y_cursor, col_w
        )
        y_apos_nome = desenhar_campo(
            "Fornecedor", dto.fornecedor_nome, col2 + 3 * mm, y_cursor, col_w
        )
        y_linha2 = min(y_apos_razao, y_apos_nome) - 2 * mm

        desenhar_campo("E-mail", dto.fornecedor_email, M + 3 * mm, y_linha2, col_w)
        desenhar_campo("Vendedor", dto.fornecedor_vendedor, col2 + 3 * mm, y_linha2, 42 * mm)
        desenhar_campo(
            "Telefone", dto.fornecedor_telefone, col2 + 48 * mm, y_linha2, col_w - 48 * mm
        )

        return y - alt - 1 * mm

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 4 — Endereço de cobrança (CORRIGIDO)
    # ══════════════════════════════════════════════════════════════════════════

    def _bloco_cob(self, c, dto, emp, y, alt):
        """Endereço de cobrança — lê cidade/UF do config.py."""
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.8)
        c.rect(M, y-alt, CW, alt, fill=0, stroke=1)

        # Endereço de cobrança = endereço da empresa faturadora (config.py)
        end_cob_bruto = emp.get("endereco", "")
        cep_cob = emp.get("cep", "") or _cep_empresa(emp)

        # Extrai cidade e UF do config.py diretamente se disponível,
        # senão tenta parsear do campo endereco
        cidade = emp.get("cidade", "")
        uf     = emp.get("uf", "")
        if not cidade or not uf:
            cidade_p, uf_p = _cidade_uf_empresa(emp)
            if not cidade: cidade = cidade_p
            if not uf:     uf     = uf_p

        # Remove cidade repetida do fim do endereço de cobrança (ex.: «... – Piracicaba»),
        # pois a cidade já aparece na linha própria logo abaixo.
        end_cob = end_cob_bruto or ""
        if cidade:
            low_end = end_cob.lower()
            low_cid = str(cidade).strip().lower()
            idx = low_end.rfind(low_cid)
            if idx > 0:
                tail = low_end[idx + len(low_cid):].strip()
                if not tail or tail in (",", "-", "–"):
                    end_cob = end_cob[:idx].rstrip(" ,–-")

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
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.8)
        c.rect(M, y-alt, CW, alt, fill=0, stroke=1)

        cond  = str(dto.condicao_pagamento or "—").strip()
        forma = str(dto.forma_pagamento or "—").strip()
        cond_upper = cond.upper()
        cond_em_etapas = "%" in cond_upper or " NO ATO " in f" {cond_upper} "
        texto_faturamento = f"{cond}   {forma}" if cond_em_etapas else f"{cond} dias   {forma}"

        # Linha 1: Faturamento + Estimativa de vencimento
        c.setFont("Helvetica-Bold", 8); c.setFillColor(C_ESCURO)
        c.drawString(M+3*mm, y-5.5*mm, "Faturamento:")
        c.setFont("Helvetica-Bold", 9); c.setFillColor(C_PRETO)
        c.drawString(M+32*mm, y-5.5*mm, texto_faturamento)
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

        # Caixinha DATA PREVISTA: vermelho até OK na obra; verde só com flag explícita no banco.
        ok_caixa = int(getattr(dto, "material_ok_na_obra", 0) or 0) != 0
        c.setStrokeColor(C_LINHA)
        c.setFillColor(C_PREVISTA_COM_OK if ok_caixa else C_PREVISTA_SEM_OK)
        c.rect(W-M-28*mm, y-14*mm, 25*mm, 6.5*mm, fill=1, stroke=1)
        c.setFont("Helvetica-Bold", 10); c.setFillColor(C_PRETO)
        cx_data = W - M - 28*mm + 12.5*mm
        c.drawCentredString(cx_data, y-11*mm, dto.data_prevista_entrega)

        # Linha PIX dentro do bloco de faturamento (forma ou condição com PIX).
        if self._forma_pagamento_tem_pix(dto):
            pix = str(getattr(dto, "fornecedor_pix", "") or "").strip()
            favorecido = str(getattr(dto, "fornecedor_favorecido", "") or "").strip()

            if pix or favorecido:
                c.setStrokeColor(C_LINHA); c.setLineWidth(0.3)
                c.line(M+2*mm, y-15.5*mm, W-M-2*mm, y-15.5*mm)

                c.setFont("Helvetica-Bold", 7.5); c.setFillColor(C_ESCURO)
                c.drawString(M+3*mm, y-19.5*mm, "PIX:")
                c.setFont("Helvetica-Bold", 8); c.setFillColor(C_PRETO)
                c.drawString(M+15*mm, y-19.5*mm, pix[:75] if pix else "—")

                if favorecido:
                    c.setFont("Helvetica-Bold", 7.5); c.setFillColor(C_ESCURO)
                    c.drawString(M+105*mm, y-19.5*mm, "FAVORECIDO:")
                    c.setFont("Helvetica", 7.5); c.setFillColor(C_PRETO)
                    c.drawString(M+130*mm, y-19.5*mm, favorecido[:35])

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

        EXEMPLO de blocos de empresa:
            ┌─────────────────────────────────────────────────────┐
            │ NOTA FISCAL DEVE SER FATURADA EM NOME DA EMPRESA    │
            │ BRASUL CONSTRUTORA LTDA                              │
            │ OBS: CONTAR FATURAMENTO A PARTIR DO DIA 27/12/24... │
            └─────────────────────────────────────────────────────┘
        """
        # Fundo levemente amarelado para diferenciar dos outros blocos
        c.setFillColor(colors.HexColor("#FDFAF0"))
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.5)
        c.rect(M, y-alt, CW, alt, fill=1, stroke=1)

        tamanho = max(7.0, _OBS_EMP_TAMANHO_PT)
        lh = 4.2 * mm
        linhas = _linhas_bloco_obs_empresa(c, obs_padrao, escala=1.0)

        c.setFont(_OBS_EMP_FONTE, tamanho)
        c.setFillColor(C_PRETO)
        yi = y - 4 * mm
        for linha in linhas:
            c.drawString(M + 3 * mm, yi, linha)
            yi -= lh

        return y - alt - 1 * mm

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 6 — Local de entrega
    # ══════════════════════════════════════════════════════════════════════════

    def _bloco_ent(self, c, dto, y, alt):
        """Endereço de entrega (obra)."""
        c.setStrokeColor(C_LINHA); c.setLineWidth(0.8)
        c.rect(M, y-alt, CW, alt, fill=0, stroke=1)

        def par(lbl, val, x, yy, max_chars=44):
            c.setFont("Helvetica-Bold", 7.5); c.setFillColor(C_ESCURO)
            c.drawString(x, yy, lbl)
            c.setFont("Helvetica", 7.5); c.setFillColor(C_PRETO)
            off = c.stringWidth(lbl, "Helvetica-Bold", 7.5) + 2
            c.drawString(x+off, yy, str(val or "—")[:max_chars])

        # Distribui as 3 linhas proporcionalmente dentro do bloco
        l1 = y - alt * 0.22   # linha 1 — Endereço / Bairro
        l2 = y - alt * 0.55   # linha 2 — Obra / Contrato
        l3 = y - alt * 0.88   # linha 3 — CEP / Cidade / UF

        par("Local de Entrega:", dto.endereco_entrega, M+3*mm,    l1)
        par("Bairro:",           dto.bairro_entrega,   M+CW*0.5,  l1)
        par("OBRA:",             dto.obra_para_pdf.upper(), M+3*mm, l2, max_chars=58)
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

    def _tabela_itens(self, c, dto, itens_pagina, y, alturas_linhas,
                      HDR_H, ROW_H, TOT_H, mostrar_totais=True, item_offset=0):
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
        fnt = getattr(self, '_fonte_tabela', 8.0)

        # Cabeçalho da tabela
        c.setFillColor(C_HDR)
        c.rect(M, y-HDR_H, CW, HDR_H, fill=1, stroke=0)
        c.setFillColor(C_BRANCO); c.setFont("Helvetica-Bold", max(7, fnt-0.5))
        x = M
        for col in cols:
            if   col["a"] == "c": c.drawCentredString(x+col["w"]/2, y-HDR_H/2-2, col["h"])
            elif col["a"] == "r": c.drawRightString(x+col["w"]-2*mm, y-HDR_H/2-2, col["h"])
            else:                 c.drawString(x+2*mm, y-HDR_H/2-2, col["h"])
            x += col["w"]
        y -= HDR_H
        y_tab_topo = y

        for i, item in enumerate(itens_pagina):
            row_h_i = alturas_linhas[i] if i < len(alturas_linhas) else ROW_H
            if i % 2 == 0:
                c.setFillColor(colors.HexColor("#FAFAFA"))
                c.rect(M, y-row_h_i, CW, row_h_i, fill=1, stroke=0)
            c.setStrokeColor(C_LINHA); c.setLineWidth(0.5)
            c.line(M, y-row_h_i, M+CW, y-row_h_i)

            yt = y - row_h_i/2 - 2
            x  = M
            dados = [
                (str(item_offset + i + 1), "c", True),
                ("", "l", False),  # descrição tratada separadamente com quebra de linha
                (self._fmt_num(item.quantidade), "c", False),
                (item.unidade, "c", False),
                (self._fmt_val(item.valor_unitario), "r", False),
                (self._fmt_val(item.valor_total), "r", False),
            ]
            for j, (val, alg, bold) in enumerate(dados):
                w = cols[j]["w"]
                c.setFont("Helvetica-Bold" if bold else "Helvetica", fnt)
                c.setFillColor(C_PRETO)
                if j == 1:
                    margem_x = 2 * mm
                    largura_util = max(5, w - (margem_x * 2))
                    line_h = max(fnt + 1, 6)
                    linhas_desc = self._quebrar_texto(
                        c, item.descricao, largura_util, "Helvetica", fnt
                    )
                    y_desc = y - 2 - fnt
                    for ln in linhas_desc:
                        c.drawString(x + margem_x, y_desc, ln)
                        y_desc -= line_h
                elif alg == "c":
                    c.drawCentredString(x+w/2, yt, val)
                elif alg == "r":
                    c.drawRightString(x+w-2*mm, yt, val)
                else:
                    c.drawString(x+2*mm, yt, val)
                x += w
            y -= row_h_i

        # Borda externa e divisórias verticais
        c.setStrokeColor(C_LINHA); c.setLineWidth(1.0)
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
                c.setStrokeColor(C_LINHA); c.setLineWidth(0.8)
                c.rect(M+CW-larg_tot, y-6*mm, larg_tot, 6*mm, fill=0, stroke=1)
                y -= 6*mm

    # ══════════════════════════════════════════════════════════════════════════
    # BLOCO 9 — Rodapé fixo na base
    # ══════════════════════════════════════════════════════════════════════════

    def _desenhar_linhas_rodape(self, c, linhas, x, y, alinhamento="left", fonte=None, tamanho=None):
        """Desenha linhas do rodapé em vermelho negrito (quebra automática se for lista de str)."""
        fonte = fonte or "Helvetica-Bold"
        tamanho = tamanho or _RODAPE_FONT_TEXTO
        esp = 4.8 * mm
        c.setFont(fonte, tamanho)
        c.setFillColor(C_RODAPE_TXT)
        for txt in linhas:
            if not str(txt or "").strip():
                y -= esp * 0.6
                continue
            if alinhamento == "right":
                c.drawRightString(x, y, str(txt))
            else:
                c.drawString(x, y, str(txt))
            y -= esp
        return y

    def _rodape(self, c, empresa_faturadora):
        """Rodapé: fundo normal, texto em vermelho negrito (e-mails e horário de obra)."""
        y = 22 * mm
        c.setStrokeColor(C_LINHA)
        c.setLineWidth(0.5)
        c.line(M, y, W - M, y)

        emp = _resolver_empresa_faturadora(empresa_faturadora)
        meio = M + CW * 0.52
        col_esq = M
        col_dir = W - M
        lh_instr = 4.6 * mm

        instr = (
            "Destacar o endereço e o Nome da obra com o Nº de meu pedido "
            "no campo de Observações."
        )
        yi = y - 4.5 * mm
        c.setFont("Helvetica-Bold", _RODAPE_FONT_TEXTO)
        c.setFillColor(C_RODAPE_TXT)
        for linha in self._quebrar_texto(
            c, instr, meio - col_esq - 2 * mm, "Helvetica-Bold", _RODAPE_FONT_TEXTO
        ):
            c.drawString(col_esq, yi, linha)
            yi -= lh_instr

        y_emails = yi - 1 * mm
        c.setFont("Helvetica-Bold", _RODAPE_FONT_TITULO)
        c.setFillColor(C_RODAPE_TXT)
        c.drawString(col_esq, y_emails, "Notas e Boletos encaminha para:")

        e1 = str(emp.get("email_rodape_1") or "").strip() or "notafiscal@brasulconstrutora.com.br"
        e2 = str(emp.get("email_rodape_2") or "").strip() or "viviane@brasulconstrutora.com.br"
        self._desenhar_linhas_rodape(
            c, [e1, e2], col_esq, y_emails - 5 * mm, tamanho=_RODAPE_FONT_TEXTO
        )

        y_dir = y - 4.5 * mm
        c.setFont("Helvetica-Bold", _RODAPE_FONT_TITULO)
        c.setFillColor(C_RODAPE_TXT)
        c.drawRightString(col_dir, y_dir, "Horário de RECEBIMENTO NA OBRA")
        self._desenhar_linhas_rodape(
            c,
            list(_HORARIO_RECEBIMENTO),
            col_dir,
            y_dir - 5 * mm,
            alinhamento="right",
            tamanho=_RODAPE_FONT_TEXTO,
        )

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
    def _quebrar_texto(c, texto: str, largura_max: float, fonte: str, tamanho: float):
        """Quebra texto em múltiplas linhas respeitando a largura disponível."""
        txt = str(texto or "").strip()
        if not txt:
            return [""]

        palavras = txt.split()
        linhas, linha = [], ""

        for p in palavras:
            teste = (linha + " " + p).strip()
            if c.stringWidth(teste, fonte, tamanho) <= largura_max:
                linha = teste
                continue

            if linha:
                linhas.append(linha)
                linha = ""

            # Palavra maior que a célula: quebra por caractere.
            pedaco = ""
            for ch in p:
                t2 = pedaco + ch
                if c.stringWidth(t2, fonte, tamanho) <= largura_max:
                    pedaco = t2
                else:
                    if pedaco:
                        linhas.append(pedaco)
                    pedaco = ch
            linha = pedaco

        if linha:
            linhas.append(linha)
        return linhas or [""]

    @staticmethod
    def _nome_arquivo(dto: PedidoDTO) -> str:
        """Gera nome do arquivo: PC-2582-BRASUL-NOME_DA_OBRA.pdf"""
        obra = "".join(
            ch for ch in dto.obra_para_pdf if ch.isalnum() or ch in " _-"
        )[:28].strip().replace(" ", "_")
        return f"PC-{dto.numero}-{dto.empresa_faturadora}-{obra}.pdf"
