"""
Generate Instagram story plots — personal climate comparison across cities.

Outputs (1080x1350px, 4:5 ratio):
  - story_cities_map.png       — B&W world map with red city markers
  - story_rainfall_all_cities.png  — cumulative daily rainfall
  - story_temperature_all_cities.png — daily mean temperature

Usage:
    python generate_story_plots.py
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from meteostat import daily, stations, Point
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TITLE_FONT = "Noto Serif Display"
BODY_FONT = "Noto Sans Display"

# Station IDs: (city_name, temp_station, rain_station)
# Lahijan has no station — Rasht for temp, Anzali for precip
CITIES = [
    ("Lahijan", "40719", "40718"),
    ("Babol",   "40736", "40736"),
    ("Tehran",  "40754", "40754"),
    ("Yazd",    "40821", "40821"),
    ("Berlin",  "10389", "10389"),
]

MONTH_STARTS = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
MONTH_LABELS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def fetch_daily_clim(sid, var, start=datetime(1991, 1, 1), end=datetime(2020, 12, 31)):
    """Fetch daily climatology (mean per day-of-year) for a station variable."""
    df = daily(sid, start, end).fetch()
    df["doy"] = df.index.dayofyear
    fill = 0 if var == "prcp" else np.nan
    return df.groupby("doy")[var].mean().reindex(range(1, 367), fill_value=fill).values


def anti_overlap(positions, min_gap):
    """Push label positions apart to avoid overlap."""
    pos = [list(p) for p in positions]
    for _ in range(80):
        for j in range(len(pos) - 1):
            gap = pos[j][1] - pos[j + 1][1]
            if gap < min_gap:
                pos[j][1] += (min_gap - gap) * 0.3
                pos[j + 1][1] -= (min_gap - gap) * 0.3
    return pos


# ── Map ──────────────────────────────────────────────────────

def plot_cities_map():
    import geopandas as gpd

    print("[1/3] Cities Map")
    ocean = gpd.read_file(os.path.join(DATA_DIR, "ne_10m_ocean.shp"))
    land = gpd.read_file(os.path.join(DATA_DIR, "ne_10m_land.shp"))

    city_coords = {
        "Lahijan": (37.21, 50.00), "Babol": (36.56, 52.68),
        "Tehran": (35.69, 51.39), "Yazd": (31.90, 54.37),
        "Berlin": (52.52, 13.40),
    }

    fig, ax = plt.subplots(figsize=(10.8, 13.5), dpi=100)
    fig.patch.set_facecolor("#1A1A1A")
    ax.set_facecolor("#1A1A1A")

    land.plot(ax=ax, facecolor="#1A1A1A", edgecolor="none", zorder=1)
    ocean.plot(ax=ax, facecolor="#FFFFFF", edgecolor="none", zorder=2)

    for name, (lat, lon) in city_coords.items():
        ax.plot(lon, lat, "o", color="#C0392B", ms=16, mew=0, zorder=10)

    center_lat = 42.2
    lon_range = 57
    lat_range = lon_range * (13.5 / 10.8)
    ax.set_xlim(5, 62)
    ax.set_ylim(center_lat - lat_range / 2, center_lat + lat_range / 2)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_position([0.0, 0.0, 1.0, 1.0])

    path = os.path.join(OUTPUT_DIR, "story_cities_map.png")
    fig.savefig(path, dpi=100, facecolor="#1A1A1A")
    plt.close()
    print(f"  Saved: {path}")


# ── Rainfall ─────────────────────────────────────────────────

def plot_rainfall():
    print("[2/3] Cumulative Rainfall")

    rain_data = {}
    for city, _, rain_sid in CITIES:
        rain_data[city] = np.nancumsum(fetch_daily_clim(rain_sid, "prcp"))
        print(f"  {city}: {rain_data[city][-1]:.0f} mm/yr")

    order = sorted(rain_data, key=lambda c: rain_data[c][-1], reverse=True)
    n = len(order)
    alphas = np.linspace(1.0, 0.18, n)
    widths = np.linspace(3.8, 1.6, n)
    days = np.arange(1, 367)

    fig, ax = plt.subplots(figsize=(10.8, 13.5), dpi=100)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    for i, city in enumerate(order):
        ax.plot(days, rain_data[city], color="#000000", lw=widths[i],
                alpha=alphas[i], solid_capstyle="round")

    # End labels
    vals = {c: float(rain_data[c][-1]) for c in order}
    y_range = max(vals.values()) - min(vals.values())
    min_gap = y_range * 0.10
    pos = anti_overlap([(c, vals[c]) for c in order], min_gap)

    for i, (city, y_label) in enumerate(pos):
        actual_y = vals[city]
        a = max(float(alphas[i]), 0.42)
        if abs(y_label - actual_y) > min_gap * 0.15:
            ax.plot([367, 370], [actual_y, y_label], color="#000", alpha=0.08, lw=0.7)
        ax.text(372, y_label, city, fontsize=30, color="#000", alpha=a,
                fontfamily=BODY_FONT, va="center")
        ax.text(372, y_label - min_gap * 0.50, f"{actual_y:.0f} mm",
                fontsize=26, color="#000", alpha=a, fontweight="bold",
                fontfamily=BODY_FONT, va="center")

    ax.set_xticks(MONTH_STARTS)
    ax.set_xticklabels(MONTH_LABELS, fontsize=22, fontfamily=BODY_FONT, color="#1A1A1A")
    ax.tick_params(axis="y", labelsize=20, colors="#1A1A1A")
    for lbl in ax.get_yticklabels():
        lbl.set_fontfamily(BODY_FONT)
    ax.set_ylabel("Cumulative Rainfall  (mm)", fontsize=28,
                  fontfamily=BODY_FONT, color="#1A1A1A", labelpad=12)
    ax.set_xlim(0, 366)
    ax.set_ylim(0, None)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)

    fig.text(0.48, 0.955, "Cumulative Rainfall", fontsize=46, color="#1A1A1A",
             fontfamily=TITLE_FONT, ha="center")
    fig.text(0.48, 0.918, "in All Cities I Lived In", fontsize=28, color="#555555",
             fontfamily=TITLE_FONT, ha="center")
    fig.text(0.48, 0.015,
             "Meteostat daily station data (1991\u20132020)  \u00b7  Lahijan = Anzali station",
             fontsize=13, color="#AAAAAA", ha="center", fontfamily=BODY_FONT)

    ax.set_position([0.16, 0.05, 0.62, 0.85])

    path = os.path.join(OUTPUT_DIR, "story_rainfall_all_cities.png")
    fig.savefig(path, dpi=100, facecolor="#FFFFFF")
    plt.close()
    print(f"  Saved: {path}")


# ── Temperature ──────────────────────────────────────────────

def plot_temperature():
    print("[3/3] Daily Temperature")

    temp_data = {}
    for city, temp_sid, _ in CITIES:
        temp_data[city] = fetch_daily_clim(temp_sid, "temp")
        v = temp_data[city]
        print(f"  {city}: {np.nanmin(v):.0f} to {np.nanmax(v):.0f} \u00b0C")

    order = sorted(temp_data, key=lambda c: np.nanmax(temp_data[c]), reverse=True)
    n = len(order)
    alphas = np.linspace(1.0, 0.18, n)
    widths = np.linspace(3.8, 1.6, n)
    days = np.arange(1, 367)

    fig, ax = plt.subplots(figsize=(10.8, 13.5), dpi=100)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    for i, city in enumerate(order):
        ax.plot(days, temp_data[city], color="#000000", lw=widths[i],
                alpha=alphas[i], solid_capstyle="round")

    # Legend in lower right
    handles = [(Line2D([0], [0], color="#000", lw=widths[i], alpha=alphas[i]), city)
               for i, city in enumerate(order)]
    leg = ax.legend([h for h, _ in handles], [l for _, l in handles],
                    loc="lower right", fontsize=22, frameon=False,
                    labelcolor="#1A1A1A", handlelength=2.5,
                    bbox_to_anchor=(0.75, 0.02))
    for text in leg.get_texts():
        text.set_fontfamily(BODY_FONT)

    ax.set_xticks(MONTH_STARTS)
    ax.set_xticklabels(MONTH_LABELS, fontsize=22, fontfamily=BODY_FONT, color="#1A1A1A")
    ax.tick_params(axis="y", labelsize=20, colors="#1A1A1A")
    for lbl in ax.get_yticklabels():
        lbl.set_fontfamily(BODY_FONT)
    ax.set_ylabel("Mean Temperature  (\u00b0C)", fontsize=28,
                  fontfamily=BODY_FONT, color="#1A1A1A", labelpad=12)
    ax.set_xlim(0, 366)
    ax.set_ylim(-5, None)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)

    fig.text(0.50, 0.955, "Daily Temperature", fontsize=46, color="#1A1A1A",
             fontfamily=TITLE_FONT, ha="center")
    fig.text(0.50, 0.918, "in All Cities I Lived In", fontsize=28, color="#555555",
             fontfamily=TITLE_FONT, ha="center")
    fig.text(0.50, 0.015,
             "Meteostat daily station data (1991\u20132020)  \u00b7  Lahijan = Rasht station",
             fontsize=13, color="#AAAAAA", ha="center", fontfamily=BODY_FONT)

    ax.set_position([0.16, 0.05, 0.82, 0.85])

    path = os.path.join(OUTPUT_DIR, "story_temperature_all_cities.png")
    fig.savefig(path, dpi=100, facecolor="#FFFFFF")
    plt.close()
    print(f"  Saved: {path}")


if __name__ == "__main__":
    print("=" * 50)
    print("Story Plots Generator")
    print("=" * 50)
    plot_cities_map()
    plot_rainfall()
    plot_temperature()
    print("\nDone!")
