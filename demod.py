from SoapySDR import *
import SoapySDR
import pyaudio
import signal
import queue
import numpy as np
import collections
import scipy.signal as sig
from pll import PLL
from PyQt5.QtCore import QThread
from utils import *

class Demodulator(QThread):
  
  def __init__(self, freq):
    QThread.__init__(self)

    self.device = dict()
    self.running = False

    self.freq = freq
    self.samp_rate = 256e3
    self.audio_fs = int(32e3)
    self.buff_len = 2048
    self.samples = int(self.buff_len/8)
    self.vol = 1.0
 
    self.p = pyaudio.PyAudio()
    self.que = queue.Queue()
    self.pll = PLL(self.samp_rate, self.buff_len)

  def activateDevice(self, device):
    self.device = device
    device = toDevice(device)

    print("[DEMOD] Activating {} device.".format(device["label"]))

    try:
      self.sdr.unmake()
    except:
      pass

    self.sdr = SoapySDR.Device(device)
    self.sdr.setGainMode(SOAPY_SDR_RX, 0, True)
    self.sdr.setSampleRate(SOAPY_SDR_RX, 0, self.samp_rate)
    self.sdr.setFrequency(SOAPY_SDR_RX, 0, self.freq)

  def setFreq(self, freq):
    self.freq = freq
    self.sdr.setFrequency(SOAPY_SDR_RX, 0, self.freq)
      
  def stop(self):
    print("[DEMOD] Stopping Demodulator")
    self.running = False

  def run(self):
    print("[DEMOD] Starting Demodulator")
    
    self.rx = self.sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
    self.sdr.activateStream(self.rx)
    
    self.running = True
    buff = np.zeros([self.buff_len], dtype=np.complex64)
    
    while self.running:
      self.sdr.readStream(self.rx, [buff], self.buff_len, timeoutUs=int(1e9))
      self.que.put(buff.astype(np.complex64))
    
    self.stream.stop_stream()
    self.stream.close()
    
    self.sdr.deactivateStream(self.rx)
    self.sdr.closeStream(self.rx)
    print("[DEMOD] Device stream has stopped.")

  def activateFm(self, tau):
    print("[DEMOD] Setting up FM demodulator...")

    self.tau = tau
    self.stereo = True

    x = np.exp(-1/(self.audio_fs * self.tau))
    self.db = [1-x]; self.da = [1,-x]
    self.pb, self.pa = sig.butter(2, [19e3-200, 19e3+200], btype='band', fs=self.samp_rate)
    self.mb, self.ma = sig.butter(10, 15e3, btype='low', fs=self.samp_rate)
    self.hb, self.ha = sig.butter(2, 40, btype='high', fs=self.samp_rate)

    self.z = {
        "mlpr": sig.lfilter_zi(self.mb, self.ma), "mlmr": sig.lfilter_zi(self.mb, self.ma),
        "dlpr": sig.lfilter_zi(self.db, self.da), "dlmr": sig.lfilter_zi(self.db, self.da),
        "hlpr": sig.lfilter_zi(self.hb, self.ha),
        "dc": collections.deque(maxlen=32),
        "diff": 0.0,
    }    
    
    try:
      self.stream.stop_stream()
      self.stream.close()
    except:
      pass

    self.stream = self.p.open(
      format=pyaudio.paFloat32,
      channels=2,
      frames_per_buffer=self.samples,
      rate=self.audio_fs,
      output=True,
      stream_callback=self.fm)

  def fm(self, in_data, frame_count, time_info, status):
    b = np.array(self.que.get()) 
    d = np.concatenate(([self.z['diff']], np.angle(b)), axis=None)
    b = np.diff(np.unwrap(d))
    self.z['diff'] = d[-1]
    b /= np.pi
    
    # Normalize for DC
    dc = np.mean(b)
    self.z['dc'].append(dc)
    b -= np.mean(self.z['dc'])
    
    # Synchronize PLL with Pilot
    P = sig.lfilter(self.pb, self.pa, b)
    self.pll.step(P)

    # Demod Left + Right (LPR)
    LPR, self.z['mlpr'] = sig.lfilter(self.mb, self.ma, b, zi=self.z['mlpr'])
    LPR, self.z['hlpr'] = sig.lfilter(self.hb, self.ha, LPR, zi=self.z['hlpr'])
    LPR = sig.resample(LPR, self.samples, window='hamming')
    LPR, self.z['dlpr'] = sig.lfilter(self.db, self.da, LPR, zi=self.z['dlpr'])
    
    I = np.zeros((self.samples*2), dtype=np.float32)

    if self.pll.freq < 19015 and self.pll.freq > 18985:
      # Demod Left - Right (LMR)
      LMR = (self.pll.mult(2) * b) * 1.05
      LMR, self.z['mlmr'] = sig.lfilter(self.mb, self.ma, LMR, zi=self.z['mlmr'])
      LMR = sig.resample(LMR, self.samples, window='hamming')
      LMR, self.z['dlmr'] = sig.lfilter(self.db, self.da, LMR, zi=self.z['dlmr'])
      
      # Mix L+R and L-R to generate L and R
      L = LPR+LMR; R = LPR-LMR
      
      self.stereo = True
      I[0::2] = L; I[1::2] = R 
    else:
      self.stereo = False
      I[0::2] = LPR; I[1::2] = LPR
    
    I *= self.vol
    I = np.clip(I, -1.0, 1.0)

    return (I.reshape(self.samples, 2), pyaudio.paContinue)

  def activateAm(self):
    print("[DEMOD] Setting up AM demodulator...")
    
    try:
      self.stream.stop_stream()
      self.stream.close()
    except:
      pass 

  def am(self, in_data, frame_count, time_info, status):
    pass
