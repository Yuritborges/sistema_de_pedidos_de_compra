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
text = text.replace('PASTA_COMPRADOR = "SuaPasta"', 'PASTA_COMPRADOR = "CI"')

# Caminhos locais — no GitHub Actions nao existe Z:\0 OBRAS\...
path_block = """
_CI_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ci_data")
os.makedirs(_CI_DATA, exist_ok=True)
DATABASE_PATH = os.path.join(_CI_DATA, "cotacao_ci.db")
BASE_REDE_DIR = _CI_DATA
PEDIDOS_DIR = os.path.join(_CI_DATA, "pedidos")
COTACOES_DIR = os.path.join(_CI_DATA, "cotacoes")
BACKUP_DIR = os.path.join(_CI_DATA, "backup")
RELACOES_DIR = os.path.join(_CI_DATA, "relacoes")
"""
text = re.sub(
    r"# Banco de trabalho do comprador.*?RELACOES_DIR = fr\".*?\"\n",
    path_block,
    text,
    flags=re.DOTALL,
)

# Remove makedirs em Z: (bloco original)
text = re.sub(
    r"\n# Cria as pastas necessárias automaticamente\nfor _pasta in \[.*?\]:\n    os\.makedirs\(_pasta, exist_ok=True\)\n",
    "\n",
    text,
    flags=re.DOTALL,
)

DST.write_text(text, encoding="utf-8")
print(f"[OK] {DST} (apenas para build CI)")
