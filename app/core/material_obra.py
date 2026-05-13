# Regra única para "OK na obra": só carimbo com data ISO + hora (como datetime('now') do SQLite).
# Não aceita DD/MM/AAAA sozinho — evita confundir com "data prevista" colada nesse campo.
import re

# Ex.: 2026-05-12 14:30:45 | 2026-05-12T14:30:45 | com fração de segundo opcional
_RE_CARIMBO_OK_OBRA = re.compile(
    r"^\d{4}-\d{2}-\d{2}[ T]\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?"
)


def material_entregue_obra_confirmado(val) -> bool:
    s = str(val or "").strip()
    if not s:
        return False
    return bool(_RE_CARIMBO_OK_OBRA.match(s))
