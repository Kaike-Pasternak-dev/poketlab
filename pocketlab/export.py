"""Export do banco para JSON/CSV."""
from __future__ import annotations
import csv, json, os
from datetime import datetime
from .db import Store

def export_all(store):
    rows = store.all_rows()
    outdir = os.path.expanduser("~/storage/shared")
    if not os.path.isdir(outdir): outdir = os.path.expanduser("~/pocketlab")
    os.makedirs(outdir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    jpath = os.path.join(outdir, f"pocketlab_{stamp}.json")
    cpath = os.path.join(outdir, f"pocketlab_{stamp}.csv")
    payload = [{"id":r[0],"ts":r[1],"kind":r[2],"label":r[3],"data":json.loads(r[4]) if r[4] else None} for r in rows]
    with open(jpath,"w",encoding="utf-8") as f: json.dump(payload,f,ensure_ascii=False,indent=2)
    with open(cpath,"w",newline="",encoding="utf-8") as f:
        wr = csv.writer(f); wr.writerow(["id","ts","kind","label","data"]); wr.writerows(rows)
    return jpath, cpath
