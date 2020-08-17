import queue
import numpy as np
import time
from soapy import Soapy
from PyQt5.QtCore import QThread
from radio.analog import WBFM, Decimator
import importlib


class Demodulator(QThread):

    def __init__(self, soapy, cuda=False):
        QThread.__init__(self)

        # Global Settings
        self.soapy = soapy
        self.cuda = cuda
        self.running = False
        self.pmode = 1
        self.safed = True
        self.mode = 0
        self.vol = 1.0

        # FM Settings
        self.tau = 75e-6
        self.stereo = True

        # Demodulation FIFO
        self.que = queue.Queue()
        self.sd = importlib.import_module("sounddevice")

    def setDevice(self, device):
        self.sfs = int(768e3)
        self.mfs = int(240e3)
        self.afs = int(48e3)

        self.sfs = self.soapy.init(device, [
            [240e3, 256e3, 1.024e6, 2.5e6, 3.0e6],
            [960e3, 480e3, 240e3, 256e3, 768e3, 1.024e6, 2.5e6, 3.0e6],
        ])

        print("[DEMOD] Sampling Rate: {}".format(self.sfs))

        self.sdr_buff = 2048
        self.dsp_buff = self.sdr_buff * 8
        self.dec_out = int(np.ceil(self.dsp_buff/(self.sfs/self.mfs)))
        self.dsp_out = int(np.ceil(self.dec_out/(self.mfs/self.afs)))

        self.dec = Decimator(self.sfs, self.mfs, cuda=self.cuda)
        self.wbfm = WBFM(self.tau, self.mfs, self.afs, cuda=self.cuda)

    def stop(self):
        print("[DEMOD] Stopping.")
        self.running = False
        while not self.safed:
            time.sleep(0.05)

    def run(self):
        print("[DEMOD] Starting.")

        self.running = True
        self.safed = False

        buff = np.zeros([self.dsp_buff], dtype=np.complex64)
        self.soapy.start()

        with self.sd.OutputStream(blocksize=self.dsp_out, callback=self.router,
                                  samplerate=self.afs, channels=2):
            while self.running:
                count = 0
                while count < self.dsp_buff:
                    count += self.soapy.read([buff[count:]], self.sdr_buff)
                self.que.put(buff.astype(np.complex64))

        with self.que.mutex:
            self.que.queue.clear()

        self.soapy.stop()
        self.safed = True

    def router(self, outdata, f, t, s):
        if self.que.qsize() < 1:
            time.sleep(0.1)

        try:
            inp = self.que.get(timeout=0.5)
        except queue.Empty:
            raise self.sd.CallbackAbort
        finally:
            if not self.running:
                raise self.sd.CallbackAbort

        if self.mode == 0:
            L, R = self.wbfm.run(self.dec.run(inp))

            if self.wbfm.freq >= 19010 and self.wbfm.freq <= 18990:
                R = L

            outdata[:] = (np.dstack((L, R)) * self.vol)

        if self.mode == 1:
            LR = np.zeros((self.dsp_out*2), dtype=np.float32)
            outdata[:] = LR.reshape(self.dsp_out, 2)
