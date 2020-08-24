import os
from fbs_runtime.platform import is_mac
from PyQt5.QtWidgets import QWidget
from utils import isCudaCapable
from PyQt5 import uic
from elevate import elevate


class SettingsWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        uic.loadUi(self.parent.appctxt.get_resource('settingswindow.ui'), self)
        self.setWindowTitle("Settings")
        self.populateSettings()

        self.installUdevBtn.clicked.connect(self.handleUdev)

        self.parent.setEnabled(False)
        self.show()

    def handleUdev(self):
        cmd = "uname -a"

        if os.getuid() != 0:
            cmd = "pkexec " + cmd

        print(os.system(cmd))

    def populateSettings(self):
        self.cudaCbx.setChecked(self.parent.enableCuda)
        self.cudaCbx.setEnabled(False)

        self.stereoCbx.setChecked(self.parent.enableStereo)
        self.stereoCbx.setEnabled(False)

        self.bufferMult.setValue(self.parent.buffer_mult)

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
        self.parent.stereoCbx = self.stereoCbx.isChecked()
        self.parent.buffer_mult = self.bufferMult.value()

        if self.deemp50Rdio.isChecked():
            self.parent.tau = 50e-6
        else:
            self.parent.tau = 75e-6

        self.parent.saveSettings()
        self.parent.loadSettings()
        self.parent.setEnabled(True)
