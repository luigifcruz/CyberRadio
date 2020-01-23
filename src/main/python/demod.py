from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32
import SoapySDR
import queue
import numpy as np
from PyQt5.QtCore import QThread
from utils import toDevice
from radio.analog import WBFM
import sounddevice as sd


class Demodulator(QThread):

    def __init__(self, freq, cuda=False, numba=False):
        QThread.__init__(self)

        self.numba = numba
        self.cuda = cuda

        self.device = dict()
        self.running = False
        self.safed = True
        self.mode = 0

        self.vol = 1.0
        self.freq = freq
        self.sfs = int(256e3)
        self.afs = int(32e3)

        self.sdr_buff = 1024
        self.dsp_buff = self.sdr_buff * 4
        self.dsp_out = int(self.dsp_buff/(self.sfs/self.afs))

    def setDevice(self, device):
        device = toDevice(device)

        print("[DEMOD] Activating {} device.".format(device["label"]))

        self.sdr = SoapySDR.Device(device)
        self.sdr.setGainMode(SOAPY_SDR_RX, 0, True)
        self.sdr.setSampleRate(SOAPY_SDR_RX, 0, self.sfs)
        self.sdr.setFrequency(SOAPY_SDR_RX, 0, self.freq)

        self.device = str(device)

    def setFM(self, tau):
        self.stereo = True
        self.demod = WBFM(tau, self.sfs, self.afs,
                          self.dsp_buff, self.cuda, self.numba)

    def setAM(self):
        pass

    def setFreq(self, freq):
        self.freq = freq
        self.sdr.setFrequency(SOAPY_SDR_RX, 0, self.freq)

    def stop(self):
        print("[DEMOD] Stopping.")
        self.running = False
        while not self.safed:
            pass

    def run(self):
        print("[DEMOD] Starting.")

        self.running = True
        self.safed = False
        buff = np.zeros([self.dsp_buff], dtype=np.complex64)
        rx = self.sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
        self.sdr.activateStream(rx)
        self.que = queue.Queue()

        with sd.RawOutputStream(blocksize=self.dsp_out, callback=self.router,
                                samplerate=self.afs, channels=2):
            while self.running:
                for i in range(self.dsp_buff//self.sdr_buff):
                    self.sdr.readStream(rx, [buff[(i*self.sdr_buff):]],
                                        self.sdr_buff, timeoutUs=int(1e9))
                self.que.put(buff.astype(np.complex64))

        self.sdr.deactivateStream(rx)
        self.sdr.closeStream(rx)
        self.safed = True

    def router(self, outdata, frames, time, status):
        if self.mode == 0:
            outdata[:] = self.fm().tobytes()
        elif self.mode == 1:
            outdata[:] = self.am().tobytes()

    def fm(self):
        L, R = self.demod.run(self.que.get())

        if self.demod.freq >= 19015 and self.demod.freq <= 18985:
            return (np.dstack((L, L)) * self.vol).astype(np.float32)
        else:
            return (np.dstack((L, R)) * self.vol).astype(np.float32)

    def am(self):
        self.que.get()
        LR = np.zeros((self.dsp_out*2), dtype=np.float32)
        return LR.reshape(self.dsp_out, 2)
