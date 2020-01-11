import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic 
from demod import Demodulator
from styles import *
from utils import *

app = QtWidgets.QApplication(sys.argv)

class MainWindow(QtWidgets.QMainWindow):
    
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    uic.loadUi("mainwindow.ui", self)
    
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
    self.threadpool = QtCore.QThreadPool()
   
    # Display Update Timer
    self.displayTimer = QtCore.QTimer(self)
    self.displayTimer.setInterval(500)
    self.displayTimer.timeout.connect(self.updateDisplay)
    
    # Devices Update Timer
    self.deviceCheckTimer = QtCore.QTimer(self)
    self.deviceCheckTimer.setInterval(1000)
    self.deviceCheckTimer.timeout.connect(self.updateDevices)
    self.deviceCheckTimer.start()
    self.updateDevices()

    # Activate First Device
    if self.deviceBox.count() > 0:
      self.demod.activateDevice(self.deviceBox.currentData())

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

    # Change Handlers
    self.freqLine.editingFinished.connect(self.handleFreq)
    self.volume.valueChanged.connect(self.handleVol)
    self.deviceBox.currentTextChanged.connect(self.handleDevice)

    # Custom Stylecheet
    self.volume.setStyleSheet(volumeStyle())

  def updateMemoryBtn(self):
    self.memA.setText(parseSaveStr(self.memory, "memA"))
    self.memB.setText(parseSaveStr(self.memory, "memB"))
    self.memC.setText(parseSaveStr(self.memory, "memC"))
    self.memD.setText(parseSaveStr(self.memory, "memD"))
    self.memE.setText(parseSaveStr(self.memory, "memE"))

  def handleMemory(self):
    sender = self.sender().objectName()
    modifiers = QtWidgets.QApplication.keyboardModifiers()

    if modifiers == QtCore.Qt.ControlModifier:
      self.memory[sender]["freq"] = self.freq
      self.updateMemoryBtn()
    else:
      self.setFreq(self.memory[sender]["freq"])

  def updateDisplay(self):
    self.chLabel.setText("STEREO" if self.demod.stereo else "MONO")

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
      elif self.mode == 1:
        self.demod.activateAm()

  def handlePower(self):
    print("[GUI] Power Toggle")

    if self.deviceBox.currentData() not in self.demod.device:
      self.demod.activateDevice(self.deviceBox.currentData())
    
    if self.running == True:
      self.powerBtn.setText("ON")
      self.demod.stop()
      self.displayTimer.stop()
      self.deviceCheckTimer.start()
      self.updateDevices()
      self.deviceBox.setEnabled(True)
    else:
      self.powerBtn.setText("OFF")
      self.setMode(self.mode, force=True)
      self.demod.start()
      self.displayTimer.start()
      self.deviceCheckTimer.stop()
      self.deviceBox.setEnabled(False)

    self.running = not self.running  

  def handleFm(self):
    print("[GUI] Activating FM")
    self.setMode(0)
  
  def handleAm(self):
    print("[GUI] Activating AM")
    self.setMode(1)

  def updateDevices(self):
    classes, devices = getDeviceList()
    self.powerBtn.setEnabled(True if len(devices) > 0 else False)
    
    for i, device in enumerate(devices):
      if self.deviceBox.findData(device) == -1:
        self.deviceBox.addItem(classes[i]['label'].split(' [')[0], device)

    for i in range(self.deviceBox.count()):
      if self.deviceBox.itemData(i) not in devices:
       self.deviceBox.removeItem(i)

  def handleDevice(self):
    currentData = self.deviceBox.currentData()
    if currentData not in self.demod.device and currentData is not None:
      self.demod.activateDevice(self.deviceBox.currentData())

window = MainWindow()
window.show()
app.exec_()
