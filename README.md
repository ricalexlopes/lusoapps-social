# lusoapps-social

Social media robot for the SwimHeat, FlightHome and StormHome brand pages (Facebook + Instagram).

| Post | When | Data |
|---|---|---|
| SwimHeat — meets of the week (PT, lines in ES/EN) | Monday 19:00, from 23 Nov 2026 | swimheat.app season lists (public live.swimrankings.net files) |
| SwimHeat — the weekend in numbers | Sunday 21:00, from 29 Nov 2026 | same; numbers only, never swimmers' names |
| StormHome — warnings (EN, then PT) | 08:00, only with orange/red warnings or an orange/red tropical cyclone | stormhome.app (MeteoAlarm CC BY 4.0, GDACS) |
| FlightHome — 7700 landings (EN, then PT) | 09:00, only if any | flighthome.app emergency log + tracks (public ADS-B, adsb.lol ODbL) |

## How it works
- `robot/social.py examples` writes example posts (text + image) to `examples/` and `out/`. Publishes nothing.
- `robot/social.py collect` saves the tracks of 7700 landings to `traces/` every 2 hours (adsb.lol keeps ~24 h).
- `robot/publish.py` publishes **only** the posts placed in `approved/` (each once) and writes `approved/*.result.json`
  with the post ids. Nothing is published unless a post file is committed to `approved/`.
- Images are drawn by `robot/cards.py` (brand colours, no faces) or taken from lusoapps.com/social/fotos.
  Map outlines: Natural Earth (public domain).

Workflows: `check.yml` (read-only key check), `examples.yml`, `collect.yml` (no keys), `publish.yml` (keys, approved/ only).

Rules: never print or commit the page keys; no children's faces, no third-party logos; never post 7500/7600;
no speculation about the cause of an emergency.
