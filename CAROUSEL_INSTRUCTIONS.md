# Iran Carousel — Claude Code Instructions

## Project: Instagram carousel export (Iran war analysis)

### Files
- `iran_carousel_v2.html` — the carousel (7 slides, 1080×1080px design)
- `export_carousel.py` — Playwright exporter → produces `output/slide_01.png` … `slide_07.png`

---

## Setup (one-time)

```bash
pip install playwright
playwright install chromium
```

---

## Export slides

```bash
cd ~/Documents/iran_maps
python export_carousel.py
```

Output: `./output/slide_01.png` through `slide_07.png` — 1080×1080px, ready for Instagram.

---

## Edit carousel content

Open `iran_carousel_v2.html`. Each slide is a `<div class="slide">` block with id `s1`–`s7`.

**Rules:**
- Max 2 short sentences per slide (the `.sentence` div)
- Keep the `.footer > .ft-note` to one citation line
- Do not change `--w:1080px` or `--scale` CSS variables — the exporter depends on them
- Google Fonts load via CDN — internet required at export time

---

## Slide map

| id | tag | key visual |
|----|-----|------------|
| s1 | cover | ICRI 1.8% · Persian star geometry |
| s2 | the players | 4-actor grid · payoff labels |
| s3 | the non-players | 90M+ big number · two-col boxes |
| s4 | why ceasefire fails | NE_lock 0.78 · 3 dyad rows |
| s5 | three missed windows | 2009 · 2019–22 · 2015 timeline |
| s6 | what the data shows | 53% vs 26% stat pair · Chenoweth |
| s7 | conclusion | Yes / NE grid · teal star geometry |

---

## Scientific sources cited

- Chenoweth & Stephan (2011) — *Why Civil Resistance Works* · Columbia UP
- Levitsky & Way (2010) — *Competitive Authoritarianism* · Cambridge UP
- Fortna (2004) — *Peace Time* · Princeton UP
- Reiter & Stam (2002) — *Democracies at War* · Princeton UP
- Abrahamian (2008) — *A History of Modern Iran* · Cambridge UP
- Bayat (2017) — *Revolution Without Revolutionaries* · Stanford UP
- Sheffer (2006) — *Diaspora Politics* · Cambridge UP
- ACLED — Armed Conflict Location & Event Data · acleddata.com
- HRANA — Human Rights Activists News Agency · en.hrana.org
- GDELT Project — gdeltproject.org

---

## Related projects in this folder

- `instructions_mountains.md` — Iranian Plateau / Alps topographic map project
- `iran_maps/` — artistic topographic visualization work

---

*Model: ICRI (Iran Conflict Resolution Index) + Nash equilibrium layer*
*ICRI_final = [0.35·(1−M) + 0.25·E + 0.20·L + 0.20·D] · (1 − 0.65·M) × (1 − NE_lock)*
*Current values: ICRI_adjusted = 8.4% · NE_lock = 0.78 · ICRI_final = 1.8%*
