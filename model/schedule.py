"""
Pick the build time statistically, instead of by guess.

Global news output is the sum of regional outputs, each following its own
local working day. There is no hour when the whole world is dark, so the
question is where the SUM is lowest -- and, within that trough, where it
sits just before the largest producer ramps for the day.

Regional weights are shares of global news output. The local-hour activity
curve follows the pattern GDELT describes for its crawlers: an automated
CMS dump around 05:00 local, a brief lull at 05:30, then the real ramp from
06:00 and a working-day plateau.
"""
import numpy as np

# region: (UTC offset hours, share of global news output)
REGIONS = {
    "US East":        (-4,  0.26),
    "US West":        (-7,  0.08),
    "UK":             ( 1,  0.12),
    "Europe (CET)":   ( 2,  0.14),
    "India":          ( 5.5,0.09),
    "China":          ( 8,  0.08),
    "Japan":          ( 9,  0.05),
    "Australia":      (10,  0.03),
    "Gulf":           ( 3,  0.06),
    "Latin America":  (-3,  0.05),
    "Africa":         ( 2,  0.04),
}

def activity(local_hour):
    """Relative publishing intensity at a given local hour (0-1)."""
    h = local_hour % 24
    # overnight floor, 05:00 CMS dump, 05:30 lull, ramp from 06:00,
    # working plateau, evening decay
    if   h < 4.5:            return 0.06
    elif h < 5.0:            return 0.10
    elif h < 5.5:            return 0.34      # automated morning dump
    elif h < 6.0:            return 0.12      # the lull GDELT describes
    elif h < 9.0:            return 0.30 + 0.55*(h-6)/3
    elif h < 17.0:           return 0.92
    elif h < 20.0:           return 0.92 - 0.45*(h-17)/3
    elif h < 23.0:           return 0.47 - 0.33*(h-20)/3
    else:                    return 0.10

def curve(step=0.25):
    hours = np.arange(0, 24, step)
    tot = np.zeros_like(hours)
    per = {}
    for name,(off,wt) in REGIONS.items():
        a = np.array([activity(h+off) for h in hours])*wt
        per[name]=a; tot+=a
    return hours, tot, per

if __name__ == "__main__":
    hours, tot, per = curve()
    tot_n = tot/tot.max()*100

    print("GLOBAL NEWS OUTPUT BY UTC HOUR  (100 = daily peak)\n")
    for i,h in enumerate(hours):
        if h % 1 == 0:
            bar = "#"*int(tot_n[i]/2.2)
            print(f"  {int(h):02d}:00 UTC  {tot_n[i]:5.1f}  {bar}")

    k = int(np.argmin(tot))
    print(f"\n  global minimum : {hours[k]:05.2f} UTC  ({tot_n[k]:.1f}% of peak)")

    # quiet band: within 10% of the minimum
    thr = tot.min()*1.10
    band = hours[tot <= thr]
    print(f"  quiet band     : {band.min():05.2f}–{band.max():05.2f} UTC")

    # within the quiet band, prefer the latest point still quiet -- the moment
    # just before the first major region ramps.
    print(f"  last quiet hour: {band.max():05.2f} UTC  (ramp begins after)")

    # who is awake at the minimum
    print(f"\n  awake at {hours[k]:05.2f} UTC:")
    for name,(off,wt) in sorted(REGIONS.items(), key=lambda x:-per[x[0]][k]):
        lh=(hours[k]+off)%24
        print(f"    {name:<15} local {int(lh):02d}:{int(lh%1*60):02d}  "
              f"contributing {per[name][k]/tot[k]*100:4.1f}%")
