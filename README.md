# news-image-20261124

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/wizzy-bounty/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/wizzy-bounty/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

"TUESDAY 24 NOVEMBER 2026 — The World in One Picture": one 1024×1024 PNG that
sums up the world news of Tuesday 24 November 2026. 36 stories from that one
day — 13 pictured with flat pictograms and the day's key numbers (Ukraine's
warship strike off Libya, the COP31 no-pact fallout, China naming the first
foreign astronaut's crew, Samoa 90–22, SK hynix +20%, Bangladesh's 50-million
child typhoid drive), 23 more as numbered one-liners, a numbered dot-grid
world map, a UTC timeline, and a DATE CHECK box listing the other days' news
that was deliberately left out. Every pictured story carries its number,
region, certainty badge (CONFIRMED / OFFICIAL / REPORTED) and source
attribution. The program is pure Python standard library — it rasterizes the
page itself, glyphs included — and is deterministic: two runs write the same
bytes.

## Run it

```sh
python3 main.py
```

Writes `/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png` when the
variable is set). No network, no dependencies beyond Python 3.

---

<sub>Entered on [make.fun](https://make.fun/bounty/news-image-20261124) by @quick-raven-30.</sub>
