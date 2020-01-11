import SoapySDR
from SoapySDR import SOAPY_SDR_CRITICAL

def toDevice(string):
  deviceList = getDeviceList()[0]
  for device in deviceList:
    if str(device) in string:
      return device

def getDeviceList():
  SoapySDR.setLogLevel(SOAPY_SDR_CRITICAL)
  lst = SoapySDR.Device.enumerate()
  return lst, [ str(d) for d in lst ]

def parseSaveStr(memory, name):
  return str(memory[name]["freq"]/1e6) + " " + memory[name]["band"]
