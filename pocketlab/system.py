"""Helpers de sistema: Termux:API, notificacao, launcher de apps."""
from __future__ import annotations
import shutil, subprocess
from dataclasses import dataclass

def have(cmd): return shutil.which(cmd) is not None

def run(cmd, timeout=30):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

def notify(title, msg):
    if have("termux-notification"):
        try: run(["termux-notification","-t",title,"-c",msg], timeout=5)
        except Exception: pass

def vibrate(ms=120):
    if have("termux-vibrate"):
        try: run(["termux-vibrate","-d",str(ms)], timeout=5)
        except Exception: pass

@dataclass(frozen=True)
class AppTarget:
    key: str; name: str; package: str; note: str

APPS = (
    AppTarget("nfc","NFC Tools","com.wakdev.wdnfc","ler/escrever NDEF"),
    AppTarget("mct","MIFARE Classic Tool","de.syss.MifareClassicTool","dump dos seus proprios cartoes Classic"),
    AppTarget("ble","nRF Connect","no.nordicsemi.android.mcp","scan BLE e explorer GATT"),
    AppTarget("wifi","WiFi Analyzer","com.farproc.wifi.analyzer","canais e RSSI (sem root)"),
    AppTarget("nrflogger","nRF Logger","no.nordicsemi.android.log","logs do nRF Connect"),
)

def launch(package):
    if have("monkey"):
        try:
            r = run(["monkey","-p",package,"-c","android.intent.category.LAUNCHER","1"], timeout=10)
            if r.returncode == 0 and "No activities found" not in (r.stdout + r.stderr):
                return True, "aberto"
        except Exception: pass
    if have("am"):
        try:
            r = run(["am","start","-a","android.intent.action.MAIN","-c","android.intent.category.LAUNCHER","-p",package], timeout=10)
            if r.returncode == 0: return True, "aberto"
        except Exception: pass
    return False, f"nao consegui abrir automatico; abre manual ({package})"
