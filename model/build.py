"""
Full build: fetch -> score -> weight -> solve dynamics -> emit web/data.js

Run:  python3 model/build.py
Every step degrades gracefully; a dead source keeps its stored value.
"""
import json, sys, os, datetime, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "model"), str(ROOT / "fetch")]

import indicators as IN
import weights as WT
import dynamics as DY
import sources as SRC

STATE = ROOT / "state.json"


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"as_of": {}}


def main():
    state = load_state()
    live = SRC.fetch_all()

    # ---- apply live values over the stored table ----------------------------
    table = {row[0]: list(row) for row in IN.D}
    for ind_id, rec in live.items():
        if ind_id in table:
            table[ind_id][4] = rec["value"]
            state["as_of"][str(ind_id)] = rec["as_of"]
    IN.D = [tuple(v) for v in table.values()]

    # ---- score, weight, solve ----------------------------------------------
    os.chdir(ROOT)
    exec(open(ROOT / "model" / "indicators.py").read(), {"__name__": "__main__"})
    WT.build()
    years, _ = DY.time_to(100.0)

    w = json.loads((ROOT / "weighted_data.json").read_text())

    # 10-year projection for the chart
    import numpy as np
    x0 = np.array([w["domains"][d]["score_w"] for d in DY.D])
    wv = np.array([w["domains"][d]["share"] for d in DY.D]) / 100.0
    t, Y = DY.run(x0, 10)
    p = dict(t=t.tolist(), Y=Y.tolist(), index=wv.dot(Y).tolist())

    rows = [[r["id"], r["domain"], r["topic"], r["indicator"], r["current"], r["unit"],
             r["score"], r["source"], r["confidence"], r["S"], r["V"], r["I"], r["C"],
             round(r["weight"] * 100, 2), state["as_of"].get(str(r["id"]), "manual")]
            for r in w["indicators"]]
    dom = {k: dict(share=v["share"], w=v["score_w"], f=v["score_flat"])
           for k, v in w["domains"].items()}
    proj = dict(t=[t for i, t in enumerate(p["t"]) if i % 4 == 0],
                index=[round(v, 1) for i, v in enumerate(p["index"]) if i % 4 == 0],
                nuclear=[round(v, 1) for i, v in enumerate(p["Y"][5]) if i % 4 == 0],
                climate=[round(v, 1) for i, v in enumerate(p["Y"][0]) if i % 4 == 0])

    now = datetime.datetime.now(datetime.timezone.utc)
    js = (f"const IND={json.dumps(rows,separators=(',',':'))};\n"
          f"const DOM={json.dumps(dom,separators=(',',':'))};\n"
          f"const WEIGHTED={w['weighted']};\nconst FLAT={w['flat']};\n"
          f"const PROJ={json.dumps(proj,separators=(',',':'))};\n"
          f"const ANCHOR_MS={int(now.timestamp()*1000)};\n"
          f"const YEARS_TO_COLLAPSE={round(years,4)};\n"
          f"const UPDATED=\"{now.strftime('%-d %B %Y')}\";\n")
    (ROOT / "web" / "data.js").write_text(js)
    STATE.write_text(json.dumps(state, indent=1))

    print(f"\nweighted {w['weighted']}%  |  equal {w['flat']}%  "
          f"|  {years:.2f} yr to 100%  |  {len(live)} live of {len(rows)}")


if __name__ == "__main__":
    main()
