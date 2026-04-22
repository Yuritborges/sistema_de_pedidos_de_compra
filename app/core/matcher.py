"""
app/core/matcher.py
===================
Motor de matching semântico para cruzamento de itens entre orçamentos.

Funciona em 4 etapas:
  1. Normalização  — remove ruído, padroniza unidades, remove marcas
  2. Extração      — converte descrição em atributos estruturados
  3. Chave canônica — representação única e comparável do produto
  4. Score         — pontuação por atributos com pesos definidos

Classificação final:
  MATCH_EXATO      (score >= 85) → aceita automaticamente   🟢
  MATCH_PROVAVEL   (score >= 50) → sugere, usuário confirma 🟡
  REVISAO_MANUAL   (score <  50) → marca 🔴, usuário decide
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# DICIONÁRIO DE SINÔNIMOS — extensível via JSON externo futuramente
# ══════════════════════════════════════════════════════════════════════════════

SINONIMOS: dict[str, str] = {
    # Características de tinta/acabamento
    "ANTIRRESPINGO":   "ANTIRRESPINGO",
    "ZERO RESPINGO":   "ANTIRRESPINGO",
    "ANTI RESPINGO":   "ANTIRRESPINGO",
    "BRI":             "BRILHO",
    "BRILHANTE":       "BRILHO",
    "ESM SINT":        "ESMALTE SINTETICO",
    "ESM":             "ESMALTE",
    "SINT":            "SINTETICO",
    "ACRILICA":        "ACRILICO",
    "LATEX":           "ACRILICO",
    "PVA":             "ACRILICO",
    "CARNEIRO":        "LA CARNEIRO",
    # Conectivos / preposições
    "C/CABO":          "COM CABO",
    "C/ CABO":         "COM CABO",
    "P/":              "PARA",
    "S/":              "SEM",
    "C/":              "COM",
    # Embalagem / tamanho
    "BD":              "BALDE",
    "BALDE":           "BALDE",
    "GL":              "GALAO",
    "GALAO":           "GALAO",
    "LT":              "LATA",
    "LATA":            "LATA",
    # Cores comuns
    "BRANCO":          "BRANCO",
    "GELO":            "GELO",
    "GRAFITE":         "GRAFITE",
    "PRETO":           "PRETO",
}

# Marcas a remover (não identificam o produto)
MARCAS: set[str] = {
    "TIGRE", "FUTURA", "ADERE", "ITAQUA", "CORANTE", "OZ", "TRAMONTINA",
    "FENIX", "ROMA", "FORTLEV", "WALE", "CEMAR", "BALDI", "STANDARD",
    "PROCOLOR", "CORAL", "SUVINIL", "ATLAS", "KILLING", "LUKSCOLOR",
    "KRONA", "AMANCO", "BRASILIT", "ETERNIT", "VOTORANTIM", "VOTOMASSA",
    "QUARTZOLIT", "WEBER", "PREDIAL", "CISER", "TEKBOND", "HENKEL",
    "OTTO", "LUMINEX", "PHILIPS", "OSRAM", "INTRAL", "STECK", "ALUMBRA",
}

# Termos de embalagem / marketing a remover
RUIDO: set[str] = {
    "ECON", "ECONOMICO", "MEGA", "SUPER", "PLUS", "MAX", "PRO",
    "STANDARD", "PREMIUM", "ESPECIAL", "EXTRA", "TOP", "MASTER",
    "EMB", "EMBALAGEM", "REFORCADO", "REFOR", "ZERO", "NOVO",
    "ORIGINAL", "CANARINHO", "BUILDING", "SUPERWASH",
}

# Tipos de produto canônicos (normaliza variações para um nome padrão)
TIPOS: dict[str, str] = {
    "ROLO":        "ROLO",
    "ROLETE":      "ROLO",
    "TRINCHA":     "TRINCHA",
    "PINCEL":      "TRINCHA",
    "FITA":        "FITA",
    "CREPE":       "FITA CREPE",
    "FITA CREPE":  "FITA CREPE",
    "SUPORTE":     "SUPORTE",
    "EXTENSOR":    "EXTENSOR",
    "CABO":        "CABO",
    "MASSA":       "MASSA",
    "ESMALTE":     "ESMALTE",
    "TINTA":       "TINTA",
    "SELADOR":     "SELADOR",
    "PRIMER":      "PRIMER",
    "AGUARRAS":    "AGUARRAS",
    "SOLVENTE":    "AGUARRAS",
    "THINNER":     "AGUARRAS",
    "LIXA":        "LIXA",
    "ESPUMA":      "ROLO ESPUMA",
    "ROLO ESPUMA": "ROLO ESPUMA",
}

# Limiar de score para classificação
LIMIAR_EXATO    = 75   # >= 75 → aceita automaticamente 🟢
LIMIAR_PROVAVEL = 45   # >= 45 → sugere, usuário confirma 🟡
                       # <  45 → marca 🔴, usuário decide


# ══════════════════════════════════════════════════════════════════════════════
# MODELOS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class AtributosProduto:
    tipo:        Optional[str] = None   # ROLO, TRINCHA, FITA CREPE …
    medida:      Optional[str] = None   # 23CM, 24MM, 2.5POL …
    medida2:     Optional[str] = None   # segunda dimensão: 50M em 24MMx50M
    volume:      Optional[str] = None   # 3.6L, 18L …
    peso:        Optional[str] = None   # 25KG, 5KG …
    caracteristica: Optional[str] = None  # ZERO RESPINGO, BRILHO, FOSCO …
    cor:         Optional[str] = None   # BRANCO, GELO, GRAFITE …
    desc_norm:   str = ""               # descrição normalizada completa
    tokens:      set  = field(default_factory=set)  # tokens após limpeza

    @property
    def chave_canonica(self) -> str:
        """Gera chave canônica: TIPO|MEDIDA|CARACT|COR|VOLUME|PESO"""
        partes = [p for p in [
            self.tipo,
            self.medida,
            self.medida2,
            self.caracteristica,
            self.cor,
            self.volume,
            self.peso,
        ] if p]
        return "|".join(partes)


@dataclass
class ResultadoMatch:
    score:       int            # 0–100
    classificacao: str          # MATCH_EXATO | MATCH_PROVAVEL | REVISAO_MANUAL
    motivo:      str            # explicação legível
    atributos_a: AtributosProduto
    atributos_b: AtributosProduto


# ══════════════════════════════════════════════════════════════════════════════
# 1. NORMALIZAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

def remover_acentos(txt: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", txt)
        if unicodedata.category(c) != "Mn"
    )


def normalizar(txt: str) -> str:
    """
    Retorna descrição limpa, maiúscula, sem acentos, sem marcas, com
    unidades padronizadas.
    """
    txt = remover_acentos(txt.upper())

    # Padroniza separadores de medida compostas: 24X50M → 24 X 50 M
    txt = re.sub(r"(\d+)\s*[Xx]\s*(\d+)", r"\1 X \2", txt)

    # Padroniza virgula decimal: 3,6L → 3.6L
    txt = re.sub(r"(\d+),(\d+)", r"\1.\2", txt)

    # Separa número de unidade: 24MM → 24 MM / 50M → 50 M
    txt = re.sub(r"(\d+\.?\d*)\s*(MM|CM|MT?|KG|G\b|ML|LT?|GL|LA\b|POL)", r"\1 \2", txt)

    # Padroniza fração: 2.1/2 → 2 1/2
    txt = re.sub(r"(\d+)\.(\d+/\d+)", r"\1 \2", txt)

    # Remove caracteres especiais (mantém letras, números, espaço, / .)
    txt = re.sub(r"[^A-Z0-9\s/.]", " ", txt)

    # Remove marcas
    for marca in MARCAS:
        txt = re.sub(rf"\b{re.escape(marca)}\b", " ", txt)

    # Remove ruídos de marketing/embalagem
    for ruido in RUIDO:
        txt = re.sub(rf"\b{re.escape(ruido)}\b", " ", txt)

    # Remove códigos de produto: sequências alfanuméricas sem sentido
    txt = re.sub(r"\b[A-Z]{2,}\d+[A-Z0-9/]*\b", " ", txt)  # ex: NCM, SKU
    txt = re.sub(r"\b\d{4,8}\b", " ", txt)                   # ex: 96034090

    # Aplica sinônimos (garante normalização semântica)
    for sinonimo, canonical in SINONIMOS.items():
        txt = re.sub(rf"\b{re.escape(sinonimo)}\b", canonical, txt)

    return re.sub(r"\s+", " ", txt).strip()


# ══════════════════════════════════════════════════════════════════════════════
# 2. EXTRAÇÃO DE ATRIBUTOS
# ══════════════════════════════════════════════════════════════════════════════

_PAT_MEDIDA   = re.compile(r"\b(\d+\.?\d*)\s*(MM|CM|POL|POLEGADA)\b")
_PAT_MEDIDA_X = re.compile(r"\b(\d+)\s*X\s*\d")  # 24 X 50M → extrai 24 como medida em MM
_PAT_COMPRIMENTO = re.compile(r"\b(\d+\.?\d*)\s*(M\b|MT\b|ML\b)\b")
_PAT_VOLUME   = re.compile(r"\b(\d+\.?\d*)\s*(L\b|LT\b|GL\b|LITRO)\b")
_PAT_PESO     = re.compile(r"\b(\d+\.?\d*)\s*(KG|G\b|GRAMA)\b")
_PAT_FRACAO   = re.compile(r"\b(\d+\s*\d+/\d+)\b")  # ex: 2 1/2


def extrair_atributos(desc_original: str) -> AtributosProduto:
    """Converte descrição em estrutura de atributos."""
    norm = normalizar(desc_original)
    tokens = set(t for t in norm.split() if len(t) > 1)
    attr = AtributosProduto(desc_norm=norm, tokens=tokens)

    # Tipo do produto
    for token, tipo_canonical in TIPOS.items():
        if token in norm:
            attr.tipo = tipo_canonical
            break

    # Medidas
    m = _PAT_MEDIDA.search(norm)
    if m:
        attr.medida = f"{m.group(1)}{m.group(2)}"
    elif _PAT_MEDIDA_X.search(norm):
        # ex: "24 X 50 M" — primeiro número é a largura em MM
        mx = _PAT_MEDIDA_X.search(norm)
        attr.medida = f"{mx.group(1)}MM"

    # Fração de polegada (ex: 2 1/2)
    mf = _PAT_FRACAO.search(norm)
    if mf and not attr.medida:
        attr.medida = mf.group(1).replace(" ", "") + "POL"

    # Comprimento (50M em fita 24MMx50M)
    mc = _PAT_COMPRIMENTO.search(norm)
    if mc:
        attr.medida2 = f"{mc.group(1)}{mc.group(2).rstrip()}"

    # Volume
    mv = _PAT_VOLUME.search(norm)
    if mv:
        attr.volume = f"{mv.group(1)}L"

    # Peso
    mp = _PAT_PESO.search(norm)
    if mp:
        attr.peso = f"{mp.group(1)}KG"

    # Característica
    for caract in ["ANTIRRESPINGO", "BRILHO", "FOSCO", "ACETINADO",
                   "METALICO", "TEXTURAS", "ACRILICO", "SINTETICO",
                   "LATEX", "LA CARNEIRO", "COM CABO"]:
        if caract in norm:
            attr.caracteristica = caract
            break

    # Cor
    for cor in ["BRANCO", "GELO", "GRAFITE", "PRETO", "VERMELHO",
                "AZUL", "VERDE", "AMARELO", "CINZA", "MARROM",
                "PALHA", "CREME", "BEGE", "CORAL"]:
        if cor in norm:
            attr.cor = cor
            break

    return attr


# ══════════════════════════════════════════════════════════════════════════════
# 3. MOTOR DE MATCHING
# ══════════════════════════════════════════════════════════════════════════════

def _score_atributos(a: AtributosProduto, b: AtributosProduto) -> tuple[int, list[str]]:
    """
    Calcula score 0–100 comparando atributos extraídos.
    Retorna (score, lista_de_motivos).

    Pesos:
      tipo         → 35 pts  (produto completamente diferente se divergir)
      medida       → 30 pts  (23CM ≠ 9CM = produto diferente)
      volume/peso  → 15 pts
      característica → 10 pts
      cor          → 10 pts
    """
    score  = 0
    motivos = []

    # ── Tipo ─────────────────────────────────────────────────────────────────
    if a.tipo and b.tipo:
        if a.tipo == b.tipo:
            score += 35
            motivos.append(f"tipo={a.tipo}")
        else:
            # Tipos completamente diferentes → impossível ser o mesmo produto
            return 0, [f"tipo diferente: {a.tipo} ≠ {b.tipo}"]
    elif a.tipo or b.tipo:
        # Um tem tipo, outro não — partial
        score += 15
        motivos.append("tipo parcial")

    # ── Medida principal ──────────────────────────────────────────────────────
    if a.medida and b.medida:
        if a.medida == b.medida:
            score += 30
            motivos.append(f"medida={a.medida}")
        else:
            # Medidas diferentes → produto diferente (ex: ROLO 9CM ≠ ROLO 23CM)
            score -= 20
            motivos.append(f"medida diferente: {a.medida} ≠ {b.medida}")
    elif a.medida or b.medida:
        score += 10
        motivos.append("medida parcial")

    # ── Volume / Peso ─────────────────────────────────────────────────────────
    vol_a = a.volume or a.peso
    vol_b = b.volume or b.peso
    if vol_a and vol_b:
        if vol_a == vol_b:
            score += 15
            motivos.append(f"volume={vol_a}")
        else:
            score -= 15
            motivos.append(f"volume diferente: {vol_a} ≠ {vol_b}")
    elif vol_a or vol_b:
        score += 5
        motivos.append("volume parcial")

    # ── Característica ────────────────────────────────────────────────────────
    if a.caracteristica and b.caracteristica:
        if a.caracteristica == b.caracteristica:
            score += 10
            motivos.append(f"caract={a.caracteristica}")
        else:
            score -= 5
            motivos.append(f"caract diferente: {a.caracteristica} ≠ {b.caracteristica}")

    # ── Cor ───────────────────────────────────────────────────────────────────
    if a.cor and b.cor:
        if a.cor == b.cor:
            score += 10
            motivos.append(f"cor={a.cor}")
        else:
            score -= 10
            motivos.append(f"cor diferente: {a.cor} ≠ {b.cor}")

    # ── Fallback: Jaccard sobre tokens normalizados ───────────────────────────
    # Complementa quando atributos são rasos (ex: "AGUARRAS 5L" vs "AGUARRAS 5L")
    if a.tokens and b.tokens:
        inter  = len(a.tokens & b.tokens)
        union  = len(a.tokens | b.tokens)
        jacc   = inter / union if union else 0
        bonus  = round(jacc * 20)  # até +20 pts de bônus
        score += bonus
        if bonus >= 10:
            motivos.append(f"tokens similares ({bonus}pts)")

    return max(0, min(100, score)), motivos


def comparar(desc_a: str, desc_b: str,
             qtd_a: float = 1.0, qtd_b: float = 1.0) -> ResultadoMatch:
    """
    Compara duas descrições e retorna ResultadoMatch com score e classificação.
    """
    attr_a = extrair_atributos(desc_a)
    attr_b = extrair_atributos(desc_b)

    score, motivos = _score_atributos(attr_a, attr_b)

    # Penalidade leve por quantidade diferente
    if qtd_a and qtd_b and abs(qtd_a - qtd_b) > max(qtd_a * 0.05, 0.5):
        score = int(score * 0.85)
        motivos.append(f"qtd diferente: {qtd_a} ≠ {qtd_b}")

    if score >= LIMIAR_EXATO:
        classificacao = "MATCH_EXATO"
    elif score >= LIMIAR_PROVAVEL:
        classificacao = "MATCH_PROVAVEL"
    else:
        classificacao = "REVISAO_MANUAL"

    return ResultadoMatch(
        score=score,
        classificacao=classificacao,
        motivo=", ".join(motivos) if motivos else "sem atributos em comum",
        atributos_a=attr_a,
        atributos_b=attr_b,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 4. CRUZAMENTO DE LISTAS (usado pelo PDFCruzamentoDialog)
# ══════════════════════════════════════════════════════════════════════════════

def cruzar_listas(
    itens_pdf:    list[dict],       # [{"descricao":..., "quantidade":..., "preco_unitario":...}]
    itens_tabela: list,             # [ItemCotacao]
) -> list[dict]:
    """
    Cruza itens do PDF com itens da tabela usando o motor semântico.

    Retorna lista de pares no mesmo formato esperado pelo PDFCruzamentoDialog:
    {
        "tipo":       "par" | "novo",
        "score":      int,
        "classificacao": "MATCH_EXATO" | "MATCH_PROVAVEL" | "REVISAO_MANUAL",
        "motivo":     str,
        "idx_tabela": int,
        "desc_tab":   str,
        "qtd_tab":    float,
        "item_pdf":   dict,
    }
    """
    pares  = []
    usados = set()

    for it_pdf in itens_pdf:
        desc_pdf = it_pdf.get("descricao", "")
        qtd_pdf  = float(it_pdf.get("quantidade") or 1)

        melhor_score  = -1
        melhor_idx    = -1
        melhor_result = None

        for idx, it_tab in enumerate(itens_tabela):
            if idx in usados:
                continue
            if not it_tab.descricao.strip():
                continue

            result = comparar(it_tab.descricao, desc_pdf,
                              it_tab.quantidade, qtd_pdf)

            if result.score > melhor_score:
                melhor_score  = result.score
                melhor_idx    = idx
                melhor_result = result

        # Aceita qualquer match com score >= 25 (REVISAO_MANUAL inclusive)
        # O usuário vai ver o 🔴 e decidir
        if melhor_idx >= 0 and melhor_score >= 25:
            usados.add(melhor_idx)
            pares.append({
                "tipo":          "par",
                "score":         melhor_score,
                "classificacao": melhor_result.classificacao,
                "motivo":        melhor_result.motivo,
                "idx_tabela":    melhor_idx,
                "desc_tab":      itens_tabela[melhor_idx].descricao,
                "qtd_tab":       itens_tabela[melhor_idx].quantidade,
                "item_pdf":      it_pdf,
            })
        else:
            pares.append({
                "tipo":          "novo",
                "score":         melhor_score if melhor_score >= 0 else 0,
                "classificacao": "REVISAO_MANUAL",
                "motivo":        "sem correspondência encontrada",
                "idx_tabela":    -1,
                "desc_tab":      "",
                "qtd_tab":       qtd_pdf,
                "item_pdf":      it_pdf,
            })

    return pares


# ══════════════════════════════════════════════════════════════════════════════
# TESTES RÁPIDOS (python matcher.py)
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pares_teste = [
        ("FITA CREPE 24MM X 50M ADERE",          "ADERE FITA CREPE 24X50M"),
        ("ROLO 23CM LA ANTIRRESPINGO",            "ROLO LA ZERO RESPINGO 23CM"),
        ("SUPORTE PARA ROLO 23CM",                "SUPORTE DE PRESSAO REFORCADO P/ ROLO 23CM"),
        ("FUTURIT ESMALTE BRI GELO 3,6L",         "FUTURIT ESM SINT.BRILHO GELO 3,6L"),
        ("TRINCHA 500 - 1 LATEX ACRILICA",        "TRINCHA 500 - 1"),
        ("ROLO 23CM LA CARNEIRO",                 "ROLO 23CM LA ANTIRRESPINGO"),   # deve ser baixo
        ("MASSA CORRIDA 25KG BALDE",              "MASSA CORRIDA 25KG"),
        ("AGUARRAS 5L",                           "AGUARRAS 5L ITAQUA"),
        ("TINTA GRAFITE ESCURO 3.6L",             "TINTA GRAFITE 3,6L BRILHO"),    # cor igual, caract dif
    ]

    print(f"\n{'DESCRIÇÃO A':<45} {'DESCRIÇÃO B':<45} {'SCORE':>6}  CLASSI")
    print("─" * 110)
    for a, b in pares_teste:
        r = comparar(a, b)
        icone = "🟢" if r.classificacao == "MATCH_EXATO" else (
                "🟡" if r.classificacao == "MATCH_PROVAVEL" else "🔴")
        print(f"{a:<45} {b:<45} {r.score:>5}%  {icone} {r.classificacao}")
        print(f"   ↳ {r.motivo}")
        print(f"   ↳ chave A: {r.atributos_a.chave_canonica}")
        print(f"   ↳ chave B: {r.atributos_b.chave_canonica}")
        print()
