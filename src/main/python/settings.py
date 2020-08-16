from fbs_runtime.platform import is_mac
from PyQt5.QtWidgets import QWidget
from utils import isCudaCapable
from PyQt5 import uic


class SettingsWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        uic.loadUi(self.parent.appctxt.get_resource('settingswindow.ui'), self)
        self.setWindowTitle("Settings")
        self.populateSettings()

        self.parent.setEnabled(False)
        self.show()

    def populateSettings(self):
        self.numbaCbx.setChecked(self.parent.enableNumba)

        self.cudaCbx.setChecked(self.parent.enableCuda)
        self.cudaCbx.setEnabled(False)

        self.stereoCbx.setChecked(self.parent.enableStereo)
        self.stereoCbx.setEnabled(False)

        if self.parent.tau == 75e-6:
            self.deemp75Rdio.setChecked(True)
        else:
            self.deemp50Rdio.setChecked(True)

        # Apply System Specific Settings
        if isCudaCapable():
            self.cudaCbx.setEnabled(True)
        else:
            print("[SETTINGS] Can't find CUPY nor CUSIGNAL. Disabling CUDA support.")

        if is_mac():
            self.cudaCbx.setEnabled(False)  # macOS doesn't support CUDA 🤷

    def closeEvent(self, event):
        self.parent.enableCuda = self.cudaCbx.isChecked()
        self.parent.enableNumba = self.numbaCbx.isChecked()
        self.parent.stereoCbx = self.stereoCbx.isChecked()

        if self.deemp50Rdio.isChecked():
            self.parent.tau = 50e-6
        else:
            self.parent.tau = 75e-6

        self.parent.saveSettings()
        self.parent.loadSettings()
        self.parent.setEnabled(True)
