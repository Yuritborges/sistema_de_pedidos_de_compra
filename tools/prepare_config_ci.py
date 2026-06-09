# Gera config.py mínimo só para PyInstaller / CI (não usar em produção).
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "config_exemplo.py"
DST = ROOT / "config.py"

if not SRC.is_file():
    raise SystemExit(f"Nao encontrei {SRC}")

text = SRC.read_text(encoding="utf-8")
text = text.replace('COMPRADOR_PADRAO = "SEU_NOME"', 'COMPRADOR_PADRAO = "CI_BUILD"')

# Caminhos locais — no GitHub Actions não existe Z:\0 OBRAS\...
path_block = """
_CI_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ci_data")
os.makedirs(_CI_DATA, exist_ok=True)
BASE_REDE_DIR = _CI_DATA
_caminhos = caminhos_comprador(BASE_REDE_DIR, COMPRADOR_PADRAO)
DATABASE_PATH = _caminhos["DATABASE_PATH"]
PEDIDOS_DIR = _caminhos["PEDIDOS_DIR"]
COTACOES_DIR = _caminhos["COTACOES_DIR"]
BACKUP_DIR = _caminhos["BACKUP_DIR"]
RELACOES_DIR = _caminhos["RELACOES_DIR"]
"""
text = re.sub(
    r"BASE_REDE_DIR = DEFAULT_BASE_REDE_DIR\n\nCOMPRADOR_PADRAO = normalizar_usuario\(COMPRADOR_PADRAO\).*?"
    r'RELACOES_DIR = _caminhos\["RELACOES_DIR"\]\n',
    f'COMPRADOR_PADRAO = normalizar_usuario(COMPRADOR_PADRAO)\n\n{path_block}',
    text,
    flags=re.DOTALL,
    count=1,
)

# Remove validação de SEU_NOME (CI usa CI_BUILD)
text = text.replace('COMPRADOR_PADRAO == "SEU_NOME"', 'False')

# Remove makedirs em pastas de rede (bloco original)
text = re.sub(
    r"\n# Cria as pastas necessárias automaticamente\nfor _pasta in .*?\n    os\.makedirs\(_pasta, exist_ok=True\)\n",
    "\n",
    text,
    flags=re.DOTALL,
)

DST.write_text(text, encoding="utf-8")
print(f"[OK] {DST} (apenas para build CI)")
