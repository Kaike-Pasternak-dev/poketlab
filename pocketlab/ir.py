"""Infravermelho nativo via Termux:API + gerador NEC."""
from __future__ import annotations
from . import system

def available(): return system.have("termux-infrared-transmit")

def frequencies():
    if not system.have("termux-infrared-frequencies"):
        return False, "Termux:API ausente ou aparelho sem blaster IR"
    r = system.run(["termux-infrared-frequencies"])
    out = (r.stdout or r.stderr).strip()
    return r.returncode == 0, out or "sem resposta"

def transmit(freq, pattern):
    if not available(): return False, "sem blaster IR / Termux:API"
    pat = ",".join(str(int(x)) for x in pattern)
    r = system.run(["termux-infrared-transmit","-f",str(freq),"-p",pat])
    ok = r.returncode == 0
    return ok, (r.stdout or r.stderr).strip() or ("enviado" if ok else "falha")

def parse_pattern(text):
    parts = [p.strip() for p in text.replace(" ", ",").split(",") if p.strip()]
    vals = [int(p) for p in parts]
    if not vals: raise ValueError("pattern vazio")
    if any(v <= 0 for v in vals): raise ValueError("todos os valores devem ser > 0")
    return vals

NEC_CARRIER = 38000

def nec_pattern(address, command, extended=False):
    if not (0 <= command <= 0xFF): raise ValueError("command deve estar entre 0x00 e 0xFF")
    if extended:
        if not (0 <= address <= 0xFFFF): raise ValueError("address extendido 0x0000-0xFFFF")
        payload = [(address >> i) & 1 for i in range(16)]
    else:
        if not (0 <= address <= 0xFF): raise ValueError("address deve estar entre 0x00 e 0xFF")
        payload = [(address >> i) & 1 for i in range(8)]
        payload += [((~address) >> i) & 1 for i in range(8)]
    payload += [(command >> i) & 1 for i in range(8)]
    payload += [((~command) >> i) & 1 for i in range(8)]
    pattern = [9000, 4500]
    for bit in payload:
        pattern.append(560)
        pattern.append(1690 if bit else 560)
    pattern.append(560)
    pattern.append(40000)
    return pattern

def parse_hex_byte(text):
    t = text.strip().lower().replace("0x", "")
    if not t: raise ValueError("valor vazio")
    v = int(t, 16)
    if not (0 <= v <= 0xFFFF): raise ValueError("fora da faixa 0x0000-0xFFFF")
    return v
