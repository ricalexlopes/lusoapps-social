#!/usr/bin/env python3
"""LusoApps social robot - writes the brand posts from each site's public data.

  python robot/social.py examples          write examples/LATEST.md + images (publishes nothing)
  python robot/social.py collect           FlightHome: save the tracks of today's 7700 landings (adsb.lol keeps ~24 h only)
  python robot/social.py prepare <kind>    write queue/<date>-<kind>.json + its image (publishes nothing)

Publishing is done only by robot/publish.py, for files placed in approved/ (see README).

Posts (kinds):
  swimheat-week    Monday 19:00: meets of the week in Portugal and Spain + deadlines (from 23 Nov 2026)
  swimheat-sunday  Sunday 21:00: the weekend in numbers (numbers only, never swimmers' names) (from 29 Nov 2026)
  stormhome        08:00, only with orange/red warnings in Europe or an orange/red tropical cyclone - English first
  flighthome       09:00, only if aircraft squawked 7700 yesterday and landed - English first, map of the track
"""
import json, math, os, sys, datetime as dt, urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import cards

UA = "LusoApps-social/0.2 (+https://lusoapps.com)"
TZ = ZoneInfo("Europe/Lisbon")
SWIM, STORM, FLIGHT = "https://swimheat.app", "https://stormhome.app", "https://flighthome.app"
RAW = "https://raw.githubusercontent.com/ricalexlopes/lusoapps-social/main/"
PHOTOS = "https://lusoapps.com/social/fotos/"
SWIM_PHOTOS = ["livres-de-cima.jpg", "mariposa-escuro.jpg", "livres-pistas-vertical.jpg", "drone-partida.jpg", "livres-prova.jpg",
               "subaquatica-nadador.jpg", "mariposa-prova.jpg", "mariposa-frente.jpg", "piscina-vazia-pistas.jpg", "subaquatica-pista.jpg"]
SWIM_START = {"swimheat-week": dt.date(2026, 11, 23), "swimheat-sunday": dt.date(2026, 11, 29)}

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"user-agent": UA, "accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def head_ok(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="HEAD", headers={"user-agent": UA}), timeout=15) as r:
            return r.status == 200
    except Exception:
        return False

MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MON_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
DIA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
DIA_ES = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

def d(s):
    return dt.date.fromisoformat(s[:10])

def span(a, b, es=False):
    A, B = d(a), d(b or a)
    dn, mn = (DIA_ES, MES_ES) if es else (DIA, MES)
    if A == B:
        return f"{dn[A.weekday()]} {A.day} {mn[A.month-1]}"
    return f"{dn[A.weekday()]} {A.day}–{dn[B.weekday()]} {B.day} {mn[B.month-1]}"

def title(s):
    """'LLIGA PROVINCIAL' -> 'Lliga Provincial' (some organisers write meet names in capitals)."""
    s = " ".join(s.split())
    if sum(c.isupper() for c in s) > 0.7 * max(1, sum(c.isalpha() for c in s)):
        small = {"de", "del", "la", "el", "y", "i", "e", "da", "do", "das", "dos", "of", "and"}
        w = s.lower().split()
        s = " ".join(x if (k and x in small) else x[:1].upper() + x[1:] for k, x in enumerate(w))
    return s

def photo(i):
    return PHOTOS + SWIM_PHOTOS[i % len(SWIM_PHOTOS)]

def outdir(day):
    p = os.path.join(ROOT, "out", day.isoformat())
    os.makedirs(p, exist_ok=True)
    return p

def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")

# ================================================================ SwimHeat
def swimheat_week(today):
    mon = today - dt.timedelta(days=today.weekday())
    sun = mon + dt.timedelta(days=6)
    lists = {n: get(f"{SWIM}/data/{n}.json") for n in ("POR", "ESP")}
    cal = get(f"{SWIM}/data/cal-POR.json").get("items", [])
    week = {n: sorted([m for m in L["meets"] if d(m["from"]) <= sun and d(m["to"]) >= mon and m.get("status") != "finished"],
                      key=lambda m: (m["from"], m["city"])) for n, L in lists.items()}
    dl = [c for c in cal if c.get("dl") and mon <= d(c["date"]) <= sun]
    if not week["POR"] and not week["ESP"] and not dl:
        return None
    t = [f"🏊 Esta semana no SwimHeat · {span(mon.isoformat(), sun.isoformat())}", ""]
    if week["POR"]:
        t.append("🇵🇹 Portugal")
        t += [f"• {span(m['from'], m['to'])} · {m['city']} — {title(m['name'])} ({m['course']})" for m in week["POR"]]
        t.append("")
    if week["ESP"]:
        t.append("🇪🇸 España")
        t += [f"• {span(m['from'], m['to'], es=True)} · {title(m['city'])} — {title(m['name'])} ({m['course']})" for m in week["ESP"]]
        t.append("")
    for c in dl:
        t.append(f"⏰ {span(c['date'], None)}: {c['name'].replace('PRAZO – ', 'último dia para os ')}")
    if dl:
        t.append("")
    t += ["Segue o teu nadador ao vivo: provas, tempos, lugares e mínimos no telemóvel. Grátis.",
          "Sigue a tu nadador en directo · Follow your swimmer live.",
          "📲 swimheat.app (link na bio)", "", "#natação #natacion #swimming #SwimHeat"]
    return {"brand": "swimheat", "kind": "swimheat-week", "when": "segunda-feira 19:00",
            "image_url": photo(mon.toordinal() // 7), "text": "\n".join(t)}

def swimheat_sunday(today):
    sun = today if today.weekday() == 6 else today - dt.timedelta(days=today.weekday() + 1)
    sat = sun - dt.timedelta(days=1)
    out = {}
    for n in ("POR", "ESP"):
        L = get(f"{SWIM}/data/{n}.json")
        meets = {m["id"]: m for m in L["meets"]}
        done = sorted([i for i in L.get("done", []) if i in meets], key=lambda i: meets[i]["from"])
        best, st = {}, {"meets": 0, "swims": 0, "sw": set(), "clubs": set(), "better": 0, "cities": []}
        for i in done:
            m = meets[i]
            if d(m["from"]) > sun:
                continue
            inwk = sat <= d(m["from"]) <= sun or sat <= d(m["to"]) <= sun
            try:
                R = get(f"{SWIM}/data/res/{i}.json")
            except Exception:
                continue
            if inwk:
                st["meets"] += 1; st["cities"].append(m["city"])
            pool = R.get("meet", {}).get("pool")
            for row in R.get("r", []):
                e, si, t, status = row[0], row[1], row[2], row[3]
                if not t or status:
                    continue
                ev = R["ev"].get(str(e), {})
                if ev.get("rc", 1) != 1:
                    continue
                s = R["sw"][si]
                key = (s[1], s[2], ev.get("d"), ev.get("s"), ev.get("g"), pool)
                if inwk:
                    st["swims"] += 1; st["sw"].add((s[1], s[2])); st["clubs"].add(s[3])
                    if key in best and t < best[key]:
                        st["better"] += 1
                if key not in best or t < best[key]:
                    best[key] = t
        out[n] = st
    p, e = out["POR"], out["ESP"]
    if not p["meets"] and not e["meets"]:
        return None
    t = [f"📊 O fim de semana em números · {span(sat.isoformat(), sun.isoformat())}", ""]
    if p["meets"]:
        t.append(f"🇵🇹 {p['meets']} provas ({', '.join(sorted(set(p['cities'])))})")
        t.append(f"   {len(p['sw'])} nadadores · {len(p['clubs'])} clubes · {p['swims']} tempos individuais")
        if p["better"]:
            t.append(f"   ⚡ {p['better']} vezes um nadador bateu o seu melhor tempo da época")
    if e["meets"]:
        t.append(f"🇪🇸 {e['meets']} competiciones ({', '.join(sorted(set(title(c) for c in e['cities'])))})")
        t.append(f"   {len(e['sw'])} nadadores · {len(e['clubs'])} clubes · {e['swims']} tiempos individuales")
    t += ["", "Todos os resultados, parciais e recordes pessoais na app. Grátis.",
          "Todos los resultados en la app · All results in the app.",
          "📲 swimheat.app (link na bio)", "", "#natação #natacion #swimming #SwimHeat"]
    return {"brand": "swimheat", "kind": "swimheat-sunday", "when": "domingo 21:00",
            "image_url": photo(sun.toordinal() // 7 + 5), "text": "\n".join(t),
            "note": "Só números, nunca nomes. 'Melhor tempo da época' compara com os tempos desta época que o SwimHeat tem (só Portugal)."}

# ================================================================ StormHome
COUNTRIES = {"andorra": ("Andorra", "Andorra"), "austria": ("Austria", "Áustria"), "belgium": ("Belgium", "Bélgica"),
             "bosnia-herzegovina": ("Bosnia", "Bósnia"), "bulgaria": ("Bulgaria", "Bulgária"), "croatia": ("Croatia", "Croácia"),
             "cyprus": ("Cyprus", "Chipre"), "czechia": ("Czechia", "Chéquia"), "denmark": ("Denmark", "Dinamarca"),
             "estonia": ("Estonia", "Estónia"), "finland": ("Finland", "Finlândia"), "france": ("France", "França"),
             "germany": ("Germany", "Alemanha"), "greece": ("Greece", "Grécia"), "hungary": ("Hungary", "Hungria"),
             "iceland": ("Iceland", "Islândia"), "ireland": ("Ireland", "Irlanda"), "israel": ("Israel", "Israel"),
             "italy": ("Italy", "Itália"), "latvia": ("Latvia", "Letónia"), "lithuania": ("Lithuania", "Lituânia"),
             "luxembourg": ("Luxembourg", "Luxemburgo"), "malta": ("Malta", "Malta"), "moldova": ("Moldova", "Moldávia"),
             "montenegro": ("Montenegro", "Montenegro"), "netherlands": ("Netherlands", "Países Baixos"), "norway": ("Norway", "Noruega"),
             "poland": ("Poland", "Polónia"), "portugal": ("Portugal", "Portugal"),
             "republic-of-north-macedonia": ("North Macedonia", "Macedónia do Norte"), "romania": ("Romania", "Roménia"),
             "serbia": ("Serbia", "Sérvia"), "slovakia": ("Slovakia", "Eslováquia"), "slovenia": ("Slovenia", "Eslovénia"),
             "spain": ("Spain", "Espanha"), "sweden": ("Sweden", "Suécia"), "switzerland": ("Switzerland", "Suíça"),
             "ukraine": ("Ukraine", "Ucrânia"), "united-kingdom": ("United Kingdom", "Reino Unido")}
HAZ = {"wind": ("wind", "vento"), "snow-ice": ("snow/ice", "neve/gelo"), "snow/ice": ("snow/ice", "neve/gelo"),
       "thunderstorm": ("thunderstorms", "trovoada"), "thunderstorms": ("thunderstorms", "trovoada"), "fog": ("fog", "nevoeiro"),
       "high-temperature": ("heat", "calor"), "extreme high temperature": ("heat", "calor"), "high temperature": ("heat", "calor"),
       "low-temperature": ("cold", "frio"), "extreme low temperature": ("cold", "frio"), "low temperature": ("cold", "frio"),
       "coastalevent": ("coastal", "agitação marítima"), "coastal event": ("coastal", "agitação marítima"),
       "forest-fire": ("fire risk", "incêndio"), "forest fire": ("fire risk", "incêndio"), "avalanches": ("avalanches", "avalanches"),
       "avalanche": ("avalanches", "avalanches"), "rain": ("rain", "chuva"), "flooding": ("flooding", "cheias"),
       "rain-flood": ("rain/flood", "chuva/cheias"), "flood": ("flooding", "cheias")}

def stormhome(today):
    rows, failed = [], 0
    for c, (en, pt) in COUNTRIES.items():
        try:
            W = get(f"{STORM}/api/warnings/eu/{c}")
        except Exception:
            failed += 1
            continue
        red = [w for w in W if w.get("l") == 4]
        orange = [w for w in W if w.get("l") == 3]
        if not red and not orange:
            continue
        hz = sorted({HAZ.get(w.get("t", "").lower(), (w.get("t", "").lower(),) * 2) for w in red + orange})
        rows.append({"en": en, "pt": pt, "red": len({w["e"] for w in red}), "orange": len({w["e"] for w in orange}),
                     "hz_en": ", ".join(sorted({h[0] for h in hz})), "hz_pt": ", ".join(sorted({h[1] for h in hz}))})
    try:
        S = get(f"{STORM}/api/storms").get("features", [])
    except Exception:
        S = []
    storms = [f["properties"] for f in S if f.get("properties", {}).get("alertlevel") in ("Orange", "Red")]
    if not rows and not storms:
        return None
    rows.sort(key=lambda r: (-r["red"], -r["orange"], r["en"]))
    en_date = f"{today.day} {MONTH_EN[today.month-1]} {today.year}"
    t = [f"⚠️ Severe weather warnings in Europe · {today.day} {MON_EN[today.month-1]}", ""]
    for r in rows[:10]:
        lv = ([f"🔴 {r['red']} red"] if r["red"] else []) + ([f"🟠 {r['orange']} orange"] if r["orange"] else [])
        t.append(f"• {r['en']}: {' · '.join(lv)} — {r['hz_en']}")
    if len(rows) > 10:
        t.append(f"• + {len(rows) - 10} more countries with orange warnings")
    for s in storms[:3]:
        t.append(f"🌀 Tropical cyclone {s.get('name','')} — {'red' if s.get('alertlevel') == 'Red' else 'orange'} alert (GDACS)")
    t += ["(number of regions with a warning)", "", "🇵🇹 Avisos laranja e vermelhos na Europa hoje:"]
    for r in rows[:10]:
        lv = ([f"🔴 {r['red']}"] if r["red"] else []) + ([f"🟠 {r['orange']}"] if r["orange"] else [])
        t.append(f"• {r['pt']}: {' · '.join(lv)} — {r['hz_pt']}")
    t += ["", "Official warnings on a live map, alerts for your area and your trip: stormhome.app (link in bio)",
          "Avisos oficiais no mapa e alertas para a tua zona e para a tua viagem.",
          "", "Sources: MeteoAlarm (EUMETNET, CC BY 4.0), GDACS. Always follow your local authorities and weather service.",
          "", "#StormHome #weather #severeweather #meteo"]
    img = cards.storm_card(en_date, [(r["en"], r["red"], r["orange"], r["hz_en"]) for r in rows],
                           [(s.get("name", ""), "red" if s.get("alertlevel") == "Red" else "orange") for s in storms],
                           os.path.join(outdir(today), "stormhome.png"))
    return {"brand": "stormhome", "kind": "stormhome", "when": "todos os dias às 08:00 (só se houver laranja/vermelho ou ciclone)",
            "image": rel(img), "text": "\n".join(t), "note": (f"{failed} países não responderam nesta leitura." if failed else "")}

# ================================================================ FlightHome
def km(a, b, c, e):
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(e - b) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(x))

_airports = None
def airports():
    global _airports
    if _airports is None:
        _airports = [a for a in get(f"{FLIGHT}/data/airports.json") if a[7] and a[7] >= 1]
    return _airports

def nearest_airport(la, lo, maxkm=15):
    best = min(airports(), key=lambda a: km(la, lo, a[5], a[6]))
    return best if km(la, lo, best[5], best[6]) <= maxkm else None

def landed_7700(day):
    """Entries of the FlightHome emergency log for a UTC day that squawked 7700, were seen 2+ times and stopped on the
    ground near a known airport. 7600 (radio failure) and 7500 are never posted."""
    L = get(f"{FLIGHT}/api/emglog?day={day.isoformat()}").get("list", [])
    out = []
    for e in L:
        if e.get("q") != "7700" and "7700" not in (e.get("qs") or []):
            continue
        last = e.get("last") or {}
        on_ground = last.get("g") == 1 or ((last.get("al") or 99999) <= 300 and (last.get("s") or 999) <= 60)
        if not on_ground or e.get("n", 0) < 2 or last.get("la") is None:
            continue
        ap = nearest_airport(last["la"], last["lo"])
        if ap:
            out.append((e, ap))
    return out, len(L)

def trace_path(day, hexid):
    return os.path.join(ROOT, "traces", day.isoformat(), hexid.lower() + ".json")

LOG = []
def log(*a):
    LOG.append(" ".join(str(x) for x in a)); print(*a)

def collect():
    """Save the tracks of 7700 landings of today and yesterday (UTC) while adsb.lol still has them."""
    now = dt.datetime.now(dt.timezone.utc)
    saved = 0
    for day in (now.date(), now.date() - dt.timedelta(days=1)):
        try:
            landed, _ = landed_7700(day)
        except Exception as ex:
            log("emglog", day, type(ex).__name__, str(ex)[:120])
            continue
        log("day", day, "7700 landed:", [e.get("f") or e["h"] for e, _ in landed])
        for e, ap in landed:
            p = trace_path(day, e["h"])
            if os.path.exists(p):
                continue
            try:
                T = get(f"{FLIGHT}/api/trace?hex={e['h']}")
            except Exception as ex:
                log("trace", e["h"], type(ex).__name__, str(ex)[:160])
                continue
            if not T.get("pts"):
                log("trace", e["h"], "no points", str(T.get("error", ""))[:160])
                continue
            os.makedirs(os.path.dirname(p), exist_ok=True)
            json.dump({"hex": e["h"], "r": T.get("r", ""), "t": T.get("t", ""), "desc": T.get("desc", ""), "from": T.get("from", 0),
                       "pts": T["pts"]}, open(p, "w"), separators=(",", ":"))
            saved += 1
    # keep 10 days of tracks
    base = os.path.join(ROOT, "traces")
    if os.path.isdir(base):
        cut = (now.date() - dt.timedelta(days=10)).isoformat()
        for dd in os.listdir(base):
            if dd < cut:
                for f in os.listdir(os.path.join(base, dd)):
                    os.remove(os.path.join(base, dd, f))
                os.rmdir(os.path.join(base, dd))
    log(f"collect: {saved} new tracks")
    os.makedirs(os.path.join(ROOT, "examples"), exist_ok=True)
    open(os.path.join(ROOT, "examples", "collect-log.txt"), "w").write(now.isoformat(timespec="seconds") + "\n" + "\n".join(LOG) + "\n")

def flight_leg(T, land_ms):
    """From a saved track, the flight that ends at the landing nearest to land_ms: (points [(lat, lon)], landing time UTC)."""
    pts, t0 = T["pts"], T.get("from", 0)
    if not pts:
        return None, None
    abs_t = lambda p: (t0 + p[0]) * 1000
    # landing = first ground point after an airborne point, nearest to the time the log last saw the aircraft
    landings = [i for i in range(1, len(pts)) if pts[i][3] == -1 and pts[i - 1][3] not in (-1, None)]
    if not landings:
        return None, None
    li = min(landings, key=lambda i: abs(abs_t(pts[i]) - land_ms))
    if abs(abs_t(pts[li]) - land_ms) > 3 * 3600e3:
        return None, None
    si = li - 1
    while si > 0 and pts[si - 1][3] != -1 and (pts[si][0] - pts[si - 1][0]) < 1800:
        si -= 1
    leg = [(p[1], p[2]) for p in pts[si:li + 1]]
    when = dt.datetime.fromtimestamp(abs_t(pts[li]) / 1000, dt.timezone.utc)
    return leg, when

def ac_name(e, T):
    desc = (T or {}).get("desc") or ""
    if desc:
        w = desc.split()
        return " ".join(x if any(ch.isdigit() for ch in x) else x.capitalize() for x in w)
    return e.get("t") or ""

def flighthome(day):
    """Post about `day` (UTC): aircraft that squawked 7700 and landed."""
    landed, total = landed_7700(day)
    if not landed:
        return None
    items = []
    for e, ap in landed:
        T = None
        p = trace_path(day, e["h"])
        if os.path.exists(p):
            T = json.load(open(p))
        leg, when = flight_leg(T, (e.get("last") or {}).get("t", 0)) if T else (None, None)
        who = e.get("f") or e.get("r") or e["h"].upper()
        items.append({"who": who, "type": ac_name(e, T), "code": e.get("t", ""), "ap": ap, "leg": leg, "when": when, "e": e})
    items.sort(key=lambda x: (x["leg"] is None, x["when"] or dt.datetime.max.replace(tzinfo=dt.timezone.utc)))
    head = f"{day.day} {MON_EN[day.month-1]} {day.year}"
    t = [f"✈️ Emergency landings · {head}", ""]
    for x in items[:8]:
        at = f" at {x['when'].strftime('%H:%M')} UTC" if x["when"] else ""
        typ = f" ({x['type']})" if x["type"] else ""
        t.append(f"• {x['who']}{typ} squawked 7700 and landed{at} in {x['ap'][3]} ({x['ap'][1] or x['ap'][0]})")
    if len(items) > 8:
        t.append(f"• + {len(items) - 8} more")
    t += ["", "Squawk 7700 asks air traffic control for priority — for medical, technical or precautionary reasons. We don't know the cause of each case.",
          "", f"🇵🇹 Aterragens de emergência · {day.day} {MES[day.month-1]}"]
    for x in items[:8]:
        at = f" às {x['when'].strftime('%H:%M')} UTC" if x["when"] else ""
        typ = f" ({x['code']})" if x["code"] else ""
        t.append(f"• {x['who']}{typ} declarou 7700 e aterrou{at} em {x['ap'][3]} ({x['ap'][1] or x['ap'][0]})")
    t += ["O código 7700 pede prioridade ao controlo aéreo — por razões médicas, técnicas ou por precaução. Não sabemos a causa de cada caso.",
          "", "Follow flights live · Segue os voos ao vivo: flighthome.app (link in bio)",
          "Public ADS-B data: adsb.lol (ODbL).", "", "#FlightHome #aviation #avgeek #squawk7700"]
    # map: the first case with a full track (else the first case, first/last log points, dashed)
    x = items[0]
    pts = x["leg"] or [((x["e"].get("first") or {}).get("la"), (x["e"].get("first") or {}).get("lo")),
                       ((x["e"].get("last") or {}).get("la"), (x["e"].get("last") or {}).get("lo"))]
    pts = [p for p in pts if p[0] is not None]
    at = f" at {x['when'].strftime('%H:%M')} UTC" if x["when"] else ""
    lines = [f"{x['who']}{' (' + x['type'] + ')' if x['type'] else ''} landed{at}",
             f"in {x['ap'][3]} ({x['ap'][1] or x['ap'][0]}) after squawking 7700",
             (f"+ {len(items) - 1} more emergency landing{'s' if len(items) > 2 else ''} that day" if len(items) > 1 else
              "Track from public ADS-B data")]
    img = cards.flight_map([{"pts": pts, "land": (x["ap"][5], x["ap"][6]), "label": f"{x['who']} · {x['ap'][1] or x['ap'][0]}"}],
                           f"Emergency landings · {head}", lines, os.path.join(outdir(day), "flighthome.png"))
    note = (f"{total} aviões no registo do dia; {len(items)} com 7700, vistos 2+ vezes e parados a menos de 15 km de um aeroporto. "
            f"Percurso no mapa: {'completo' if x['leg'] else 'só o primeiro e o último ponto (linha tracejada)'}.")
    return {"brand": "flighthome", "kind": "flighthome", "when": "todos os dias às 09:00 (só se houver casos)",
            "image": rel(img), "text": "\n".join(t), "note": note}

# ================================================================ commands
def build(kind, today):
    if kind == "swimheat-week":
        return swimheat_week(today)
    if kind == "swimheat-sunday":
        return swimheat_sunday(today)
    if kind == "stormhome":
        return stormhome(today)
    if kind == "flighthome":
        return flighthome(dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1))
    raise SystemExit("unknown kind " + kind)

def prepare(kind):
    today = dt.datetime.now(TZ).date()
    if kind in SWIM_START and today < SWIM_START[kind]:
        print(f"{kind}: starts on {SWIM_START[kind]}"); return
    p = build(kind, today)
    if not p:
        print(f"{kind}: nothing to post today"); return
    os.makedirs(os.path.join(ROOT, "queue"), exist_ok=True)
    f = os.path.join(ROOT, "queue", f"{today.isoformat()}-{kind}.json")
    json.dump(p, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("prepared", rel(f))

def examples():
    now = dt.datetime.now(TZ)
    today = now.date()
    parts = ["# Exemplos do robô de redes sociais", "",
             f"Gerado a {now.strftime('%d/%m/%Y %H:%M')} (hora de Lisboa) com dados reais. **Nada foi publicado.**", ""]
    ex_dir = os.path.join(ROOT, "examples")
    os.makedirs(ex_dir, exist_ok=True)
    jobs = [("SwimHeat — provas da semana", lambda: swimheat_week(today)),
            ("SwimHeat — resumo de domingo", lambda: swimheat_sunday(today)),
            ("StormHome — avisos", lambda: stormhome(today))]
    # FlightHome: yesterday, else today so far (UTC), so there is something to look at
    utc = dt.datetime.now(dt.timezone.utc).date()
    jobs.append((f"FlightHome — aterragens de emergência (7700) de {utc - dt.timedelta(days=1)}",
                 lambda: flighthome(utc - dt.timedelta(days=1))))
    jobs.append((f"FlightHome — aterragens de emergência (7700) de hoje, {utc} (até agora)",
                 lambda: dict(flighthome(utc) or {}, kind="flighthome-today") or None))
    for name, fn in jobs:
        parts.append(f"## {name}")
        try:
            p = fn()
        except Exception as ex:
            parts += [f"_Sem dados nesta leitura ({type(ex).__name__}: {str(ex)[:120]})._", ""]
            continue
        if not p or not p.get("text"):
            parts += ["_Hoje não publicaria nada (sem conteúdo para este tipo de publicação)._", ""]
            continue
        if p.get("image"):
            img = f"![imagem]({'../' + p['image']})"
            ph = p["image"]
        else:
            ph = p["image_url"] + (" ✅" if head_ok(p["image_url"]) else " ⚠️ (imagem não encontrada)")
            img = f"![imagem]({p['image_url']})"
        parts += [f"- **Quando:** {p['when']}", "- **Onde:** Facebook + Instagram", f"- **Imagem:** {ph}"]
        if p.get("note"):
            parts.append(f"- **Nota:** {p['note']}")
        parts += ["", img, "", "```", p["text"], "```", ""]
        json.dump(p, open(os.path.join(ex_dir, p["kind"] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    out = "\n".join(parts)
    open(os.path.join(ex_dir, "LATEST.md"), "w", encoding="utf-8").write(out)
    print(out)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "examples"
    if cmd == "examples":
        examples()
    elif cmd == "collect":
        collect()
    elif cmd == "prepare":
        prepare(sys.argv[2])
    else:
        raise SystemExit(__doc__)
