from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32
import SoapySDR
import queue
import numpy as np
import time
from PyQt5.QtCore import QThread
from utils import toDevice
from radio.analog import WBFM, Decimator
import importlib


class Demodulator(QThread):

    def __init__(self, freq, model_path,
                 cuda=False, numba=False, cursed=False):
        QThread.__init__(self)

        # Global Settings
        self.device = dict()
        self.cursed = cursed
        self.numba = numba
        self.cuda = cuda
        self.running = False
        self.pmode = 1
        self.safed = True
        self.mode = 0
        self.vol = 1.0
        self.freq = freq

        # FM Settings
        self.tau = 75e-6
        self.stereo = True

        # Demodulation FIFO
        self.que = queue.Queue()
        self.sd = importlib.import_module("sounddevice")

        # Enable PyTorch Model
        if self.cursed:
            try:
                self.th = importlib.import_module("torch")
                self.net = importlib.import_module("cursednet")

                self.dev = self.th.device('cuda' if self.th.cuda.is_available() else 'cpu')
                self.model = self.net.CursedNet(input_ch=2, output_ch=1)
                self.model = self.model.to(self.dev)
                self.model.load_state_dict(self.th.load(model_path))
                self.model.eval()
            except Exception as e:
                print('Error importing Torch Library:', e)

    def setDevice(self, device):
        device = toDevice(device)

        print("[DEMOD] Activating {} device.".format(device["label"]))

        self.sdr = SoapySDR.Device(device)
        self.sdr.setGainMode(SOAPY_SDR_RX, 0, True)
        self.sdr.setFrequency(SOAPY_SDR_RX, 0, self.freq)
        supported_fs = self.sdr.getSampleRateRange(SOAPY_SDR_RX, 0)

        avfs = [
            [256e3, 1.024e6, 2.5e6, 3.0e6],
            [960e3, 480e3, 256e3, 768e3, 1.024e6, 2.5e6, 3.0e6],
        ]

        self.sfs = int(768e3)
        self.mfs = int(256e3)
        self.afs = int(32e3)

        for fs in reversed(supported_fs):
            for pfs in avfs[self.pmode]:
                if pfs >= fs.minimum() and pfs <= fs.maximum():
                    self.sfs = int(pfs)
                    break

        print("[DEMOD] Sampling Rate: {}".format(self.sfs))

        self.sdr_buff = 1024
        self.dsp_buff = self.sdr_buff * 16
        self.dec_out = int(self.dsp_buff/(self.sfs/self.mfs))
        self.dsp_out = int(self.dec_out/(self.mfs/self.afs))

        self.fdec = Decimator(self.afs, self.afs, self.dsp_out, cuda=self.cuda)
        self.dec = Decimator(self.sfs, self.mfs, self.dec_out, cuda=self.cuda)
        self.wbfm = WBFM(self.tau, self.mfs, self.afs,
                         self.dec_out, cuda=self.cuda, numba=self.numba)

        self.sdr.setSampleRate(SOAPY_SDR_RX, 0, self.sfs)
        self.device = str(device)

    def setFreq(self, freq):
        self.freq = freq
        self.sdr.setFrequency(SOAPY_SDR_RX, 0, self.freq)

    def stop(self):
        print("[DEMOD] Stopping.")
        self.running = False
        while not self.safed:
            time.sleep(0.05)

    def run(self):
        print("[DEMOD] Starting.")

        self.running = True
        self.safed = False

        plan = [(i*self.sdr_buff) for i in range(self.dsp_buff//self.sdr_buff)]
        buff = np.zeros([self.dsp_buff], dtype=np.complex64)
        rx = self.sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
        self.sdr.activateStream(rx)

        with self.sd.OutputStream(blocksize=self.dsp_out, callback=self.router,
                                  samplerate=self.afs, channels=2):
            while self.running:
                for i in plan:
                    self.sdr.readStream(rx, [buff[i:]], self.sdr_buff)
                self.que.put_nowait(buff.astype(np.complex64))

        with self.que.mutex:
            self.que.queue.clear()

        self.sdr.deactivateStream(rx)
        self.sdr.closeStream(rx)
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

            if self.cursed:
                inp = self.dec.run(inp)
                inp = np.stack([np.real(inp), np.imag(inp)])
                inp = np.expand_dims(inp, axis=0).astype(np.float32)
                inp = self.th.tensor(inp)
                res = self.model(inp.to(self.dev))[0]
                res = res.cpu().detach().numpy()[0]
                res = self.fdec.run(res)
                outdata[:] = (np.dstack((res, res)) * self.vol)
                return

            L, R = self.wbfm.run(self.dec.run(inp))
            L = self.fdec.run(L)
            R = self.fdec.run(R)

            if self.wbfm.freq >= 19010 and self.wbfm.freq <= 18990:
                R = L

            outdata[:] = (np.dstack((L, R)) * self.vol)

        if self.mode == 1:
            LR = np.zeros((self.dsp_out*2), dtype=np.float32)
            outdata[:] = LR.reshape(self.dsp_out, 2)
