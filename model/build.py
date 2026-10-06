"""
Full build: fetch -> score -> weight -> solve dynamics -> emit docs/data.js

Run:  python model/build.py     (Windows)
      python3 model/build.py    (Linux / the GitHub runner)

Every step degrades gracefully. A dead source keeps its stored value and is
flagged "manual" in the output, so the page can show how stale each number is.
"""
import json, sys, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "model"), str(ROOT / "fetch")]

import indicators as IN
import weights as WT
import dynamics as DY
import sources as SRC

STATE = ROOT / "state.json"
OUT_DIR = ROOT / "docs"          # rename to "web" if not serving from Pages


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"as_of": {}}


def score(cur, a0, a100):
    return max(0.0, min(100.0, (cur - a0) / (a100 - a0) * 100))


def main():
    state = load_state()
    live = SRC.fetch_all()

    # ---- apply live values over the stored table ---------------------------
    rows = []
    for (i, dom, topic, ind, cur, a0, a100, unit, src, conf) in IN.D:
        if i in live:
            cur = live[i]["value"]
            state["as_of"][str(i)] = live[i]["as_of"]
            conf = 1
        rows.append(dict(id=i, domain=dom, topic=topic, indicator=ind,
                         current=round(cur, 4), a0=a0, a100=a100, unit=unit,
                         source=src, confidence=conf,
                         score=round(score(cur, a0, a100), 1)))

    # ---- derive weights from the four axes ---------------------------------
    tot = 0.0
    for r in rows:
        S, V, I, C = WT.AX[r["id"]]
        w = (S ** 1.0) * (V ** 0.8) * (I ** 0.4) * (C ** 0.6)
        r.update(S=S, V=V, I=I, C=C, w_raw=w)
        tot += w
    for r in rows:
        r["weight"] = r["w_raw"] / tot

    weighted = sum(r["weight"] * r["score"] for r in rows)
    flat = sum(r["score"] for r in rows) / len(rows)

    dom = {}
    for r in rows:
        e = dom.setdefault(r["domain"], {"w": 0.0, "ws": 0.0, "n": 0, "s": 0.0})
        e["w"] += r["weight"]; e["ws"] += r["weight"] * r["score"]
        e["n"] += 1; e["s"] += r["score"]
    for e in dom.values():
        e["score_w"] = round(e["ws"] / e["w"], 1)
        e["score_flat"] = round(e["s"] / e["n"], 1)
        e["share"] = round(e["w"] * 100, 1)

    # ---- coupled dynamics --------------------------------------------------
    import numpy as np
    x0 = np.array([dom[d]["score_w"] for d in DY.D])
    wv = np.array([dom[d]["share"] for d in DY.D]) / 100.0

    t, Y = DY.run(x0, 10)
    proj = dict(t=[float(v) for v in t[::4]],
                index=[round(float(v), 1) for v in wv.dot(Y)[::4]],
                nuclear=[round(float(v), 1) for v in Y[DY.IDX["Nuclear"]][::4]],
                climate=[round(float(v), 1) for v in Y[DY.IDX["Climate"]][::4]])

    tl, Yl = DY.run(x0, 150)
    compl = wv.dot(Yl)
    years = None
    for k in range(1, len(tl)):
        if compl[k] >= 100.0:
            a, b = compl[k - 1], compl[k]
            years = tl[k - 1] + (100.0 - a) / (b - a) * (tl[k] - tl[k - 1])
            break
    if years is None:
        years = 150.0

    # ---- emit --------------------------------------------------------------
    out_rows = [[r["id"], r["domain"], r["topic"], r["indicator"], r["current"],
                 r["unit"], r["score"], r["source"], r["confidence"],
                 r["S"], r["V"], r["I"], r["C"], round(r["weight"] * 100, 2),
                 state["as_of"].get(str(r["id"]), "manual")] for r in rows]
    out_dom = {k: dict(share=v["share"], w=v["score_w"], f=v["score_flat"])
               for k, v in dom.items()}

    now = datetime.datetime.now(datetime.timezone.utc)
    stamp = f"{now.day} {now.strftime('%B %Y')}"     # portable; %-d is glibc-only
    js = (f"const IND={json.dumps(out_rows, separators=(',', ':'))};\n"
          f"const DOM={json.dumps(out_dom, separators=(',', ':'))};\n"
          f"const WEIGHTED={round(weighted, 1)};\n"
          f"const FLAT={round(flat, 1)};\n"
          f"const PROJ={json.dumps(proj, separators=(',', ':'))};\n"
          f"const ANCHOR_MS={int(now.timestamp() * 1000)};\n"
          f"const YEARS_TO_COLLAPSE={round(years, 4)};\n"
          f'const UPDATED="{stamp}";\n')

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "data.js").write_text(js, encoding="utf-8")
    STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")

    print(f"\n  weighted {weighted:.1f}%   equal {flat:.1f}%   "
          f"{years:.2f} yr to 100%   {len(live)} live of {len(rows)}")
    for k, v in sorted(out_dom.items(), key=lambda x: -x[1]["share"]):
        print(f"    {k:<12} share {v['share']:>5.1f}%   weighted {v['w']:>5.1f}")


if __name__ == "__main__":
    main()
