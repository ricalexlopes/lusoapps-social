"""Images for the brand posts (1080x1350, Instagram portrait). No faces, no third-party logos.

flight_map(...)  FlightHome: the aircraft's track on a map, landing point marked (FlightHome colours)
storm_card(...)  StormHome: the list of orange/red warnings on the StormHome dark card
"""
import json, math, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, DPI = 1080, 1350, 100
_land = _borders = None

def _outlines():
    global _land, _borders
    if _land is None:
        _land = json.load(open(os.path.join(HERE, "assets", "land.json")))
        _borders = json.load(open(os.path.join(HERE, "assets", "borders.json")))
    return _land, _borders

# FlightHome colours (flighthome/app.css)
FH = {"navy": "#0B2545", "orange": "#E8590C", "paper": "#F5F1E8", "water": "#DCEBF2", "muted": "#475569", "line": "#C9D3DD", "green": "#146C43"}
# StormHome colours (stormhome/app.css)
SH = {"bg": "#0b1522", "text": "#e8eef6", "muted": "#93a4b8", "accent": "#ff8a3d", "red": "#ff5d5d", "orange": "#ff9f43", "line": "#1d2b3d"}

def _fig(bg):
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    fig.patch.set_facecolor(bg)
    return fig

def flight_map(tracks, title, lines, out_path):
    """tracks: [{'pts': [(lat, lon), ...], 'land': (lat, lon), 'label': 'RYR7RJ · DUB'}]  (pts may be just the first and last point)
    title: big headline, lines: 1-3 short lines under the map."""
    land, borders = _outlines()
    lats = [p[0] for t in tracks for p in t["pts"]] + [t["land"][0] for t in tracks]
    lons = [p[1] for t in tracks for p in t["pts"]] + [t["land"][1] for t in tracks]
    la0, la1, lo0, lo1 = min(lats), max(lats), min(lons), max(lons)
    # map box: square-ish on screen, with margin, at least ~4 degrees wide
    mlat = (la0 + la1) / 2
    k = max(math.cos(math.radians(mlat)), 0.2)
    span_lo = max((lo1 - lo0) * 1.35, (la1 - la0) * 1.35 / k * 1.25, 4.0)
    span_la = span_lo * k / 1.25
    clo, cla = (lo0 + lo1) / 2, (la0 + la1) / 2
    x0, x1, y0, y1 = clo - span_lo / 2, clo + span_lo / 2, cla - span_la / 2, cla + span_la / 2

    fig = _fig(FH["paper"])
    # header
    hd = fig.add_axes([0, 0.86, 1, 0.14]); hd.axis("off"); hd.set_xlim(0, 1); hd.set_ylim(0, 1)
    hd.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="square,pad=0", color=FH["navy"]))
    hd.text(0.05, 0.62, "FlightHome", color="white", fontsize=30, fontweight="bold", va="center")
    hd.text(0.05, 0.27, title, color="#FFD8C2", fontsize=19, fontweight="bold", va="center")
    hd.text(0.95, 0.62, " SQUAWK 7700 ", color="white", fontsize=15, fontweight="bold", ha="right", va="center",
            bbox=dict(boxstyle="round,pad=0.5", fc=FH["orange"], ec="none"))
    # map
    ax = fig.add_axes([0.04, 0.24, 0.92, 0.6])
    ax.set_facecolor(FH["water"]); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect(1 / k)
    for s in ("top", "right", "bottom", "left"):
        ax.spines[s].set_color(FH["line"])
    ax.set_xticks([]); ax.set_yticks([])
    for ring in land:
        xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
        if max(xs) < x0 - 5 or min(xs) > x1 + 5 or max(ys) < y0 - 5 or min(ys) > y1 + 5:
            continue
        ax.add_patch(Polygon(ring, closed=True, facecolor="white", edgecolor="#AFC4D3", linewidth=0.8))
    for ln in borders:
        xs = [p[0] for p in ln]; ys = [p[1] for p in ln]
        if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
            continue
        ax.plot(xs, ys, color="#C9D3DD", linewidth=0.8, zorder=2)
    for t in tracks:
        ys = [p[0] for p in t["pts"]]; xs = [p[1] for p in t["pts"]]
        full = len(t["pts"]) > 2
        ax.plot(xs, ys, color=FH["orange"], linewidth=4 if full else 3, linestyle="-" if full else (0, (4, 3)),
                solid_capstyle="round", zorder=4)
        ax.plot(xs[0], ys[0], "o", color="white", markeredgecolor=FH["orange"], markeredgewidth=3, markersize=11, zorder=5)
        ax.plot(t["land"][1], t["land"][0], "o", color=FH["green"], markeredgecolor="white", markeredgewidth=3, markersize=20, zorder=6)
        ax.annotate(t["label"], (t["land"][1], t["land"][0]), xytext=(14, 14), textcoords="offset points", fontsize=17,
                    fontweight="bold", color=FH["navy"], zorder=7,
                    bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=FH["line"]))
    # footer
    ft = fig.add_axes([0.05, 0.02, 0.9, 0.2]); ft.axis("off"); ft.set_xlim(0, 1); ft.set_ylim(0, 1)
    y = 0.86
    for i, l in enumerate(lines[:3]):
        ft.text(0, y, l, color=FH["navy"] if i == 0 else FH["muted"], fontsize=22 if i == 0 else 17,
                fontweight="bold" if i == 0 else "normal", va="top")
        y -= 0.26 if i == 0 else 0.21
    ft.text(0, 0.02, "flighthome.app", color=FH["orange"], fontsize=20, fontweight="bold", va="bottom")
    ft.text(1, 0.02, "ADS-B: adsb.lol (ODbL) · Map: Natural Earth", color=FH["muted"], fontsize=11, ha="right", va="bottom")
    fig.savefig(out_path, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path

def storm_card(date_label, rows, storms, out_path):
    """rows: [(country_en, n_red, n_orange, hazards_en)], storms: [(name, level)]"""
    fig = _fig(SH["bg"])
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.07, 0.93, "StormHome", color=SH["text"], fontsize=34, fontweight="bold", va="center")
    ax.text(0.07, 0.885, "Severe weather warnings in Europe", color=SH["accent"], fontsize=21, fontweight="bold", va="center")
    ax.text(0.07, 0.85, date_label + "  ·  number of regions with a warning", color=SH["muted"], fontsize=17, va="center")
    y = 0.79
    for country, nr, no, haz in rows[:9]:
        ax.add_patch(FancyBboxPatch((0.07, y - 0.035), 0.86, 0.06, boxstyle="round,pad=0.005,rounding_size=0.015",
                                    color="#13233a"))
        ax.text(0.1, y, country, color=SH["text"], fontsize=21, fontweight="bold", va="center")
        x = 0.5
        if nr:
            ax.text(x, y, f"● {nr} red", color=SH["red"], fontsize=17, fontweight="bold", va="center"); x += 0.16
        if no:
            ax.text(x, y, f"● {no} orange", color=SH["orange"], fontsize=17, fontweight="bold", va="center")
        ax.text(0.1, y - 0.022, haz, color=SH["muted"], fontsize=13, va="center")
        y -= 0.075
    if len(rows) > 9:
        ax.text(0.1, y + 0.01, f"+ {len(rows) - 9} more countries with orange warnings", color=SH["muted"], fontsize=15, va="center")
        y -= 0.05
    for name, lvl in storms[:2]:
        ax.text(0.1, y, f"Tropical cyclone {name} — {lvl} alert (GDACS)",
                color=SH["accent"], fontsize=17, fontweight="bold", va="center")
        y -= 0.045
    ax.text(0.07, 0.07, "stormhome.app", color=SH["accent"], fontsize=24, fontweight="bold", va="center")
    ax.text(0.07, 0.035, "Official warnings: MeteoAlarm (EUMETNET, CC BY 4.0) · GDACS. Always follow your local authorities.",
            color=SH["muted"], fontsize=11.5, va="center")
    fig.savefig(out_path, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path
