from fbs_runtime.application_context.PyQt5 import ApplicationContext
from fbs_runtime.platform import is_mac
from PyQt5.QtWidgets import QApplication, QMainWindow, QErrorMessage
from PyQt5.QtCore import QTimer, Qt, QThread, QSettings
from PyQt5.QtGui import QFontDatabase
from PyQt5 import uic
from demod import Demodulator
from styles import volumeStyle, comboStyle, modBtnDisabled, modBtnEnabled
from utils import parseSaveStr, getDeviceList, defaultFavorites
from settings import SettingsWindow
import numpy as np
import sys


class MainWindow(QMainWindow):

    def __init__(self, appctxt):
        super(MainWindow, self).__init__()
        self.appctxt = appctxt

        # Load Path from Resources
        self.mainwindow = self.appctxt.get_resource('mainwindow.ui')
        self.cursednet = self.appctxt.get_resource('cursednet.pth')

        # Load Window UI
        uic.loadUi(self.mainwindow, self)

        # Load Settings
        self.loadSettings()

        # Routine State
        self.running = False

        # Display Update Timer
        self.displayTimer = QTimer(self)
        self.displayTimer.setInterval(500)
        self.displayTimer.timeout.connect(self.updateDisplay)

        # Devices Update Timer
        self.deviceCheckTimer = QTimer(self)
        self.deviceCheckTimer.setInterval(1000)
        self.deviceCheckTimer.timeout.connect(self.updateDevices)
        self.deviceCheckTimer.start()
        self.updateDevices()

        # Activate First Device
        self.handleDevice(quiet=True)

        # Text Setting with Initial Conditions
        self.updateMemoryBtn()
        self.setFreq(self.freq)

        # Value Setting with Initial Conditions
        self.setWindowTitle("CyberRadio")
        self.volume.setValue(self.demod.vol*100)

        # Buttons Handlers Declaration
        self.modFmBtn.clicked.connect(self.handleFm)
        self.modAmBtn.clicked.connect(self.handleAm)
        self.powerBtn.clicked.connect(self.handlePower)
        self.settingsBtn.clicked.connect(self.handleSettingsWindow)
        self.memA.clicked.connect(self.handleMemory)
        self.memB.clicked.connect(self.handleMemory)
        self.memC.clicked.connect(self.handleMemory)
        self.memD.clicked.connect(self.handleMemory)
        self.memE.clicked.connect(self.handleMemory)

        # Load Custom Fonts
        QFontDatabase.addApplicationFont(
            appctxt.get_resource('fonts/Comfortaa-VariableFont.ttf'))
        QFontDatabase.addApplicationFont(
            appctxt.get_resource('fonts/RacingSansOne-Regular.ttf'))
        QFontDatabase.addApplicationFont(
            appctxt.get_resource('fonts/RobotoMono-Bold.ttf'))
        QFontDatabase.addApplicationFont(
            appctxt.get_resource('fonts/RobotoMono-Regular.ttf'))

        # Change Handlers
        self.freqLine.editingFinished.connect(self.handleFreq)
        self.volume.valueChanged.connect(self.handleVol)
        self.deviceBox.currentTextChanged.connect(self.handleDevice)

        # Custom Stylecheet
        self.volume.setStyleSheet(volumeStyle())
        self.deviceBox.setStyleSheet(
            comboStyle(appctxt.get_resource('down_arrow.png')))
        self.uiToggle(False)

        # Print System Information
        print("[GUI] Python Version:\n{}".format(sys.version))
        print("[GUI] Numpy Version: {}".format(np.__version__))

        # Show Window
        self.center()
        self.show()

    def closeEvent(self, event):
        self.displayTimer.stop()
        self.demod.stop()
        self.saveSettings()
        print("[GUI] Exiting...")

    def checkSettings(self):
        settings = QSettings('luigicruz', 'CyberRadio')
        if not settings.value('settings_set', type=bool):
            print("[GUI] Previous settings not found. Creating new ones.")
            settings.setValue('settings_set', True)
            settings.setValue('enable_cuda', False)
            settings.setValue('enable_cursed', False)
            settings.setValue('enable_numba', not is_mac())
            settings.setValue('enable_stereo', True)
            settings.setValue('last_frequency', 96.9e6)
            settings.setValue('demodulation_mode', 0)
            settings.setValue('tau', 75e-6)
            settings.setValue('favorites_list', defaultFavorites())
            settings.setValue('volume', 0)
            del settings

    def saveSettings(self):
        print("[GUI] Saving current settings.")
        settings = QSettings('luigicruz', 'CyberRadio')
        settings.setValue('last_frequency', self.freq)
        settings.setValue('enable_cuda', self.enableCuda)
        settings.setValue('enable_numba', self.enableNumba)
        settings.setValue('enable_cursed', self.enableCursed)
        settings.setValue('enable_stereo', self.enableStereo)
        settings.setValue('demodulation_mode', self.demod.mode)
        settings.setValue('tau', self.tau)
        settings.setValue('favorites_list', self.memory)
        settings.setValue('volume', self.demod.vol)
        del settings

    def loadSettings(self):
        print("[GUI] Loading settings.")
        self.checkSettings()

        settings = QSettings('luigicruz', 'CyberRadio')
        self.memory = settings.value('favorites_list')
        self.freq = settings.value('last_frequency', type=float)
        self.enableCuda = settings.value('enable_cuda', type=bool)
        self.enableNumba = settings.value('enable_numba', type=bool)
        self.enableCursed = settings.value('enable_cursed', type=bool)
        self.enableStereo = settings.value('enable_stereo', type=bool)
        self.mode = settings.value('demodulation_mode', type=int)
        self.tau = settings.value('tau', type=float)
        self.vol = settings.value('volume', type=float)

        # Print Configurations
        print("[GUI] Enable CUDA: {}".format(self.enableCuda))
        print("[GUI] Enable Numba: {}".format(self.enableNumba))
        print("[GUI] Enable Stereo: {}".format(self.enableStereo))
        print("[GUI] Enable Cursed: {}".format(self.enableCursed))
        print("[GUI] Demodulator Mode: {}".format(self.mode))
        print("[GUI] Tau Value: {}".format(self.tau))
        print("[GUI] Volume Value: {}".format(self.vol))
        print("[GUI] Initial Freq: {}".format(self.freq))

        # Configure Universal Demodulator
        self.demod = Demodulator(self.freq, self.cursednet, self.enableCuda,
                                 self.enableNumba, self.enableCursed)
        self.demod.mode = self.mode
        self.demod.vol = self.vol
        self.demod.tau = self.tau

        self.saveSettings()

    def center(self):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def handleSettingsWindow(self):
        self.settingsWindow = SettingsWindow(self)

    def updateMemoryBtn(self):
        self.memA.setText(parseSaveStr(self.memory, "memA"))
        self.memB.setText(parseSaveStr(self.memory, "memB"))
        self.memC.setText(parseSaveStr(self.memory, "memC"))
        self.memD.setText(parseSaveStr(self.memory, "memD"))
        self.memE.setText(parseSaveStr(self.memory, "memE"))

    def handleMemory(self):
        sender = self.sender().objectName()
        modifiers = QApplication.keyboardModifiers()

        if modifiers == Qt.ControlModifier:
            self.memory[sender]["freq"] = self.freq
            self.updateMemoryBtn()
        else:
            self.setFreq(self.memory[sender]["freq"])

    def updateDisplay(self):
        self.chBtn.setText("STEREO" if self.demod.stereo else "MONO")

    def handleVol(self):
        self.demod.vol = float(self.volume.value()/100)

    def handleFreq(self):
        newFreq = float(self.freqLine.displayText().replace(',', ''))
        print("[GUI] New Frequency: {}".format(newFreq))
        self.setFreq(newFreq)

    def setFreq(self, newFreq):
        self.freqLine.setText(str(int(newFreq)).zfill(9))

        if self.freq != newFreq:
            self.demod.setFreq(newFreq)
            self.freq = newFreq

    def setMode(self, newMode):
        self.demod.mode = newMode
        if self.demod.mode == 0:
            self.modFmBtn.setEnabled(False)
            self.modAmBtn.setEnabled(True)
            self.modAmBtn.setStyleSheet(modBtnDisabled())
            self.modFmBtn.setStyleSheet(modBtnEnabled())
        elif self.demod.mode == 1:
            self.modFmBtn.setEnabled(True)
            self.modAmBtn.setEnabled(False)
            self.modAmBtn.setStyleSheet(modBtnEnabled())
            self.modFmBtn.setStyleSheet(modBtnDisabled())

    def handlePower(self):
        if not self.handleDevice():
            return

        if self.running:
            self.powerBtn.setText("ON")
            self.deviceBox.setEnabled(True)
            self.settingsBtn.setEnabled(True)
            self.displayTimer.stop()
            self.deviceCheckTimer.start()
            self.updateDevices()
            self.uiToggle(False)
            self.demod.stop()
        else:
            self.powerBtn.setText("OFF")
            self.deviceBox.setEnabled(False)
            self.settingsBtn.setEnabled(False)
            self.setMode(self.demod.mode)
            self.demod.start(QThread.TimeCriticalPriority)
            self.displayTimer.start()
            self.deviceCheckTimer.stop()
            self.uiToggle(True)

        self.running = not self.running

    def handleFm(self):
        self.setMode(0)

    def handleAm(self):
        self.setMode(1)

    def uiToggle(self, opt):
        self.modFmBtn.setEnabled(opt)
        self.modAmBtn.setEnabled(opt)

        self.memA.setEnabled(opt)
        self.memB.setEnabled(opt)
        self.memC.setEnabled(opt)
        self.memD.setEnabled(opt)
        self.memE.setEnabled(opt)

        self.rdsBtn.setEnabled(opt)
        self.chBtn.setEnabled(opt)

    def updateDevices(self):
        classes, devices = getDeviceList()
        self.powerBtn.setEnabled(True if len(devices) > 0 else False)

        for i, device in enumerate(devices):
            if self.deviceBox.findData(device) == -1:
                self.deviceBox.addItem(
                    classes[i]['label'].split(' [')[0], device)

        for i in range(self.deviceBox.count()):
            if self.deviceBox.itemData(i) not in devices:
                self.deviceBox.removeItem(i)

    def handleDevice(self, quiet=False):
        newDevice = self.deviceBox.currentData()

        if newDevice is None:
            return False

        try:
            if newDevice not in self.demod.device:
                self.demod.setDevice(newDevice)
            return True
        except Exception as e:
            if not quiet:
                error_dialog = QErrorMessage()
                error_dialog.showMessage(str(e))
                error_dialog.exec_()
            print(str(e))
            return False


if __name__ == '__main__':
    print("Starting CyberRadio...")
    appctxt = ApplicationContext()
    window = MainWindow(appctxt)
    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
