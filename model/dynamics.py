"""
Coupled dynamics for the Collapse Index.

Each domain is a state x_i in [0,100]. Two forces act on it:

  1. intrinsic drift  r_i  — the observed rate of change of that domain's own
     indicators, in index-points per year, taken from reported trends.
  2. cross-coupling  K_ij — the degree to which a stressed domain j pushes
     domain i. Climate stress drives resource scarcity; resource scarcity
     drives conflict; conflict drives nuclear risk.

     dx_i/dt = r_i * (x_i/100) * (1 - x_i/100) * 4 + sum_j K_ij * (x_j/100)

The logistic term means a domain already near either extreme moves slowly;
the middle is where things move fastest. Coupling is one-directional per
entry and is NOT symmetric.

This is a projection, not a forecast. It assumes current rates and current
coupling hold, which is exactly what fails in a real crisis.
"""
import numpy as np, json
from scipy.integrate import solve_ivp

D=["Climate","Biosphere","Resources","Pollution","Health",
   "Nuclear","Conflict","Economy","Society","Technology"]
IDX={d:i for i,d in enumerate(D)}

# intrinsic drift, index-points per year, from reported trends
R=dict(Climate=0.8,Biosphere=1.0,Resources=0.5,Pollution=0.3,Health=0.4,
       Nuclear=2.5,Conflict=2.0,Economy=0.6,Society=1.0,Technology=3.0)

# K[target][source] = points/yr added to target when source sits at 100
COUP={
 "Biosphere":{"Climate":0.9,"Pollution":0.5},
 "Resources":{"Climate":1.0,"Biosphere":0.7,"Conflict":0.6},
 "Health":   {"Pollution":0.5,"Resources":0.6,"Conflict":0.5,"Economy":0.4},
 "Conflict": {"Resources":1.1,"Society":0.8,"Economy":0.6,"Climate":0.4},
 "Nuclear":  {"Conflict":1.4,"Society":0.5,"Technology":0.4},
 "Economy":  {"Conflict":0.9,"Resources":0.6,"Health":0.3,"Technology":0.4},
 "Society":  {"Economy":0.8,"Resources":0.5,"Technology":0.7,"Conflict":0.6},
 "Climate":  {"Resources":0.2},
 "Pollution":{"Economy":0.2},
 "Technology":{},
}
K=np.zeros((10,10))
for t,srcs in COUP.items():
    for s,v in srcs.items(): K[IDX[t],IDX[s]]=v

def rhs(t,x):
    x=np.clip(x,0,100); u=x/100.0
    drift=np.array([R[d] for d in D])*u*(1-u)*4
    return drift + K.dot(u)

def run(x0,years=10):
    s=solve_ivp(rhs,(0,years),x0,t_eval=np.linspace(0,years,years*4+1),
                method="RK45",rtol=1e-8,atol=1e-10)
    return s.t,s.y

if __name__=="__main__":
    wd=json.load(open("weighted_data.json"))
    x0=np.array([wd["domains"][d]["score_w"] for d in D])
    W =np.array([wd["domains"][d]["share"] for d in D])/100.0
    t,Y=run(x0,10)
    comp=W.dot(Y)

    print(f"start weighted index: {comp[0]:.1f}%")
    print()
    print(f"{'yr':>3} {'index':>7}  " + " ".join(f"{d[:4]:>5}" for d in D))
    for i,yr in enumerate(t):
        if abs(yr-round(yr))<1e-9 and int(yr)%2==0:
            print(f"{int(yr):>3} {comp[i]:>7.1f}  " + " ".join(f"{Y[j,i]:>5.1f}" for j in range(10)))
    print()
    # sensitivity: which domain, if frozen at today's value, slows the index most
    print("IF ONE DOMAIN WERE HELD AT TODAY'S LEVEL (10-yr index effect)")
    base=comp[-1]
    out=[]
    for j,d in enumerate(D):
        Rs=dict(R); Rs[d]=0.0
        Ksave=K[j].copy(); K[j]=0
        globals()['R']=Rs
        _,Y2=run(x0,10); K[j]=Ksave; globals()['R']=dict(Climate=0.8,Biosphere=1.0,
            Resources=0.5,Pollution=0.3,Health=0.4,Nuclear=2.5,Conflict=2.0,
            Economy=0.6,Society=1.0,Technology=3.0)
        out.append((base-W.dot(Y2)[-1],d))
    for v,d in sorted(out,reverse=True):
        print(f"  −{v:>4.1f} pts   {d}")

    json.dump(dict(domains=D,t=t.tolist(),Y=Y.tolist(),index=comp.tolist()),
              open("projection.json","w"))

def time_to(target=100.0, horizon=120):
    """Years until the weighted composite reaches `target`, at current rates."""
    import json as _j
    wd=_j.load(open("weighted_data.json"))
    x0=np.array([wd["domains"][d]["score_w"] for d in D])
    W =np.array([wd["domains"][d]["share"] for d in D])/100.0
    t,Y=run(x0,horizon); comp=W.dot(Y)
    for i in range(1,len(t)):
        if comp[i]>=target:
            a,b=comp[i-1],comp[i]
            f=(target-a)/(b-a)
            return t[i-1]+f*(t[i]-t[i-1]), comp
    return None, comp
