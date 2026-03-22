"""
Iran 4,000 km Strike Radius - 2-slide Instagram carousel (1080x1080 px).

Usage:
    python generate_slides.py            # Generate both slides
    python generate_slides.py --slide 1  # Map slide only
    python generate_slides.py --slide 2  # Text slide only
"""

import os
import sys
import warnings

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.patches import FancyBboxPatch

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BG = "#0d0d0d"
LAND = "#1a1a2e"
BORDER = "#2e2e4a"
RED = "#ff2a2a"
ORANGE = "#ff6600"
YELLOW = "#ffdd00"
WHITE = "#ffffff"
GREY = "#aaaaaa"
TAG_GREY = "#888888"

FIG_SIZE = (10.8, 10.8)  # -> 1080x1080 at DPI 100
DPI = 100

TEHRAN = (51.3890, 35.6892)  # lon, lat
RADIUS_KM = 4000

CITIES = {
    #         lon       lat      color   size  fsize  weight
    "Tehran": (51.3890, 35.6892, RED,    80,   11,    "bold"),
    "Berlin": (13.4050, 52.5200, ORANGE, 60,    9,    "normal"),
    "Paris":  ( 2.3522, 48.8566, ORANGE, 60,    9,    "normal"),
    "Rome":   (12.4964, 41.9028, ORANGE, 60,    9,    "normal"),
    "London": (-0.1276, 51.5074, ORANGE, 60,    9,    "normal"),
    "Moscow": (37.6173, 55.7558, YELLOW, 50,    9,    "normal"),
}

OUTLINE = [pe.withStroke(linewidth=3, foreground=BG)]
OUTLINE_THICK = [pe.withStroke(linewidth=4, foreground=BG)]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_fig(projection=None):
    fig = plt.figure(figsize=FIG_SIZE, dpi=DPI)
    fig.patch.set_facecolor(BG)
    if projection:
        ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], projection=projection)
    else:
        ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_facecolor(BG)
    ax.set_axis_off()
    return fig, ax


def _save(fig, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(path, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"\u2705 {filename} saved")


def _geodesic_circle(lon, lat, radius_km, n=360):
    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    lons, lats = [], []
    for az in np.linspace(0, 360, n, endpoint=False):
        dlon, dlat, _ = geod.fwd(lon, lat, az, radius_km * 1000)
        lons.append(dlon)
        lats.append(dlat)
    lons.append(lons[0])
    lats.append(lats[0])
    return lons, lats


# ---------------------------------------------------------------------------
# Slide 1 - Strike radius map
# ---------------------------------------------------------------------------

def generate_map_slide():
    print("Generating slide 1: strike radius map ...")
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    proj = ccrs.PlateCarree()
    fig, ax = _create_fig(projection=proj)
    ax.set_extent([-15, 85, 5, 72], crs=proj)

    # --- map layers ---
    ax.add_feature(cfeature.OCEAN, facecolor=BG, edgecolor="none", zorder=0)
    ax.add_feature(cfeature.LAND, facecolor=LAND, edgecolor="none", zorder=1)
    ax.add_feature(cfeature.BORDERS, edgecolor=BORDER, linewidth=0.4, zorder=2)
    ax.add_feature(cfeature.COASTLINE, edgecolor=BORDER, linewidth=0.5, zorder=2)

    # --- 4000 km geodesic circle ---
    clons, clats = _geodesic_circle(*TEHRAN, RADIUS_KM)
    ax.fill(clons, clats, transform=proj,
            facecolor=RED, alpha=0.12, zorder=3)
    ax.plot(clons, clats, transform=proj,
            color=RED, linewidth=1.8, linestyle="--", zorder=4)

    # --- city markers & labels ---
    for name, (lon, lat, color, size, fsize, weight) in CITIES.items():
        ax.scatter(lon, lat, s=size, color=color, edgecolors="none",
                   transform=proj, zorder=6)
        label_color = RED if name == "Tehran" else WHITE
        ax.text(lon, lat + 1.4, name, transform=proj,
                color=label_color, fontsize=fsize, fontweight=weight,
                ha="center", va="bottom", fontfamily="sans-serif",
                path_effects=OUTLINE, zorder=7)

    # --- Tehran -> Berlin annotation line ---
    blon, blat = CITIES["Berlin"][:2]
    ax.plot([TEHRAN[0], blon], [TEHRAN[1], blat], transform=proj,
            color=ORANGE, linewidth=1.0, linestyle="--", zorder=5)
    mid_lon = (TEHRAN[0] + blon) / 2
    mid_lat = (TEHRAN[1] + blat) / 2
    ax.text(mid_lon, mid_lat + 1.5, "~3,800 km", transform=proj,
            color=WHITE, fontsize=10, ha="center", fontfamily="sans-serif",
            path_effects=OUTLINE, zorder=7)

    # --- title (top-left) ---
    fig.text(0.05, 0.93, "\u2622  IRAN STRIKE RADIUS",
             color=RED, fontsize=22, fontweight="bold",
             fontfamily="sans-serif", path_effects=OUTLINE_THICK)

    # --- bottom source strip ---
    bar = FancyBboxPatch((0, 0), 1, 0.065, transform=fig.transFigure,
                          facecolor="black", alpha=0.65,
                          boxstyle="square,pad=0", zorder=10)
    fig.patches.append(bar)
    fig.text(0.5, 0.025,
             "Demonstrated range: 4,000 km  |  Source: IDF, WSJ, CNN \u2014 March 21, 2026",
             color=GREY, fontsize=13, ha="center", fontfamily="sans-serif",
             zorder=11)

    _save(fig, "slide_1_map.png")


# ---------------------------------------------------------------------------
# Slide 2 - Bilingual text card
# ---------------------------------------------------------------------------

def generate_text_slide():
    print("Generating slide 2: bilingual text ...")
    fig, ax = _create_fig()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # --- vertical divider ---
    ax.plot([0.5, 0.5], [0.08, 0.92], color=RED, linewidth=0.8, alpha=0.6)

    # --- English (left) ---
    ax.text(0.25, 0.88, "\U0001f6a8 BERLIN IS IN RANGE.",
            color=RED, fontsize=28, fontweight="bold",
            ha="center", va="top", fontfamily="sans-serif")

    en_body = (
        "On March 21, 2026, Iran fired a\n"
        "ballistic missile at a US-UK base\n"
        "4,000 km away \u2014 the same distance\n"
        "as Berlin.\n"
        "\n"
        "Europe has no sovereign missile\n"
        "defense system capable of stopping\n"
        "an Iranian IRBM.\n"
        "\n"
        "\u2753 WHO IS PROTECTING US?"
    )
    ax.text(0.25, 0.72, en_body,
            color=WHITE, fontsize=14, linespacing=1.6,
            ha="center", va="top", fontfamily="sans-serif")

    en_tags = (
        "@bundespraesident\n"
        "@bmvg_bundeswehr\n"
        "#Iran #Missile #EuropeanSecurity\n"
        "#NATO #Berlin #Defence"
    )
    ax.text(0.25, 0.18, en_tags,
            color=TAG_GREY, fontsize=11,
            ha="center", va="top", fontfamily="sans-serif",
            linespacing=1.4)

    # --- German (right) ---
    ax.text(0.75, 0.88, "\U0001f6a8 BERLIN IST IN\nREICHWEITE.",
            color=RED, fontsize=28, fontweight="bold",
            ha="center", va="top", fontfamily="sans-serif",
            linespacing=1.2)

    de_body = (
        "Am 21. M\u00e4rz 2026 feuerte der Iran\n"
        "eine Rakete auf einen US-UK-\n"
        "St\u00fctzpunkt 4.000 km entfernt \u2014\n"
        "dieselbe Distanz wie Berlin.\n"
        "\n"
        "Europa besitzt kein eigenst\u00e4ndiges\n"
        "Raketenabwehrsystem gegen\n"
        "iranische Mittelstreckenraketen.\n"
        "\n"
        "\u2753 WER SCH\u00dcTZT UNS?"
    )
    ax.text(0.75, 0.72, de_body,
            color=WHITE, fontsize=14, linespacing=1.6,
            ha="center", va="top", fontfamily="sans-serif")

    de_tags = (
        "@bundespraesident\n"
        "@bmvg_bundeswehr\n"
        "#Iran #Rakete #Europ\u00e4ischeSicherheit\n"
        "#NATO #Berlin #Verteidigung"
    )
    ax.text(0.75, 0.18, de_tags,
            color=TAG_GREY, fontsize=11,
            ha="center", va="top", fontfamily="sans-serif",
            linespacing=1.4)

    # --- bottom red bar ---
    bar = FancyBboxPatch((0, 0), 1, 0.06, transform=ax.transAxes,
                          facecolor=RED, edgecolor="none",
                          boxstyle="square,pad=0", zorder=10)
    ax.add_patch(bar)
    ax.text(0.5, 0.03,
            "IRAN \u00b7 4000KM \u00b7 MARCH 2026 \u00b7 OPERATION EPIC FURY",
            color=WHITE, fontsize=15, fontweight="bold",
            ha="center", va="center", fontfamily="sans-serif", zorder=11)

    _save(fig, "slide_2_text.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
SLIDE_FUNCS = {
    1: generate_map_slide,
    2: generate_text_slide,
}


def main():
    selected = None
    if "--slide" in sys.argv:
        idx = sys.argv.index("--slide") + 1
        if idx < len(sys.argv):
            selected = int(sys.argv[idx])

    print("=" * 50)
    print("Iran Strike Radius \u2014 Instagram Carousel")
    print("=" * 50)

    slides = [selected] if selected else sorted(SLIDE_FUNCS)
    for s in slides:
        try:
            SLIDE_FUNCS[s]()
        except Exception as e:
            print(f"  ERROR slide {s}: {e}")
            import traceback
            traceback.print_exc()

    print("\nDone!")


if __name__ == "__main__":
    main()
