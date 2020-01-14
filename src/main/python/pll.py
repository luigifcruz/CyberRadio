import numpy as np
import collections
import scipy.signal as sig
from numba import njit

class PLL:
    def __init__(self, fs, length):
        self.fs = fs
        self.phi = 0.0
        self.freq = 0.0
        self.len = length
        self.f_cb = collections.deque(maxlen=64)
        self.algn = np.arange(0, np.pi*2, np.pi/6)
        self.times = np.arange(0, 1, 1/fs)[:self.len]

        print("[PLL] Compiling Numba...")
        signal = self.wave(self.fs/4, 1.0, self.times)
        result = self.freq_estimator(signal, self.fs)
        phase = self.alignments(signal, self.algn, self.fs/4, self.times)
        print("[PLL] Done ({}, {}, {})".format(self.fs/4, result, np.argmax(phase)))

    @staticmethod
    @njit(fastmath=True)
    def wave(freq, phase, times):
        return np.cos(2.0*np.pi*freq*times+phase)

    @staticmethod
    @njit(fastmath=True)
    def freq_estimator(x, fs):
        zeros = np.where(np.diff(np.signbit(x)))[0]
        return fs/np.mean(np.diff(zeros[5:-5]))/2

    @staticmethod
    @njit(fastmath=True)
    def alignments(x, algn, freq, times):
        err_ls = []
        for i in range(len(algn)):
            signal = x + np.sin(2.0*np.pi*freq*times+algn[i])
            err_ls.append(np.mean(np.abs(signal)))
        return err_ls
        
    def step(self, x):
        # Estimate Signal Frequency
        freq = self.freq_estimator(x, self.fs)
        self.f_cb.append(freq)
        self.freq = np.mean(self.f_cb)

        # Get Phase Compensation
        error_ls = self.alignments(x, self.algn, self.freq, self.times)
        self.phi = self.algn[np.argmax(error_ls)]
        
    def mult(self, mult=1):
        omega = ((self.phi*mult)+(np.pi/mult))
        return self.wave(self.freq*mult, omega, self.times)
