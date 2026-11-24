#!/data/data/com.termux/files/usr/bin/bash
set -e
pkg update -y
pkg install python termux-api git -y
termux-setup-storage || true
pip install --upgrade rich
echo
echo 'PocketLab instalado. Rode: python -m pocketlab'
