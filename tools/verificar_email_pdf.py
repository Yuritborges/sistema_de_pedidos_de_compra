# Verifica e-mail do rodapé em PDFs Interiorana (diagnóstico pós-release).
# Uso: python tools/verificar_email_pdf.py [caminho.pdf]

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _extrair_rodape(pdf: Path) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("Instale: pip install pypdf")
        sys.exit(1)
    text = ""
    for page in PdfReader(str(pdf)).pages:
        text += page.extract_text() or ""
    linhas = []
    for ln in text.splitlines():
        low = ln.lower()
        if "notafiscal@" in low or "notas e boletos" in low:
            linhas.append(ln.strip())
    return linhas


def main() -> None:
    if len(sys.argv) > 1:
        alvos = [Path(sys.argv[1])]
    else:
        pasta = ROOT.parent / "brasul_pedidos" / "Iury" / "pdfs de pedidos"
        if not pasta.is_dir():
            pasta = Path(r"Z:\0 OBRAS\brasul_pedidos\Iury\pdfs de pedidos")
        alvos = sorted(
            pasta.glob("PC-*-INTERIORANA-*.pdf"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:3]

    from app.infrastructure.pdf_generator import _emails_rodape_pdf

    print("Codigo atual INTERIORANA:", _emails_rodape_pdf({}, "INTERIORANA"))
    print()
    for pdf in alvos:
        if not pdf.is_file():
            print("NAO ENCONTRADO:", pdf)
            continue
        import datetime as dt

        mt = dt.datetime.fromtimestamp(pdf.stat().st_mtime)
        print(f"=== {pdf.name} ({mt:%Y-%m-%d %H:%M:%S}) ===")
        for ln in _extrair_rodape(pdf):
            print(" ", ln)
        print()


if __name__ == "__main__":
    main()
