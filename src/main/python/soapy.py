import os
import ctypes
import SoapySDR
from SoapySDR import SOAPY_SDR_CRITICAL, SOAPY_SDR_RX, SOAPY_SDR_CF32


class Soapy():

    def __init__(self, ctx, power_mode=1):
        SoapySDR.setLogLevel(SOAPY_SDR_CRITICAL)

        self.sdr = None
        self.device = dict()
        self.rx_stream = None
        self.frequency = int(96.9e6)
        self.power_mode = power_mode

        try:
            mod_base = ctx.get_resource('lib/modules')
            sdr_base = ctx.get_resource('lib/sdr')
        except:
            print("[DEVICES] Loading external modules.")
            return

        for sdr_name in os.listdir(sdr_base):
            sdr_path = os.path.join(sdr_base, sdr_name)
            ctypes.CDLL(sdr_path, ctypes.RTLD_LOCAL)

        for mod_path in SoapySDR.listModules(mod_base):
            err = SoapySDR.loadModule(mod_path)
            if not err:
                ver = SoapySDR.getModuleVersion(mod_path)
                print("[GUI] Loaded internal module {} ({})".format(os.path.basename(mod_path), ver))
            else:
                print("[GUI] Can't load module {}: {}".format(mod_path, err))

    def list(self):
        lst = SoapySDR.Device.enumerate()
        return lst, [str(d) for d in lst]

    def stringToDevice(self, string):
        device_lst = self.list()[0]
        for device in device_lst:
            if str(device) in string:
                return device

    def init(self, device_str, supported_rates):
        self.close()

        device = self.stringToDevice(device_str)

        print("[SOAPY] Activating {} device.".format(device["label"]))

        self.sdr = SoapySDR.Device(device)
        self.sdr.setGainMode(SOAPY_SDR_RX, 0, True)
        self.sdr.setFrequency(SOAPY_SDR_RX, 0, self.frequency)

        rates = self.sdr.getSampleRateRange(SOAPY_SDR_RX, 0)

        for fs in reversed(rates):
            for pfs in supported_rates[self.power_mode]:
                if pfs >= fs.minimum() and pfs <= fs.maximum():
                    self.sdr.setSampleRate(SOAPY_SDR_RX, 0, int(pfs))
                    self.device = device_str
                    return int(pfs)

    def abandon(self):
        self.sdr = None
        self.rx_stream = None
        self.device = dict()

    def close(self):
        if self.sdr:
            self.stop()
            self.sdr = None
            self.device = dict()

    def start(self):
        if self.sdr:
            self.rx_stream = self.sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
            self.sdr.activateStream(self.rx_stream)

    def read(self, buffer, size):
        if self.sdr:
            return self.sdr.readStream(self.rx_stream, buffer,
                                       size, timeoutUs=int(5e5)).ret

    def tune(self, frequency):
        self.frequency = frequency
        if self.sdr:
            self.sdr.setFrequency(SOAPY_SDR_RX, 0, frequency)

    def stop(self):
        if self.sdr and self.rx_stream:
            self.sdr.deactivateStream(self.rx_stream)
            self.sdr.closeStream(self.rx_stream)
            self.rx_stream = None
