#!/bin/bash

cd /home

echo "[GEN] Setup pyenv..."
export PATH="~/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

echo "[GEN] Sanity check..."
SoapySDRUtil --info
python3 --version
echo "+++++++++++++++++++++"

echo "[GEN] Building binary..."
fbs clean
fbs freeze

echo "[GEN] Exiting..."