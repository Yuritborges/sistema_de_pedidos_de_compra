# Traduções Qt pt_BR — botões padrão de QMessageBox (Sim/Não/Cancelar/OK).

import os
import sys


def instalar_traducoes_qt_pt_br(app) -> None:
    """
    Carrega qtbase_pt_BR / qt_pt_BR (pastas do PySide6 no dev; no .exe, em PySide6/translations).
    """
    try:
        from PySide6.QtCore import QLocale, QLibraryInfo, QTranslator

        QLocale.setDefault(QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil))

        paths = []
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            paths.append(os.path.join(sys._MEIPASS, "PySide6", "translations"))
        try:
            paths.append(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
        except Exception:
            pass

        for base in ("qtbase", "qt"):
            tr = QTranslator()
            for path in paths:
                if path and os.path.isdir(path):
                    if tr.load(f"{base}_pt_BR", path):
                        app.installTranslator(tr)
                        break
    except Exception:
        pass
