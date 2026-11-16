# lusoapps-social

Social media robot for the SwimHeat, FlightHome and StormHome brand pages (Facebook + Instagram).

**Current stage: examples only.** `robot/social.py` reads each site's public data and writes the posts it *would*
publish to `examples/LATEST.md`. Nothing is published, and the examples job gets no page keys.

| Post | When | Data |
|---|---|---|
| SwimHeat — meets of the week | Monday | swimheat.app season lists (public live.swimrankings.net files) |
| SwimHeat — the weekend in numbers | Sunday evening | same; numbers only, never swimmers' names |
| StormHome — warnings | daily, only with orange/red warnings or a tropical cyclone | stormhome.app (MeteoAlarm CC BY 4.0, GDACS) |
| FlightHome — emergencies that landed | daily, only if there are any | flighthome.app emergency log (public ADS-B, adsb.lol ODbL) |

Workflows: `check.yml` (read-only check of the page keys), `examples.yml` (writes the examples; no secrets).

Rules: never print or commit the page keys; photos come from lusoapps.com/social/fotos (credits in that folder);
no children's faces, no third-party logos, no speculation about the cause of an emergency.
