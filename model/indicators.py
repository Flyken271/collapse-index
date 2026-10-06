import json, statistics as st

# (id, domain, topic, indicator, current, a0, a100, unit, source, conf)
# conf: 1 = search-confirmed value, 2 = mixed, 3 = background/constructed
D=[
 (1,"Climate","Global temperature","GMST anomaly vs preindustrial",1.45,0,4.0,"°C","Copernicus/C3S 2025",1),
 (2,"Climate","Greenhouse gases","Atmospheric CO2",425.7,280,700,"ppm","NOAA Mauna Loa",1),
 (3,"Climate","Ocean heat","0-2000m heat content anomaly",300,0,1000,"ZJ","Cheng et al./IAP 2026",2),
 (4,"Climate","Sea level","Rate of global mean rise",4.4,0,30,"mm/yr","NASA/JPL 2025",1),
 (5,"Climate","Tipping points","AMOC strength at 26N",16,20,5,"Sv","RAPID/NOC 2025",2),
 (6,"Biosphere","Biodiversity","Living Planet Index",27,100,10,"index","WWF/ZSL LPR 2024",2),
 (7,"Biosphere","Insects","Cumulative abundance change",-40,0,-75,"%","meta-analysis 2020-25",2),
 (8,"Biosphere","Coral reefs","Reef area under bleaching stress",84,0,90,"%","NOAA CRW / ICRI 2025",1),
 (9,"Biosphere","Forests","Amazon cumulative deforestation",18,0,25,"% of biome","INPE/Lovejoy-Nobre",2),
 (10,"Biosphere","Soil","Share of land degraded",30,0,50,"%","UNCCD 2025",2),
 (11,"Resources","Freshwater","Population under seasonal scarcity",50,5,75,"% of humanity","UN-Water/UNESCO",2),
 (12,"Resources","Fisheries","Stocks fished unsustainably",35,10,70,"%","FAO SOFIA 2026",1),
 (13,"Resources","Food security","Prevalence of undernourishment",8.5,2.5,40,"% of population","World Bank / FAO",1),
 (14,"Resources","Critical minerals","Top-3 share of refining",87,40,95,"%","IEA 2026",2),
 (15,"Resources","Energy","Fossil share of primary energy",80,10,85,"%","IEA/EI 2025",2),
 (16,"Pollution","Plastics","Annual production",450,100,1200,"Mt/yr","OECD",2),
 (17,"Pollution","Air quality","Population-weighted PM2.5",29,5,100,"ug/m3","HEI SoGA 2025",2),
 (18,"Pollution","Novel entities","Planetary boundary status",70,0,100,"constructed","PIK/SRC PHC 2025",3),
 (19,"Pollution","Nitrogen cycle","Reactive N fixation",190,62,300,"Tg N/yr","Richardson et al.",2),
 (20,"Pollution","Pollution mortality","Share of all deaths",16,1,50,"%","Lancet Planet Health",2),
 (21,"Health","AMR","Deaths attributable to resistance",1.14,0.25,10,"millions/yr","GRAM/Lancet 2024",1),
 (22,"Health","Pandemic risk","Global Health Security Index",40.2,85,25,"index","NTI/JHU",2),
 (23,"Health","Vaccination","DTP3 coverage",85,95,50,"%","WHO/UNICEF WUENIC",2),
 (24,"Health","Mental health","Population with a mental disorder",12.5,5,30,"%","WHO 2025",2),
 (25,"Health","Health systems","Global life expectancy",73.3,85,45,"years","WHO/UN WPP",2),
 (26,"Nuclear","Arsenals","Warheads on high alert",2100,0,4000,"warheads","SIPRI 2025",2),
 (27,"Nuclear","Doctrine & threats","Threat/doctrine escalation",70,0,100,"constructed","Kremlin doctrine 2024",3),
 (28,"Nuclear","Arms control","Treaty architecture intact",75,0,100,"constructed","New START lapsed 2026",1),
 (29,"Nuclear","Proliferation","Safeguards/verification loss",55,0,100,"constructed","IAEA Iran access lost",2),
 (30,"Nuclear","Expert composite","Doomsday Clock",85,1020,0,"seconds to midnight","Bulletin 2026",1),
 (31,"Conflict","Ukraine war","Combined casualties",2.0,0,10,"millions","2026 reporting",2),
 (32,"Conflict","NATO-Russia","Hostility & gray-zone escalation",60,0,100,"constructed","OSINT/NATO 2026",2),
 (33,"Conflict","Taiwan Strait","PLA ADIZ incursions",3000,100,12000,"aircraft/yr","Taiwan MND",2),
 (34,"Conflict","Middle East","Regional escalation state",40,0,100,"constructed","2026 reporting",2),
 (35,"Conflict","Global conflict","Active state-based conflicts",60,25,100,"conflicts","UCDP 2026",1),
 (36,"Economy","Debt","Global public debt",100,60,200,"% of GDP","IMF Fiscal Monitor 2026",1),
 (37,"Economy","Inflation","Global headline inflation",4.1,2.5,50,"%","IMF WEO 2026",2),
 (38,"Economy","Inequality","Top 1% wealth share",46,20,80,"%","World Inequality Lab",2),
 (39,"Economy","Trade fragmentation","US average effective tariff",16,3,40,"%","Yale Budget Lab 2026",1),
 (40,"Economy","Market fragility","Top-10 share of S&P 500",39,18,60,"%","2026 market data",2),
 (41,"Society","Democracy","Population living in autocracies",72,30,95,"%","V-Dem 2026",1),
 (42,"Society","Displacement","Forcibly displaced",1.5,0.5,10,"% of humanity","UNHCR 2026",1),
 (43,"Society","Press freedom","RSF global score",53.5,80,30,"index","RSF 2026",2),
 (44,"Society","Civil unrest","Population exposed to conflict",12.5,2,50,"%","ACLED",2),
 (45,"Society","Trust","Corruption Perceptions Index",43,70,20,"index","Transparency Intl 2026",2),
 (46,"Technology","AI capability","Frontier training compute (log)",26.7,24,29,"log10 FLOP","Epoch AI",2),
 (47,"Technology","AI & labour","Entry-level employment gap",-13,0,-100,"%","Stanford DEL 2026",1),
 (48,"Technology","Cyberattacks","Named ransomware victims",8000,500,100000,"per year","IT-ISAC 2026",2),
 (49,"Technology","Biosecurity","Verification & screening gaps",55,0,100,"constructed","BWC / IGSC",3),
 (50,"Technology","Orbital risk","Tracked debris >10cm",40000,10000,500000,"objects","ESA DISCOS 2026",2),
]

def score(cur,a0,a100):
    s=(cur-a0)/(a100-a0)*100
    return max(0.0,min(100.0,s))

rows=[]
for i,dom,topic,ind,cur,a0,a100,unit,src,conf in D:
    rows.append(dict(id=i,domain=dom,topic=topic,indicator=ind,current=cur,a0=a0,a100=a100,
                     unit=unit,source=src,confidence=conf,score=round(score(cur,a0,a100),1)))

doms={}
for r in rows: doms.setdefault(r["domain"],[]).append(r["score"])
dom_scores={k:round(sum(v)/len(v),1) for k,v in doms.items()}

flat=round(sum(r["score"] for r in rows)/len(rows),1)
dom_mean=round(sum(dom_scores.values())/len(dom_scores),1)

print(f"{'DOMAIN':<14}{'n':>3}{'mean':>8}")
for k,v in sorted(dom_scores.items(), key=lambda x:-x[1]):
    print(f"{k:<14}{len(doms[k]):>3}{v:>8.1f}")
print()
print(f"Unweighted mean of all 50 indicators : {flat}")
print(f"Mean of 8 domain means (equal domains): {dom_mean}")
print()
top=sorted(rows,key=lambda r:-r["score"])[:8]
print("HIGHEST-SCORING INDICATORS")
for r in top: print(f"  {r['score']:>5.1f}  {r['domain']:<12} {r['topic']} — {r['indicator']}")
print()
low=sorted(rows,key=lambda r:r["score"])[:5]
print("LOWEST-SCORING INDICATORS")
for r in low: print(f"  {r['score']:>5.1f}  {r['domain']:<12} {r['topic']} — {r['indicator']}")

json.dump(dict(indicators=rows,domains=dom_scores,flat=flat,dom_mean=dom_mean),
          open("index_data.json","w"),indent=1)
