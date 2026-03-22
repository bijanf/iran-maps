# INSTRUCTIONS: Iran Missile Range — Instagram Carousel Post

## Overview
Create a 2-slide Instagram carousel post (1080x1080 px each) about Iran's newly demonstrated
4,000 km ballistic missile capability. The post is urgent and alarming in tone.
Output: one Python script (`generate_slides.py`) that produces two PNG files.

---

## Slide 1 — The Map

**File:** `slide_1_map.png`

### Visual requirements
- Canvas: **1080 x 1080 px**, background color `#0d0d0d` (near-black)
- Use `matplotlib` + `cartopy` (projection: `PlateCarree` or `Orthographic` centered on Iran)
- Map extent: show Europe, Middle East, North Africa, Central Asia

### Map layers (in order)
1. **Ocean fill:** `#0d0d0d`
2. **Land fill:** `#1a1a2e` (dark navy)
3. **Country borders:** `#2e2e4a`, linewidth 0.4
4. **Coastlines:** `#2e2e4a`, linewidth 0.5

### Strike radius circle
- Center: Tehran, Iran → `(35.6892° N, 51.3890° E)`
- Radius: **4,000 km** (geodesic — use `pyproj` or `geopy` to compute the circle polygon)
- Fill: red with alpha `0.12`
- Border: `#ff2a2a`, linewidth 1.8, linestyle `--`

### Markers
| City | Coords | Style |
|------|--------|-------|
| Tehran | 35.69°N, 51.39°E | Red dot `#ff2a2a`, size 80 |
| Berlin | 52.52°N, 13.40°E | Orange dot `#ff6600`, size 60 |
| Paris | 48.85°N, 2.35°E | Orange dot `#ff6600`, size 60 |
| Rome | 41.90°N, 12.50°E | Orange dot `#ff6600`, size 60 |
| London | 51.51°N, -0.13°E | Orange dot `#ff6600`, size 60 |
| Moscow | 55.75°N, 37.62°E | Yellow dot `#ffdd00`, size 50 |

Label each city in white, font size 9, offset slightly above the dot.
Label Tehran in red `#ff2a2a`, font size 11, bold.

### Text overlays on slide 1
- **Top-left corner:**
  ```
  ☢  IRAN STRIKE RADIUS
  ```
  Font: bold, size 22, color `#ff2a2a`

- **Bottom strip** (semi-transparent black bar, full width, height ~100px):
  ```
  Demonstrated range: 4,000 km  |  Source: IDF, WSJ, CNN — March 21, 2026
  ```
  Font: size 13, color `#aaaaaa`

- **Large annotation line** from Tehran dot pointing toward Berlin:
  - Dashed orange line `#ff6600`
  - Label: `~3,800 km` near midpoint, white, font size 10

---

## Slide 2 — Text Post (Bilingual)

**File:** `slide_2_text.png`

### Layout
- Canvas: **1080 x 1080 px**, background `#0d0d0d`
- Two vertical halves separated by a thin vertical line `#ff2a2a` at x=540

### Left half — English
**Headline (alarming, bold):**
```
🚨 BERLIN IS IN RANGE.
```
Color: `#ff2a2a`, font size 36, bold

**Body text:**
```
On March 21, 2026, Iran fired a
ballistic missile at a US-UK base
4,000 km away — the same distance
as Berlin.

Europe has no sovereign missile
defense system capable of stopping
an Iranian IRBM.

❓ WHO IS PROTECTING US?
```
Color: `#ffffff`, font size 19, line spacing 1.6

**Tags (smaller, grey):**
```
@bundespraesident
@bmvg_bundeswehr
#Iran #Missile #EuropeanSecurity
#NATO #Berlin #Defence
```
Color: `#888888`, font size 14

### Right half — German
**Headline:**
```
🚨 BERLIN IST IN REICHWEITE.
```
Color: `#ff2a2a`, font size 36, bold

**Body text:**
```
Am 21. März 2026 feuerte der Iran
eine Rakete auf einen US-UK-Stützpunkt
4.000 km entfernt — dieselbe Distanz
wie Berlin.

Europa besitzt kein eigenständiges
Raketenabwehrsystem gegen iranische
Mittelstreckenraketen.

❓ WER SCHÜTZT UNS?
```
Color: `#ffffff`, font size 19, line spacing 1.6

**Tags (smaller, grey):**
```
@bundespraesident
@bmvg_bundeswehr
#Iran #Rakete #EuropäischeSicherheit
#NATO #Berlin #Verteidigung
```
Color: `#888888`, font size 14

### Bottom bar (both halves)
Full-width strip, height 60px, background `#ff2a2a`:
```
        IRAN · 4000KM · MARCH 2026 · OPERATION EPIC FURY
```
Color: `#ffffff`, font size 15, bold, centered

---

## Python script requirements

**File:** `generate_slides.py`

### Dependencies to install (if missing)
```bash
pip install matplotlib cartopy pyproj Pillow numpy
```

### Script structure
```
generate_slides.py
├── generate_map_slide()       → saves slide_1_map.png
├── generate_text_slide()      → saves slide_2_text.png
└── main()                     → calls both, prints confirmation
```

### Notes
- Use `matplotlib.patches.Circle` or a geodesic polygon via `pyproj.Geod` for the 4,000 km circle
- All text rendering via `matplotlib.text` — no external font files needed (use `DejaVu Sans` bold)
- Save at **300 DPI** minimum for print quality, but target **1080x1080 px screen resolution**
- Use `fig.savefig(..., bbox_inches='tight', facecolor=fig.get_facecolor())`
- Print to console on success:
  ```
  ✅ slide_1_map.png saved
  ✅ slide_2_text.png saved
  ```

---

## Output files summary
| File | Dimensions | Purpose |
|------|-----------|---------|
| `slide_1_map.png` | 1080x1080 px | Instagram slide 1 — map |
| `slide_2_text.png` | 1080x1080 px | Instagram slide 2 — bilingual text |
| `generate_slides.py` | — | Python script that generates both |

---

## Instagram posting notes (for Bijan)
- Post as **carousel** (2 slides)
- Caption (English first, then German):
  ```
  🚨 On March 21, 2026, Iran demonstrated it can hit Berlin.
  Europe has no independent ballistic missile defense.
  Who is protecting us? 👇

  🚨 Am 21. März 2026 bewies der Iran, dass er Berlin treffen kann.
  Europa hat keine eigenständige Raketenabwehr.
  Wer schützt uns? 👇

  @bundespraesident @bmvg_bundeswehr
  #Iran #Missile #Berlin #NATO #EuropeanSecurity #Rakete #Verteidigung
  ```
- Tag accounts manually in the Instagram post editor after upload
