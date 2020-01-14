#!/bin/bash

cd /home

SoapySDRUtil --info
SoapySDRUtil --find

export PATH="~/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv global 3.7.6
python3 --version

fbs clean
fbs freeze
