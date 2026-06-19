# app/ui/combo_sem_roda.py
# QComboBox que ignora a roda do mouse (evita trocar item ao rolar a página).

from PySide6.QtWidgets import QComboBox


class ComboSemRoda(QComboBox):
    def wheelEvent(self, event):
        event.ignore()
