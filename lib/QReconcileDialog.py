from __future__ import annotations

from qtpy import QtCore, QtWidgets


class QReconcileDialog(QtWidgets.QDialog):
    '''Modal dialog for resolving mismatches between hardware and saved
    settings.

    Presents a table of properties whose hardware value differs from the
    value stored in the configuration file, and asks the user to choose
    which source should be authoritative.

    Parameters
    ----------
    hw : dict
        Property values read directly from the hardware.
    saved : dict
        Property values read from the configuration file.
    diff_keys : list[str]
        Keys present in both *hw* and *saved* whose values differ.
    hardware_dominant : bool
        When ``True``, "Keep Hardware" is the default button.
        Default: ``False`` ("Use Saved" is the default).
    parent : QWidget or None
        Parent widget.  Default: ``None``.

    Attributes
    ----------
    keep_hardware : bool
        ``True`` if the user chose "Keep Hardware" or dismissed the dialog.
        ``False`` if the user chose "Use Saved".
    '''

    def __init__(self,
                 hw: dict,
                 saved: dict,
                 diff_keys: list[str],
                 hardware_dominant: bool = False,
                 parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Configuration Mismatch')
        self._choice = 'hardware'

        layout = QtWidgets.QVBoxLayout(self)

        label = QtWidgets.QLabel(
            'The saved configuration differs from the current hardware '
            'settings.\nWhich values should be used?'
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        table = QtWidgets.QTableWidget(len(diff_keys), 3, self)
        table.setHorizontalHeaderLabels(['Property', 'Hardware', 'Saved'])
        table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        for row, key in enumerate(diff_keys):
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(key))
            table.setItem(row, 1,
                          QtWidgets.QTableWidgetItem(str(hw.get(key, ''))))
            table.setItem(row, 2,
                          QtWidgets.QTableWidgetItem(str(saved.get(key, ''))))
        table.resizeColumnsToContents()
        layout.addWidget(table)

        btn_layout = QtWidgets.QHBoxLayout()
        hw_btn = QtWidgets.QPushButton('Keep Hardware')
        saved_btn = QtWidgets.QPushButton('Use Saved')
        hw_btn.clicked.connect(self._keep_hardware)
        saved_btn.clicked.connect(self._use_saved)
        if hardware_dominant:
            hw_btn.setDefault(True)
            hw_btn.setFocus()
        else:
            saved_btn.setDefault(True)
            saved_btn.setFocus()
        btn_layout.addWidget(hw_btn)
        btn_layout.addWidget(saved_btn)
        layout.addLayout(btn_layout)

    @property
    def keep_hardware(self) -> bool:
        '''bool: ``True`` if "Keep Hardware" was chosen or the dialog
        was dismissed.'''
        return self._choice == 'hardware'

    @QtCore.Slot()
    def _keep_hardware(self) -> None:
        self._choice = 'hardware'
        self.accept()

    @QtCore.Slot()
    def _use_saved(self) -> None:
        self._choice = 'saved'
        self.accept()


__all__ = ['QReconcileDialog']
