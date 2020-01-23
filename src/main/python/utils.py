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
    return lst, [str(d) for d in lst]


def parseSaveStr(memory, name):
    return str(memory[name]["freq"]/1e6) + " " + memory[name]["band"]


def isCudaCapable():
    try:
        import cupy
    except ImportError:
        return False
    return True


def defaultFavorites():
    return {
            "memA": {
                "freq": 96.9e6,
                "band": "FM"
            },
            "memB": {
                "freq": 94.5e6,
                "band": "FM"
            },
            "memC": {
                "freq": 97.5e6,
                "band": "FM"
            },
            "memD": {
                "freq": 95.5e6,
                "band": "FM"
            },
            "memE": {
                "freq": 87.9e6,
                "band": "FM"
            },
        }
