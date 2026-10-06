"""
Live fetchers for the indicators that have a free, keyless public source.

Each returns (value, as_of_iso) or (None, None) on any failure. Nothing here
raises: a dead source must degrade to the stored manual value, never break
the build.

Most of the fifty indicators publish annually in PDFs and cannot be fetched.
Those keep their manual values in model/indicators.py and are flagged in the
output with their own cadence, so the page can show how stale each one is.
"""
import csv, io, json, datetime, urllib.request

UA = {"User-Agent": "collapse-index/1.0 (+https://github.com/)"}
TIMEOUT = 25

def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", "replace")

def _safe(fn):
    def wrap(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as e:
            print(f"  ! {fn.__name__}: {type(e).__name__}: {e}")
            return None, None
    return wrap


@_safe
def co2_ppm():
    """NOAA GML Mauna Loa weekly mean CO2. Updated weekly."""
    txt = _get("https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_weekly_mlo.csv")
    rows = [r for r in csv.reader(io.StringIO(txt)) if r and not r[0].startswith("#")]
    hdr = rows[0]
    for r in reversed(rows[1:]):
        rec = dict(zip(hdr, r))
        try:
            v = float(rec["average"])
        except (KeyError, ValueError):
            continue
        if v > 0:
            d = f"{int(rec['year'])}-{int(rec['month']):02d}-{int(rec['day']):02d}"
            return v, d
    return None, None


@_safe
def gistemp_anomaly():
    """NASA GISTEMP v4 global land-ocean anomaly vs 1951-80, converted to a
    pre-industrial (1880-99) baseline. Updated monthly."""
    txt = _get("https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv")
    lines = [l for l in txt.splitlines() if l and l[0].isdigit()]
    rd = csv.reader(io.StringIO("\n".join(lines)))
    best = None
    for r in rd:
        try:
            yr, jd = int(r[0]), r[13]
            if jd not in ("***", "", "****"):
                best = (yr, float(jd))
        except (ValueError, IndexError):
            continue
    if not best:
        return None, None
    # GISTEMP's 1951-80 base sits ~0.26 C above the 1880-99 mean
    return round(best[1] + 0.26, 3), f"{best[0]}-12-31"


@_safe
def worldbank(indicator, country="WLD"):
    """World Bank Open Data. Keyless. Annual, lags 1-2 years."""
    url = (f"https://api.worldbank.org/v2/country/{country}/indicator/"
           f"{indicator}?format=json&per_page=12&mrv=12")
    data = json.loads(_get(url))
    if len(data) < 2 or not data[1]:
        return None, None
    for row in data[1]:
        if row.get("value") is not None:
            return float(row["value"]), f"{row['date']}-12-31"
    return None, None


@_safe
def ucdp_conflicts(year=None):
    """UCDP candidate events API — count of distinct active conflicts."""
    year = year or datetime.date.today().year - 1
    url = f"https://ucdpapi.pcr.uu.se/api/ucdpprioconflict/24.1?pagesize=1000&Year={year}"
    data = json.loads(_get(url))
    ids = {r.get("conflict_id") for r in data.get("Result", []) if r.get("conflict_id")}
    return (len(ids), f"{year}-12-31") if ids else (None, None)


@_safe
def stooq_close(sym="^spx"):
    """Stooq daily close. Keyless CSV. Used as a market-stress input."""
    txt = _get(f"https://stooq.com/q/d/l/?s={sym}&i=d")
    rows = list(csv.DictReader(io.StringIO(txt)))
    last = rows[-1]
    return float(last["Close"]), last["Date"]


# indicator id -> callable returning (value, as_of)
#
# Only verified-working sources are listed. Units here MUST match the units of
# the matching indicator in model/indicators.py -- a fetcher that returns a
# different quantity than the indicator defines will silently corrupt the score.
LIVE = {
    1:  lambda: gistemp_anomaly(),            # deg C vs preindustrial
    2:  lambda: co2_ppm(),                    # ppm CO2 (not CO2-equivalent)
    13: lambda: worldbank("SN.ITK.DEFC.ZS"),  # % undernourished
    25: lambda: worldbank("SP.DYN.LE00.IN"),  # years
    37: lambda: worldbank("FP.CPI.TOTL.ZG"),  # % inflation
}

# Dropped, and why:
#   35  UCDP conflicts  -- public API returns 401; needs a key or a changed base
#   36  global debt     -- World Bank publishes no WLD aggregate for public debt
# Both keep their stored values and are flagged "manual" on the page.


def fetch_all():
    out = {}
    print("fetching live sources")
    for ind_id, fn in LIVE.items():
        v, d = fn()
        if v is not None:
            out[ind_id] = {"value": v, "as_of": d}
            print(f"  ok  #{ind_id:<3} {v} ({d})")
        else:
            print(f"  --  #{ind_id:<3} unavailable, keeping stored value")
    return out


if __name__ == "__main__":
    print(json.dumps(fetch_all(), indent=1))
