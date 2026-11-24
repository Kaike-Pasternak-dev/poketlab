"""Scan TCP da rede LOCAL (sua rede, com autorizacao). Sem root."""
from __future__ import annotations
import ipaddress, socket, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

COMMON_PORTS = (22, 80, 443, 8080, 8443, 554, 1883, 9100)

@dataclass
class HostResult:
    ip: str; open_ports: list

def local_ip(iface="wlan0"):
    try:
        r = subprocess.run(["ip","-4","addr","show",iface], capture_output=True, text=True, timeout=5)
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.startswith("inet "): return line.split()[1].split("/")[0]
    except Exception: pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1)); ip = s.getsockname()[0]; s.close()
        return ip
    except Exception: return None

def probe(ip, ports, timeout):
    opened = []
    for p in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(timeout)
        try:
            if s.connect_ex((ip, p)) == 0: opened.append(p)
        except OSError: pass
        finally: s.close()
    return HostResult(ip, opened)

def scan(cidr, ports=COMMON_PORTS, timeout=0.25, workers=64, progress=None):
    net = ipaddress.ip_network(cidr, strict=False)
    hosts = [str(h) for h in net.hosts()]
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(probe, ip, ports, timeout): ip for ip in hosts}
        done = 0
        for fut in as_completed(futs):
            res = fut.result(); done += 1
            if progress: progress(done, len(hosts))
            if res.open_ports: results.append(res)
    results.sort(key=lambda r: tuple(int(x) for x in r.ip.split(".")))
    return results
