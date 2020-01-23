from SoapySDR import SOAPY_SDR_RX, SOAPY_SDR_CF32
import SoapySDR
import pyaudio
import queue
import numpy as np
from PyQt5.QtCore import QThread
from utils import toDevice
from radio.analog import WBFM


class Demodulator(QThread):

    def __init__(self, freq, cuda=False, numba=False):
        QThread.__init__(self)

        self.numba = numba
        self.cuda = cuda

        self.device = dict()
        self.running = False
        self.mode = 0

        self.vol = 1.0
        self.freq = freq
        self.sfs = int(256e3)
        self.afs = int(32e3)

        self.sdr_buff = 1024
        self.dsp_buff = self.sdr_buff * 4
        self.dsp_out = int(self.dsp_buff/(self.sfs/self.afs))

        self.que = queue.Queue()

    def activateDevice(self, device):
        device = toDevice(device)

        print("[DEMOD] Activating {} device.".format(device["label"]))

        self.sdr = SoapySDR.Device(device)
        self.sdr.setGainMode(SOAPY_SDR_RX, 0, True)
        self.sdr.setSampleRate(SOAPY_SDR_RX, 0, self.sfs)
        self.sdr.setFrequency(SOAPY_SDR_RX, 0, self.freq)

        self.p = pyaudio.PyAudio()
        self.device = str(device)

    def setFreq(self, freq):
        self.freq = freq
        self.sdr.setFrequency(SOAPY_SDR_RX, 0, self.freq)

    def stop(self):
        print("[DEMOD] Stopping Demodulator")
        self.running = False

    def run(self):
        print("[DEMOD] Starting Demodulator")

        self.running = True
        self.mode = 0

        buff = np.zeros([self.dsp_buff], dtype=np.complex64)
        self.rx = self.sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
        self.sdr.activateStream(self.rx)

        while self.running:
            for i in range(self.dsp_buff//self.sdr_buff):
                self.sdr.readStream(
                    self.rx,
                    [buff[(i*self.sdr_buff):]],
                    self.sdr_buff,
                    timeoutUs=int(1e9))
            self.que.put(buff.astype(np.complex64))

        self.sdr.deactivateStream(self.rx)
        self.sdr.closeStream(self.rx)

        print("[DEMOD] Device stream has stopped.")

    def activateFm(self, tau):
        print("[DEMOD] Setting up FM demodulator...")

        self.running = True
        self.mode = 0

        self.stereo = True
        self.demod = WBFM(tau, self.sfs, self.afs, self.dsp_buff, self.cuda, self.numba)

        stream_info = pyaudio.PaMacCoreStreamInfo(
            flags=pyaudio.PaMacCoreStreamInfo.paMacCorePlayNice)

        self.que.queue.clear()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=2,
            frames_per_buffer=self.dsp_out,
            rate=self.afs,
            output=True,
            output_host_api_specific_stream_info=stream_info,
            stream_callback=self.fm)

    def fm(self, in_data, frame_count, time_info, status):
        # Receive and Demodulate Samples
        L, R = self.demod.run(self.que.get())

        # Create PyAudio Stereo Matrix
        LR = np.zeros((self.dsp_out*2), dtype=np.float32)

        if self.demod.freq >= 19015 and self.demod.freq <= 18985:
            LR[0::2] = L
            LR[1::2] = L
        else:
            LR[0::2] = L
            LR[1::2] = R

        # Further Sanitize the Output
        LR *= self.vol
        LR = LR.reshape(self.dsp_out, 2)

        if not self.running or self.mode == 0:
            print("[DEMOD] Stopping dangling stream.")
            self.que.queue.clear()
            return (None, pyaudio.paAbort)

        return (np.copy(LR.tobytes()), pyaudio.paContinue)

    def activateAm(self):
        print("[DEMOD] Setting up AM demodulator...")

        self.running = True
        self.mode = 1

    def am(self, in_data, frame_count, time_info, status):
        pass
