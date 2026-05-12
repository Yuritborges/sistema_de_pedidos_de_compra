import sys
from PySide6.QtWidgets import QApplication
from app.ui.main_window_patrao import MainWindowPatrao
from app.ui.qt_i18n import instalar_traducoes_qt_pt_br


def main():
    app = QApplication(sys.argv)
    instalar_traducoes_qt_pt_br(app)
    win = MainWindowPatrao()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()