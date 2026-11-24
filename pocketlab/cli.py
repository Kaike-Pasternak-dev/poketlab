"""PocketLab - interface principal (rich)."""
from __future__ import annotations
import argparse, time

from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich import box

from . import __version__, ir, netscan, system, export
from .db import Store
from .ui import console, banner, rule, ok, warn, err, info, menu_table, panel

MENU = [
    ("1", "IR - frequencias", "lista carriers do blaster nativo"),
    ("2", "IR - transmitir raw", "envia pattern (microssegundos)"),
    ("3", "IR - gerar NEC", "address/command -> pattern pronto"),
    ("4", "Rede - scan local", "hosts/portas da SUA rede (autorizado)"),
    ("5", "Apps - NFC/BLE/WiFi", "abre ferramentas externas"),
    ("6", "Etiquetas de lab", "cadastra devices e associa capturas"),
    ("7", "Historico", "ultimas capturas no banco"),
    ("8", "Exportar", "JSON + CSV em ~/storage/shared"),
    ("9", "Diagnostico", "checa o que este aparelho suporta"),
    ("s", "Sobre / limites", "o que roda de verdade e o que exige hardware"),
    ("0", "Sair", ""),
]


def ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    try:
        v = console.input(f"[key]?[/] {prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        return default
    return v or default


def act_ir_freq(store):
    rule("IR - frequencias suportadas")
    good, out = ir.frequencies()
    if good:
        panel(out, "carriers (Hz)", "ok")
        store.log("ir_freq", "carriers", {"raw": out})
    else:
        warn(out)


def _send_pattern(store, freq, pattern, label, extra=None):
    good, msg = ir.transmit(freq, pattern)
    (ok if good else err)(msg)
    data = {"pattern": pattern, "ok": good}
    if extra:
        data.update(extra)
    cid = store.log("ir_tx", label, data)
    if good:
        system.vibrate(); system.notify("PocketLab", "IR transmitido")
    _offer_link(store, cid)


def act_ir_send(store):
    rule("IR - transmitir raw")
    if not ir.available():
        warn("este aparelho nao tem blaster IR (ou falta Termux:API)")
        return
    try:
        freq = int(ask("frequencia Hz", "38000"))
        if not (10000 <= freq <= 60000):
            err("frequencia fora da faixa tipica (10000-60000 Hz)"); return
    except ValueError:
        err("frequencia invalida (use um numero inteiro)"); return
    info("pattern = pulsos em microssegundos, separados por virgula")
    info("exemplo: 9000,4500,560,560,560,1690,560,560,560,40000")
    raw = ask("pattern")
    if not raw:
        warn("pattern vazio, cancelado"); return
    try:
        pattern = ir.parse_pattern(raw)
    except ValueError as e:
        err(str(e)); return
    _send_pattern(store, freq, pattern, f"{freq}Hz")


def act_ir_nec(store):
    rule("IR - gerar NEC")
    info("NEC padrao: address 8 bits + command 8 bits (inversos automaticos)")
    info("NEC extendido: address 16 bits (sem inverso)")
    ext = ask("extendido? (s/N)", "n").lower().startswith("s")
    try:
        addr = ir.parse_hex_byte(ask("address hex (ex 0x04)"))
        cmd = ir.parse_hex_byte(ask("command hex (ex 0x08)"))
        pattern = ir.nec_pattern(addr, cmd, extended=ext)
    except ValueError as e:
        err(str(e)); return
    info(f"pattern gerado: {len(pattern)} valores @ {ir.NEC_CARRIER} Hz")
    console.print(", ".join(map(str, pattern[:12])) + " ...")
    if not ir.available():
        warn("sem blaster IR: vou so salvar o pattern no banco")
        cid = store.log("ir_nec", f"addr={addr:#x} cmd={cmd:#x}",
                        {"address": addr, "command": cmd, "extended": ext,
                         "freq": ir.NEC_CARRIER, "pattern": pattern})
        ok(f"pattern salvo (captura #{cid})")
        _offer_link(store, cid)
        return
    if ask("transmitir agora? (S/n)", "s").lower().startswith("n"):
        cid = store.log("ir_nec", f"addr={addr:#x} cmd={cmd:#x}",
                        {"address": addr, "command": cmd, "extended": ext,
                         "freq": ir.NEC_CARRIER, "pattern": pattern})
        ok(f"pattern salvo (captura #{cid})")
        _offer_link(store, cid)
        return
    _send_pattern(store, ir.NEC_CARRIER, pattern,
                  f"NEC addr={addr:#x} cmd={cmd:#x}",
                  {"address": addr, "command": cmd, "extended": ext})


def act_scan(store):
    rule("Rede - scan local")
    warn("use somente na SUA rede ou com autorizacao por escrito")
    ip = netscan.local_ip()
    if ip:
        info(f"IP detectado: {ip}")
        default_cidr = ip.rsplit(".", 1)[0] + ".0/24"
    else:
        default_cidr = "192.168.1.0/24"
    cidr = ask("faixa CIDR", default_cidr)
    try:
        import ipaddress
        net = ipaddress.ip_network(cidr, strict=False)
        if net.num_addresses > 4096:
            err("faixa grande demais (max /20). reduz o escopo."); return
    except ValueError as e:
        err(f"CIDR invalido: {e}"); return

    with Progress(SpinnerColumn(), TextColumn("[accent]{task.description}"),
                  BarColumn(bar_width=None),
                  TextColumn("{task.completed}/{task.total}"),
                  TimeElapsedColumn(), console=console) as prog:
        task = prog.add_task("varrendo", total=max(net.num_addresses - 2, 1))
        def cb(done, total):
            prog.update(task, completed=done, total=total)
        results = netscan.scan(cidr, progress=cb)

    if not results:
        warn("nenhum host com porta comum aberta"); return
    t = Table(box=box.SIMPLE_HEAVY, header_style="accent", border_style="muted")
    t.add_column("host", style="brand")
    t.add_column("portas abertas", style="key")
    for r in results:
        t.add_row(r.ip, ", ".join(map(str, r.open_ports)))
    console.print(t)
    ok(f"{len(results)} host(s) encontrado(s)")
    cid = store.log("lan_scan", cidr,
                    {"hosts": [{"ip": r.ip, "ports": r.open_ports} for r in results]})
    system.notify("PocketLab", f"scan: {len(results)} hosts")
    _offer_link(store, cid)


def act_apps(store):
    rule("Apps - ferramentas externas")
    items = [(str(i + 1), a.name, a.note) for i, a in enumerate(system.APPS)]
    console.print(menu_table(items))
    k = ask("numero")
    if not k.isdigit() or not (1 <= int(k) <= len(system.APPS)):
        warn("opcao invalida"); return
    app = system.APPS[int(k) - 1]
    good, msg = system.launch(app.package)
    (ok if good else warn)(f"{app.name}: {msg}")
    store.log("app_launch", app.name, {"package": app.package, "ok": good})


def _offer_link(store, capture_id):
    devs = store.list_devices()
    if not devs:
        return
    if ask("associar esta captura a um device? (s/N)", "n").lower().startswith("s"):
        _link_capture(store, capture_id)


def _link_capture(store, capture_id):
    devs = store.list_devices()
    if not devs:
        warn("nenhum device cadastrado ainda"); return
    t = Table(box=box.SIMPLE_HEAVY, header_style="accent", border_style="muted")
    t.add_column("id", style="key", justify="right")
    t.add_column("nome", style="brand")
    t.add_column("categoria", style="muted")
    for d in devs:
        t.add_row(str(d[0]), d[1], d[2] or "")
    console.print(t)
    k = ask("id do device")
    if not k.isdigit():
        warn("id invalido"); return
    did = int(k)
    if not store.get_device(did):
        warn("device nao existe"); return
    store.link(capture_id, did)
    ok(f"captura #{capture_id} associada ao device #{did}")


def act_devices(store):
    rule("Etiquetas de lab")
    sub = [("1", "listar devices", ""), ("2", "cadastrar device", ""),
           ("3", "ver capturas de um device", ""), ("4", "remover device", ""),
           ("5", "associar captura existente", ""), ("0", "voltar", "")]
    console.print(menu_table(sub))
    k = ask("opcao")
    if k == "1":
        devs = store.list_devices()
        if not devs:
            warn("nenhum device cadastrado"); return
        t = Table(box=box.SIMPLE_HEAVY, header_style="accent", border_style="muted")
        t.add_column("id", style="key", justify="right")
        t.add_column("nome", style="brand")
        t.add_column("categoria", style="muted")
        t.add_column("local", style="muted")
        t.add_column("notas", style="muted")
        for d in devs:
            t.add_row(str(d[0]), d[1], d[2] or "", d[3] or "", d[4] or "")
        console.print(t)
    elif k == "2":
        name = ask("nome do device (ex: TV sala)")
        if not name:
            warn("nome vazio"); return
        cat = ask("categoria (ex: tv, ac, sensor)")
        loc = ask("local (ex: sala)")
        notes = ask("notas")
        try:
            did = store.add_device(name, cat, loc, notes)
            ok(f"device cadastrado #{did}: {name}")
        except Exception as e:
            err(f"nao cadastrou (nome duplicado?): {e}")
    elif k == "3":
        k2 = ask("id do device")
        if not k2.isdigit():
            warn("id invalido"); return
        dev = store.get_device(int(k2))
        if not dev:
            warn("device nao existe"); return
        rows = store.captures_for_device(int(k2))
        panel(f"{dev[1]}  |  {dev[2] or '-'}  |  {dev[3] or '-'}", "device", "accent")
        if not rows:
            warn("sem capturas associadas"); return
        t = Table(box=box.SIMPLE_HEAVY, header_style="accent", border_style="muted")
        t.add_column("id", style="key", justify="right")
        t.add_column("quando", style="muted")
        t.add_column("tipo", style="brand")
        t.add_column("rotulo", style="muted")
        for r in rows:
            t.add_row(str(r[0]), r[1], r[2], r[3] or "")
        console.print(t)
    elif k == "4":
        k2 = ask("id do device pra remover")
        if not k2.isdigit():
            warn("id invalido"); return
        if ask("confirma remover? (s/N)", "n").lower().startswith("s"):
            store.delete_device(int(k2)); ok("removido")
    elif k == "5":
        k2 = ask("id da captura")
        if not k2.isdigit():
            warn("id invalido"); return
        _link_capture(store, int(k2))


def act_history(store):
    rule("Historico")
    rows = store.recent(25)
    if not rows:
        warn("banco vazio"); return
    t = Table(box=box.SIMPLE_HEAVY, header_style="accent", border_style="muted")
    t.add_column("id", style="muted", justify="right")
    t.add_column("quando", style="muted")
    t.add_column("tipo", style="brand")
    t.add_column("rotulo", style="key")
    for r in rows:
        t.add_row(str(r[0]), r[1], r[2], r[3] or "")
    console.print(t)


def act_export(store):
    rule("Exportar")
    j, c = export.export_all(store)
    ok(f"JSON: {j}")
    ok(f"CSV : {c}")
    system.notify("PocketLab", "export concluido")


def act_diag(store):
    rule("Diagnostico do aparelho")
    import os
    checks = [
        ("Termux:API (termux-notification)", system.have("termux-notification")),
        ("Blaster IR (transmit)", ir.available()),
        ("IR frequencies", system.have("termux-infrared-frequencies")),
        ("comando ip", system.have("ip")),
        ("monkey (launcher)", system.have("monkey")),
        ("acesso a ~/storage/shared", os.path.isdir(os.path.expanduser("~/storage/shared"))),
    ]
    t = Table(box=box.SIMPLE_HEAVY, header_style="accent", border_style="muted")
    t.add_column("recurso", style="brand")
    t.add_column("status", justify="center")
    for name, good in checks:
        t.add_row(name, "[ok]sim[/]" if good else "[warn]nao[/]")
    console.print(t)
    panel(
        "O celular NAO possui radio Sub-GHz, antena 125 kHz, receptor IR\n"
        "nem GPIO exposto. Essas funcoes exigem hardware externo.\n"
        "NFC e monitor mode WiFi ficam nos apps dedicados.",
        "limites de hardware (fisica, nao software)", "warn")
    store.log("diag", "checks", {n: g for n, g in checks})


def act_about(store):
    rule("Sobre / limites")
    panel(
        "PocketLab roda 100% no Termux, sem hardware externo.\n"
        "Executa de verdade: IR nativo (se houver blaster) com gerador NEC,\n"
        "scan TCP da sua rede local, etiquetas de lab, banco SQLite e export.\n\n"
        "O celular NAO tem radio Sub-GHz, antena 125 kHz, receptor IR nem GPIO.\n"
        "Essas funcoes exigem hardware externo - nenhum software cria radio.\n\n"
        "Uso somente em equipamentos proprios ou com autorizacao por escrito.",
        "o que este app e e o que nao e", "accent")


ACTIONS = {
    "1": act_ir_freq, "2": act_ir_send, "3": act_ir_nec, "4": act_scan,
    "5": act_apps, "6": act_devices, "7": act_history, "8": act_export,
    "9": act_diag, "s": act_about,
}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pocketlab",
                                 description="Canivete de laboratorio 100% Termux")
    ap.add_argument("--db", default=None, help="caminho do banco SQLite")
    ap.add_argument("--version", action="version", version=f"PocketLab {__version__}")
    args = ap.parse_args(argv)

    store = Store(args.db) if args.db else Store()
    try:
        while True:
            console.clear()
            banner(__version__, store.count(), ir.available())
            console.print(menu_table(MENU))
            choice = ask("opcao").lower()
            if choice == "0":
                info("falou"); break
            fn = ACTIONS.get(choice)
            if not fn:
                warn("opcao invalida"); time.sleep(0.6); continue
            try:
                fn(store)
            except KeyboardInterrupt:
                warn("interrompido")
            except Exception as e:
                err(f"{type(e).__name__}: {e}")
            console.input("\n[muted]Enter para voltar ao menu...[/]")
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
