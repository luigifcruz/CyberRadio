from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QApplication, QMainWindow, QErrorMessage
from PyQt5.QtCore import QThreadPool, QTimer, Qt, QThread
from PyQt5.QtGui import QFontDatabase
from PyQt5 import uic
from demod import Demodulator
from styles import *
from utils import parseSaveStr, getDeviceList
import sys

class MainWindow(QMainWindow):
    
  def __init__(self):
    super(MainWindow, self).__init__()
    uic.loadUi(appctxt.get_resource('mainwindow.ui'), self)
    
    # Initial Conditions
    self.memory = {
      "memA": {
        "freq": 96.9e6,
        "band": "FM" },
      "memB": {
        "freq": 94.5e6,
        "band": "FM" },
      "memC": {
        "freq": 97.5e6,
        "band": "FM" },
      "memD": {
        "freq": 95.5e6,
        "band": "FM" },
      "memE": {
        "freq": 87.9e6,
        "band": "FM" },
    }
    self.freq = 96.9e6
    self.running = False
    self.mode = 0

    self.tau = 75e-6

    # Universal Demodulator Configuration
    self.demod = Demodulator(self.freq)
    
    # Threading 
    self.threadpool = QThreadPool()
   
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
    self.memA.clicked.connect(self.handleMemory)
    self.memB.clicked.connect(self.handleMemory)
    self.memC.clicked.connect(self.handleMemory)
    self.memD.clicked.connect(self.handleMemory)
    self.memE.clicked.connect(self.handleMemory)

    # Load Custom Fonts
    QFontDatabase.addApplicationFont(appctxt.get_resource('fonts/Comfortaa-VariableFont.ttf'))
    QFontDatabase.addApplicationFont(appctxt.get_resource('fonts/RacingSansOne-Regular.ttf'))
    QFontDatabase.addApplicationFont(appctxt.get_resource('fonts/RobotoMono-Bold.ttf'))
    QFontDatabase.addApplicationFont(appctxt.get_resource('fonts/RobotoMono-Regular.ttf'))

    # Change Handlers
    self.freqLine.editingFinished.connect(self.handleFreq)
    self.volume.valueChanged.connect(self.handleVol)
    self.deviceBox.currentTextChanged.connect(self.handleDevice)

    # Custom Stylecheet
    self.volume.setStyleSheet(volumeStyle())
    self.deviceBox.setStyleSheet(comboStyle(appctxt.get_resource('down_arrow.png')))
    self.uiToggle(False)

    # Show Window
    self.show()
    
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

  def setMode(self, newMode, force=False):
    if self.mode != newMode or force:
      self.mode = newMode
      if self.mode == 0:
        self.demod.activateFm(self.tau)
        self.modFmBtn.setEnabled(False)
        self.modAmBtn.setEnabled(True)
        self.modAmBtn.setStyleSheet(modBtnDisabled())
        self.modFmBtn.setStyleSheet(modBtnEnabled())
      elif self.mode == 1:
        self.demod.activateAm()
        self.modFmBtn.setEnabled(True)
        self.modAmBtn.setEnabled(False)
        self.modAmBtn.setStyleSheet(modBtnEnabled())
        self.modFmBtn.setStyleSheet(modBtnDisabled())

  def handlePower(self):
    print("[GUI] Power Toggle")

    if not self.handleDevice():
        return
    
    if self.running == True:
      self.powerBtn.setText("ON")
      self.demod.stop()
      self.displayTimer.stop()
      self.deviceCheckTimer.start()
      self.updateDevices()
      self.deviceBox.setEnabled(True)
      self.uiToggle(False)
    else:
      self.powerBtn.setText("OFF")
      self.setMode(self.mode, force=True)
      self.demod.start(QThread.TimeCriticalPriority)
      self.displayTimer.start()
      self.deviceCheckTimer.stop()
      self.deviceBox.setEnabled(False)
      self.uiToggle(True)

    self.running = not self.running  

  def handleFm(self):
    print("[GUI] Activating FM")
    self.setMode(0)
  
  def handleAm(self):
    print("[GUI] Activating AM")
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
        self.deviceBox.addItem(classes[i]['label'].split(' [')[0], device)

    for i in range(self.deviceBox.count()):
      if self.deviceBox.itemData(i) not in devices:
       self.deviceBox.removeItem(i)

  def handleDevice(self, quiet=False):
    newDevice = self.deviceBox.currentData()
    try:
      if newDevice not in self.demod.device and newDevice is not None:
        self.demod.activateDevice(newDevice)
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
  window = MainWindow()
  exit_code = appctxt.app.exec_()
  sys.exit(exit_code)