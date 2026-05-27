# Gera config.py mínimo só para PyInstaller / CI (não usar em produção).
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "config_exemplo.py"
DST = ROOT / "config.py"

if not SRC.is_file():
    raise SystemExit(f"Nao encontrei {SRC}")

text = SRC.read_text(encoding="utf-8")
text = text.replace('COMPRADOR_PADRAO = "SEU_NOME"', 'COMPRADOR_PADRAO = "CI_BUILD"')
text = text.replace('PASTA_COMPRADOR = "SuaPasta"', 'PASTA_COMPRADOR = "CI"')
DST.write_text(text, encoding="utf-8")
print(f"[OK] {DST} (apenas para build CI)")
