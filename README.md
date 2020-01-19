# 📻 CyberRadio
### A SDR based FM/AM radio App for the desktop. [Video Demo](https://twitter.com/luigifcruz/status/1218739111332282368?s=20)
Compatible with most SDRs supported by SoapySDR. Based on the [radio-core](https://github.com/luigifreitas/radio-core) module. Accelerated on the GPU with CUDA by [#cuSignal](https://github.com/rapidsai/cusignal) and on the CPU with [Numba](https://numba.pydata.org/) functions.

<p align="center">
<img src="https://github.com/luigifreitas/CyberRadio/raw/master/cyberradio.png" />
</p>

## Features
- 📻 Listen to wideband FM and AM Stations with Stereo Support.
- ⏩ Hot-swap SDRs without closing the app.
- 🖱️ Programmable frequency shortcuts (Ctrl + Left Click). 
- 📦 Zero-installation pre-compiled binary packages.
- 💻 Efficient DSP.

## Compatibility
- Linux
- macOS Sierra
- Windows 10
- ARM SoC

## Validated Radios
- AirSpy HF+ Discovery
- LimeSDR Mini/USB
- PlutoSDR
- RTL-SDR

## Installation
Pre-compiled binary packages will be available once this app reaches beta. For now, if you want to try the pre-release version of the app, you should compile it yourself by following the instructions below.

### System Dependencies
- SoapySDR Base ([Repo](https://github.com/pothosware/SoapySDR))
- SoapySDR Modules ([LimeSuite](https://github.com/myriadrf/LimeSuite.git), [AirspyHF](https://github.com/pothosware/SoapyAirspyHF), [PlutoSDR](https://github.com/pothosware/SoapyPlutoSDR), [RTL-SDR](https://github.com/pothosware/SoapyRTLSDR))
- Python 3.5+ and Pip
- PulseAudio

#### Ubuntu/Debian
After installing the base SoapySDR and its modules, install the direct dependencies with `apt`:
```bash
$ apt install libpulse-dev libsamplerate-dev libasound2-dev portaudio19-dev
```

### Python Dependencies
```
$ git clone https://github.com/luigifreitas/CyberRadio
$ cd CyberRadio
$ pip3 install -r requirements.txt
```
##### Running
```
$ fbs run 
```
##### Compile Static Binary
```
$ fbs freeze
```
##### Generate Installer
```
$ fbs installer
```

## Hacking
The DSP used in this project is also available on the [PyAudio](https://github.com/luigifreitas/PyRadio) Repository. This is a better and more comprehensive way to start hacking this App. If you are interested in the core DSP, you should look for [radio-core](https://github.com/luigifreitas/radio-core).

## Roadmap
This is a list of unfinished tasks that I pretend to pursue soon. Pull requests are more than welcome!
- [ ] Study porting the UI to QML.
- [ ] Add AM Support.
- [ ] Add USB/LSB Support.
- [ ] Add TX capability.
- [ ] Finish RDS decoder.
- [ ] Add more settings.
- [ ] Implement settings memory.
- [ ] Better Stereo reliability detector.
- [ ] Docker cross-compiler for AArch-64.
- [ ] Docker cross-compiler for Windows.
