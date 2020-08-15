#!/bin/bash

cd /home

echo "[GEN] Setup pyenv..."
export PATH="~/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

echo "PATH=$PATH:$(ruby -e 'print Gem.user_dir')/bin" >> ~/.bashrc
source ~/.bashrc

echo "[GEN] Executing installer..."
fbs installer

echo "[GEN] Exiting..."