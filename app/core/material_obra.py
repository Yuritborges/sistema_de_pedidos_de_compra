# Regra única para "OK na obra" no banco: só conta com carimbo de data reconhecível.
# Evita texto solto ("1", "SIM", "0") deixar a linha verde por engano.
import re

_RE_SQLITE_TS = re.compile(
    r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)?"
)
_RE_BR_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}")


def material_entregue_obra_confirmado(val) -> bool:
    s = str(val or "").strip()
    if not s:
        return False
    if _RE_SQLITE_TS.match(s):
        return True
    if _RE_BR_DATA.match(s):
        return True
    return False
