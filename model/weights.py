"""
Weighting model for the Collapse Index.

Each indicator is scored on four axes (1-5), and the weight is derived from them.
No weight is assigned by hand.

  S  severity ceiling   how much of civilization this could end at its worst
  V  velocity           how fast it can traverse from now to catastrophic
                        5 = minutes/hours, 4 = weeks, 3 = months, 2 = years, 1 = decades
  I  irreversibility    how recoverable the catastrophic state is
                        5 = permanent, 3 = centuries, 1 = fixable within years
  C  coupling           how strongly failure here drives failure elsewhere

  w_raw = S^1.0 * V^0.8 * I^0.4 * C^0.6     (normalised to sum to 1)

Velocity carries the largest exponent after severity: a hazard that can
cross its whole range before anyone can react is worth more attention
than one of equal magnitude that takes forty years to arrive.
"""
import json

# id: (S, V, I, C)
AX = {
 1:(5,1,5,5),  2:(4,1,5,5),  3:(4,1,5,4),  4:(3,1,5,3),  5:(5,2,5,5),
 6:(4,2,5,4),  7:(4,2,4,4),  8:(3,3,5,3),  9:(4,2,5,4), 10:(4,1,4,4),
11:(4,2,3,4), 12:(3,2,3,3), 13:(4,3,2,4), 14:(2,3,1,3), 15:(3,1,3,4),
16:(2,1,4,2), 17:(2,1,2,2), 18:(3,1,5,3), 19:(3,1,3,3), 20:(2,1,2,2),
21:(4,2,3,3), 22:(5,4,3,4), 23:(2,2,2,2), 24:(2,1,2,2), 25:(3,2,2,3),
26:(5,5,4,4), 27:(5,5,5,5), 28:(5,4,3,4), 29:(4,3,4,4), 30:(5,5,5,5),
31:(3,4,2,4), 32:(5,5,3,5), 33:(4,4,3,5), 34:(3,4,2,4), 35:(3,3,2,4),
36:(2,2,2,3), 37:(1,3,1,2), 38:(2,1,2,3), 39:(2,3,2,3), 40:(3,4,2,4),
41:(3,2,3,4), 42:(2,2,2,3), 43:(2,2,2,3), 44:(2,3,2,3), 45:(2,2,2,3),
46:(5,4,4,4), 47:(2,3,2,3), 48:(3,5,2,4), 49:(5,4,4,4), 50:(1,2,4,2),
}

def build():
    d=json.load(open("index_data.json"))
    rows=d["indicators"]
    tot=0.0
    for r in rows:
        S,V,I,C = AX[r["id"]]
        w = (S**1.0)*(V**0.8)*(I**0.4)*(C**0.6)
        r.update(S=S,V=V,I=I,C=C,w_raw=w); tot+=w
    for r in rows:
        r["weight"]=r["w_raw"]/tot
    weighted = sum(r["weight"]*r["score"] for r in rows)
    flat     = sum(r["score"] for r in rows)/len(rows)

    # domain rollup
    dom={}
    for r in rows:
        e=dom.setdefault(r["domain"],{"w":0.0,"ws":0.0,"n":0,"s":0.0})
        e["w"]+=r["weight"]; e["ws"]+=r["weight"]*r["score"]; e["n"]+=1; e["s"]+=r["score"]
    for k,e in dom.items():
        e["score_w"]=round(e["ws"]/e["w"],1); e["score_flat"]=round(e["s"]/e["n"],1)
        e["share"]=round(e["w"]*100,1)

    print(f"{'DOMAIN':<13}{'share%':>8}{'flat':>8}{'weighted':>10}")
    for k,e in sorted(dom.items(), key=lambda x:-x[1]["share"]):
        print(f"{k:<13}{e['share']:>8.1f}{e['score_flat']:>8.1f}{e['score_w']:>10.1f}")
    print()
    print(f"  Unweighted index : {flat:.1f}%")
    print(f"  Weighted index   : {weighted:.1f}%")
    print()
    print("TOP 10 INDICATORS BY WEIGHT")
    for r in sorted(rows,key=lambda r:-r["weight"])[:10]:
        print(f"  {r['weight']*100:>5.2f}%  S{r['S']} V{r['V']} I{r['I']} C{r['C']}  "
              f"{r['topic']:<22} score {r['score']:>5.1f}")
    print()
    print("BOTTOM 5 BY WEIGHT")
    for r in sorted(rows,key=lambda r:r["weight"])[:5]:
        print(f"  {r['weight']*100:>5.2f}%  S{r['S']} V{r['V']} I{r['I']} C{r['C']}  {r['topic']}")

    json.dump(dict(indicators=rows,domains=dom,weighted=round(weighted,1),
                   flat=round(flat,1)),open("weighted_data.json","w"),indent=1)
    return weighted

if __name__=="__main__": build()
