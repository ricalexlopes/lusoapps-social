#!/usr/bin/env python3
"""LusoApps social robot - writes the brand posts from each site's public data.

This version only WRITES EXAMPLES (examples/LATEST.md). It publishes nothing and uses no page keys.

Posts:
  swimheat-week    Monday: meets of the week in Portugal and Spain + deadlines for qualifying times
  swimheat-sunday  Sunday evening: summary of the weekend (numbers only, never swimmers' names)
  stormhome        Daily, only when there are orange/red warnings in Europe or an active tropical cyclone
  flighthome       Daily: aircraft that declared an emergency yesterday (7700/7600) and landed

Data: swimheat.app/data (season lists built from public live.swimrankings.net files),
stormhome.app/api (MeteoAlarm, CC BY 4.0; GDACS), flighthome.app/api/emglog (public ADS-B data, adsb.lol, ODbL).
"""
import json, math, sys, datetime as dt, urllib.request, urllib.error
from zoneinfo import ZoneInfo

UA = "LusoApps-social/0.1 (+https://lusoapps.com)"
TZ = ZoneInfo("Europe/Lisbon")
SWIM, STORM, FLIGHT = "https://swimheat.app", "https://stormhome.app", "https://flighthome.app"
PHOTOS = "https://lusoapps.com/social/fotos/"
SWIM_PHOTOS = ["livres-de-cima.jpg", "mariposa-escuro.jpg", "livres-pistas-vertical.jpg", "drone-partida.jpg", "livres-prova.jpg",
               "subaquatica-nadador.jpg", "mariposa-prova.jpg", "mariposa-frente.jpg", "piscina-vazia-pistas.jpg", "subaquatica-pista.jpg"]

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"user-agent": UA, "accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def head_ok(url):
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"user-agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception:
        return False

MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
DIA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
DIA_ES = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

def d(s):
    return dt.date.fromisoformat(s[:10])

def span(a, b, es=False):
    """'sáb 21–dom 22 nov' / 'sáb 21 nov'"""
    A, B = d(a), d(b or a)
    dn, mn = (DIA_ES, MES_ES) if es else (DIA, MES)
    if A == B:
        return f"{dn[A.weekday()]} {A.day} {mn[A.month-1]}"
    return f"{dn[A.weekday()]} {A.day}–{dn[B.weekday()]} {B.day} {mn[B.month-1]}"

def title(s):
    """Meet names come in capitals from some organisers: 'LLIGA PROVINCIAL' -> 'Lliga Provincial'."""
    s = " ".join(s.split())
    if sum(c.isupper() for c in s) > 0.7 * sum(c.isalpha() for c in s):
        small = {"de", "del", "la", "el", "y", "i", "e", "da", "do", "das", "dos"}
        w = s.lower().split()
        s = " ".join(x if (k and x in small) else x[:1].upper() + x[1:] for k, x in enumerate(w))
    return s

def photo(i):
    return PHOTOS + SWIM_PHOTOS[i % len(SWIM_PHOTOS)]

# ---------------------------------------------------------------- SwimHeat: the week
def swimheat_week(today):
    mon = today - dt.timedelta(days=today.weekday())
    sun = mon + dt.timedelta(days=6)
    lists = {n: get(f"{SWIM}/data/{n}.json") for n in ("POR", "ESP")}
    cal = get(f"{SWIM}/data/cal-POR.json").get("items", [])
    week = {}
    for n, L in lists.items():
        week[n] = sorted([m for m in L["meets"] if d(m["from"]) <= sun and d(m["to"]) >= mon and m.get("status") != "finished"],
                         key=lambda m: (m["from"], m["city"]))
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
    return {"brand": "SwimHeat", "when": "segunda-feira 19:00", "where": "Facebook + Instagram",
            "photo": photo(mon.toordinal() // 7), "text": "\n".join(t)}

# ---------------------------------------------------------------- SwimHeat: the weekend in numbers
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
            inwk = sat <= d(m["from"]) <= sun or sat <= d(m["to"]) <= sun
            if d(m["from"]) > sun:
                continue
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
                if ev.get("rc", 1) != 1:  # individual events only
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
    return {"brand": "SwimHeat", "when": "domingo 21:00", "where": "Facebook + Instagram",
            "photo": photo(sun.toordinal() // 7 + 5), "text": "\n".join(t),
            "note": "Só números, nunca nomes. 'Melhor tempo da época' compara com os tempos que o SwimHeat tem desta época (só Portugal, onde temos a época completa)."}

# ---------------------------------------------------------------- StormHome
COUNTRIES = {"andorra": "Andorra", "austria": "Áustria", "belgium": "Bélgica", "bosnia-herzegovina": "Bósnia", "bulgaria": "Bulgária",
             "croatia": "Croácia", "cyprus": "Chipre", "czechia": "Chéquia", "denmark": "Dinamarca", "estonia": "Estónia", "finland": "Finlândia",
             "france": "França", "germany": "Alemanha", "greece": "Grécia", "hungary": "Hungria", "iceland": "Islândia", "ireland": "Irlanda",
             "israel": "Israel", "italy": "Itália", "latvia": "Letónia", "lithuania": "Lituânia", "luxembourg": "Luxemburgo", "malta": "Malta",
             "moldova": "Moldávia", "montenegro": "Montenegro", "netherlands": "Países Baixos", "norway": "Noruega", "poland": "Polónia",
             "portugal": "Portugal", "republic-of-north-macedonia": "Macedónia do Norte", "romania": "Roménia", "serbia": "Sérvia",
             "slovakia": "Eslováquia", "slovenia": "Eslovénia", "spain": "Espanha", "sweden": "Suécia", "switzerland": "Suíça",
             "ukraine": "Ucrânia", "united-kingdom": "Reino Unido"}
HAZ = {"wind": "vento", "snow-ice": "neve/gelo", "snow/ice": "neve/gelo", "thunderstorm": "trovoada", "fog": "nevoeiro",
       "high-temperature": "calor", "extreme high temperature": "calor", "low-temperature": "frio", "extreme low temperature": "frio",
       "coastalevent": "agitação marítima", "coastal event": "agitação marítima", "forest-fire": "incêndio", "forest fire": "incêndio",
       "avalanches": "avalanches", "avalanche": "avalanches", "rain": "chuva", "flooding": "cheias", "rain-flood": "chuva/cheias", "flood": "cheias"}

def stormhome(today):
    rows, failed = [], 0
    for c, nome in COUNTRIES.items():
        try:
            W = get(f"{STORM}/api/warnings/eu/{c}")
        except Exception:
            failed += 1
            continue
        now = dt.datetime.now(dt.timezone.utc)
        red = [w for w in W if w.get("l") == 4]
        orange = [w for w in W if w.get("l") == 3]
        if not red and not orange:
            continue
        haz = sorted({HAZ.get(w.get("t", "").lower(), w.get("t", "").lower()) for w in red + orange})
        rows.append((len(red), len({w["e"] for w in red}), len({w["e"] for w in orange}), nome, haz))
    try:
        S = get(f"{STORM}/api/storms").get("features", [])
    except Exception:
        S = []
    storms = [f["properties"] for f in S if f.get("properties", {}).get("alertlevel") in ("Orange", "Red")]
    if not rows and not storms:
        return None
    rows.sort(key=lambda r: (-r[0], -r[1], -r[2], r[3]))
    t = [f"⚠️ Avisos meteorológicos na Europa · {today.day} {MES[today.month-1]}", ""]
    for nred, rred, rora, nome, haz in rows[:10]:
        lvl = []
        if rred: lvl.append(f"🔴 {rred} região{'ões' if rred > 1 else ''}")
        if rora: lvl.append(f"🟠 {rora} região{'ões' if rora > 1 else ''}")
        t.append(f"• {nome}: {' · '.join(lvl)} — {', '.join(haz)}")
    if len(rows) > 10:
        t.append(f"• e mais {len(rows) - 10} países com aviso laranja")
    for s in storms[:3]:
        t.append(f"🌀 {s.get('name','')} — alerta {'vermelho' if s.get('alertlevel') == 'Red' else 'laranja'} (GDACS)")
    t += ["", "Segue os avisos oficiais no mapa e recebe alertas para a tua zona e para a tua viagem.",
          "Official warnings on a live map · stormhome.app (link na bio)",
          "", "Fontes: MeteoAlarm (EUMETNET, CC BY 4.0), GDACS. Segue sempre as indicações da proteção civil e do serviço meteorológico do teu país.",
          "", "#StormHome #meteo #weather #avisos"]
    return {"brand": "StormHome", "when": "todos os dias às 08:00, só quando há laranja/vermelho ou ciclone", "where": "Facebook + Instagram",
            "photo": "imagem do globo com os avisos (a gerar a partir do site) ou foto da biblioteca StormHome",
            "text": "\n".join(t), "note": (f"{failed} países não responderam nesta leitura." if failed else "")}

# ---------------------------------------------------------------- FlightHome
def haversine(a, b, c, e):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = p2 - p1, math.radians(e - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))

def flighthome(today):
    day = today - dt.timedelta(days=1)
    L = get(f"{FLIGHT}/api/emglog?day={day.isoformat()}").get("list", [])
    try:
        AP = [a for a in get(f"{FLIGHT}/data/airports.json") if a[7] and a[7] >= 1]
    except Exception:
        AP = []
    landed = []
    for e in L:
        q = e.get("q", "")
        if q not in ("7700", "7600"):  # 7500 (hijack) is never posted: often a wrong code, and too sensitive
            continue
        last = e.get("last") or {}
        on_ground = last.get("g") == 1 or ((last.get("al") or 99999) <= 300 and (last.get("s") or 999) <= 60)
        if not on_ground or e.get("n", 0) < 2:  # seen at least twice, so a one-off wrong code is left out
            continue
        ap = None
        if AP and last.get("la") is not None:
            best = min(AP, key=lambda a: haversine(last["la"], last["lo"], a[5], a[6]))
            if haversine(last["la"], last["lo"], best[5], best[6]) <= 15:
                ap = best
        if not ap:  # landed somewhere we cannot name with confidence: leave it out
            continue
        landed.append((e, ap))
    if not landed:
        return None
    t = [f"✈️ Emergências de ontem que terminaram em terra · {day.day} {MES[day.month-1]}", ""]
    for e, ap in landed[:8]:
        who = e.get("f") or e.get("r") or e.get("h", "").upper()
        typ = f" ({e['t']})" if e.get("t") else ""
        code = "7700 emergência" if e.get("q") == "7700" else "7600 falha de rádio"
        t.append(f"• {who}{typ} — aterrou em {ap[3]} ({ap[1] or ap[0]}) · código {code}")
    if len(landed) > 8:
        t.append(f"• e mais {len(landed) - 8}")
    t += ["", "Os pilotos marcam 7700 sempre que precisam de prioridade — muitas vezes por um passageiro doente ou por precaução.",
          "Yesterday's emergency squawks that ended on the ground · flighthome.app (link na bio)",
          "", "Dados ADS-B públicos (adsb.lol, ODbL). Sem especulação sobre causas.",
          "", "#FlightHome #aviation #avgeek #squawk7700"]
    return {"brand": "FlightHome", "when": "todos os dias às 09:00 (só se houver casos)", "where": "Facebook + Instagram",
            "photo": "mapa FlightHome com os pontos de aterragem (a gerar) ou foto da biblioteca FlightHome",
            "text": "\n".join(t),
            "note": f"{len(L)} aviões no registo de ontem; {len(landed)} com 7700/7600, vistos 2+ vezes e parados a menos de 15 km de um aeroporto conhecido."}

# ---------------------------------------------------------------- examples
def main():
    now = dt.datetime.now(TZ)
    today = now.date()
    parts = [f"# Exemplos do robô de redes sociais", "",
             f"Gerado a {now.strftime('%d/%m/%Y %H:%M')} (hora de Lisboa) com dados reais. **Nada foi publicado.**", ""]
    for name, fn in (("SwimHeat — provas da semana", swimheat_week), ("SwimHeat — resumo de domingo", swimheat_sunday),
                     ("StormHome — avisos", stormhome), ("FlightHome — emergências que aterraram", flighthome)):
        parts.append(f"## {name}")
        try:
            p = fn(today)
        except Exception as ex:
            parts += [f"_Sem dados nesta leitura ({type(ex).__name__}: {str(ex)[:120]})._", ""]
            continue
        if not p:
            parts += ["_Hoje não publicaria nada (sem conteúdo para este tipo de publicação)._", ""]
            continue
        ph = p["photo"]
        ok = (" ✅" if head_ok(ph) else " ⚠️ (imagem não encontrada)") if ph.startswith("http") else ""
        parts += [f"- **Quando:** {p['when']}", f"- **Onde:** {p['where']}", f"- **Imagem:** {ph}{ok}"]
        if p.get("note"):
            parts.append(f"- **Nota:** {p['note']}")
        parts += ["", "```", p["text"], "```", ""]
    out = "\n".join(parts)
    import os
    os.makedirs("examples", exist_ok=True)
    with open("examples/LATEST.md", "w", encoding="utf-8") as f:
        f.write(out)
    print(out)

if __name__ == "__main__":
    sys.exit(main())
