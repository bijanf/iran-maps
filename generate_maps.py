"""
Generate 10 maps of Iran for an Instagram carousel — clean white theme.
Output: 1080x1350px PNGs optimized for Instagram engagement.

Usage:
    python generate_maps.py           # Generate all 10 slides
    python generate_maps.py --map 1   # Generate a specific slide (1-10)
"""

import os
import sys
import warnings

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.merge import merge as rio_merge
from matplotlib.colors import LinearSegmentedColormap
from shapely.geometry import mapping

warnings.filterwarnings("ignore")

# ── Constants ──────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Clean white palette
BG_COLOR = "#FFFFFF"
LAND_COLOR = "#E8E8E8"
WATER_COLOR = "#D6EAF8"
NEIGHBOR_LAND_COLOR = "#F0F0F0"
BORDER_COLOR = "#333333"
BORDER_WIDTH = 1.5
ACCENT_COLOR = "#C0392B"
TEXT_COLOR = "#1A1A1A"
MUTED_TEXT = "#666666"
FIG_SIZE = (10.8, 13.5)
DPI = 100
TOTAL_SLIDES = 9

TITLE_FONT = {
    "fontsize": 44,
    "color": TEXT_COLOR,
    "fontweight": "bold",
    "fontfamily": "sans-serif",
}

# Text outline for readability over imagery
TEXT_OUTLINE = [pe.withStroke(linewidth=3, foreground="#FFFFFF")]

# Water body label positions (lon, lat)
SEA_LABELS = [
    (51.5, 27.0, "Persian Gulf"),
    (58.5, 24.8, "Gulf of Oman"),
    (51.0, 38.5, "Caspian Sea"),
]

# Iran map extent (with padding)
IRAN_EXTENT = {
    "minx": 43.5, "maxx": 64.0,
    "miny": 24.5, "maxy": 40.5,
}


# ── Helpers ────────────────────────────────────────────────

def create_fig():
    """Create a figure with a fixed-position axis so Iran stays in the same spot across all slides."""
    fig = plt.figure(figsize=FIG_SIZE, dpi=DPI)
    fig.patch.set_facecolor(BG_COLOR)
    # Leave room for title at top and micro-hook + dots at bottom
    ax = fig.add_axes([0.02, 0.06, 0.96, 0.85])
    ax.set_facecolor(BG_COLOR)
    ax.set_axis_off()
    return fig, ax


def create_text_fig():
    """Create a figure for text-only slides (no map axis)."""
    fig = plt.figure(figsize=FIG_SIZE, dpi=DPI)
    fig.patch.set_facecolor(BG_COLOR)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_facecolor(BG_COLOR)
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return fig, ax


def load_boundary():
    """Load Iran boundary shapefile."""
    shp_path = os.path.join(DATA_DIR, "iran_boundary.shp")
    if not os.path.exists(shp_path):
        raise FileNotFoundError(
            f"Boundary shapefile not found: {shp_path}\n"
            "Run: python download_data.py"
        )
    return gpd.read_file(shp_path)


def load_and_mask_raster(tif_path, boundary_gdf):
    """Load a raster file and mask it to Iran's boundary."""
    if not os.path.exists(tif_path):
        raise FileNotFoundError(f"Raster not found: {tif_path}")

    with rasterio.open(tif_path) as src:
        boundary_proj = boundary_gdf.to_crs(src.crs)
        geometries = [mapping(geom) for geom in boundary_proj.geometry]

        nodata_val = src.nodata if src.nodata is not None else 0
        if np.issubdtype(src.dtypes[0], np.integer):
            mask_nodata = int(nodata_val)
        else:
            mask_nodata = np.nan

        out_image, out_transform = rio_mask(
            src, geometries, crop=True, nodata=mask_nodata
        )
        data = out_image[0].astype(float)
        if mask_nodata is not np.nan:
            data[data == mask_nodata] = np.nan
        if src.nodata is not None and src.nodata != mask_nodata:
            data[out_image[0] == src.nodata] = np.nan

    return data, out_transform


def load_dem_raster(boundary_gdf):
    """Load DEM — merge SRTM tiles with downsampling for 1080px output."""
    import tempfile
    from rasterio.enums import Resampling

    single_tif = os.path.join(DATA_DIR, "iran_dem.tif")
    if os.path.exists(single_tif):
        return load_and_mask_raster(single_tif, boundary_gdf)

    tiles_dir = os.path.join(DATA_DIR, "srtm_tiles")
    tile_files = sorted(
        os.path.join(tiles_dir, f)
        for f in os.listdir(tiles_dir)
        if f.endswith(".tif")
    )
    if not tile_files:
        raise FileNotFoundError("No DEM data found (iran_dem.tif or srtm_tiles/*.tif)")

    print(f"    Merging {len(tile_files)} SRTM tiles (downsampled)...")

    # Read each tile downsampled by 4x (6000->1500 per tile) then merge
    datasets = []
    tmp_files = []
    for tf in tile_files:
        with rasterio.open(tf) as src:
            factor = 8
            new_h = src.height // factor
            new_w = src.width // factor
            data = src.read(
                1, out_shape=(new_h, new_w),
                resampling=Resampling.average,
            )
            new_transform = src.transform * src.transform.scale(
                src.width / new_w, src.height / new_h
            )
            tmp = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
            tmp_files.append(tmp.name)
            profile = src.profile.copy()
            profile.update(
                height=new_h, width=new_w,
                transform=new_transform,
                dtype="int16",
            )
            with rasterio.open(tmp.name, "w", **profile) as dst:
                dst.write(data, 1)

    # Open downsampled tiles and merge
    ds_list = [rasterio.open(f) for f in tmp_files]
    try:
        mosaic, mosaic_transform = rio_merge(ds_list)
    finally:
        for d in ds_list:
            d.close()

    # Write merged result
    merged_tmp = tempfile.NamedTemporaryFile(suffix=".tif", delete=False)
    profile = {
        "driver": "GTiff",
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "count": 1,
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": mosaic_transform,
    }
    with rasterio.open(merged_tmp.name, "w", **profile) as dst:
        dst.write(mosaic[0].astype(np.float32), 1)

    # Clean up tile temps
    for f in tmp_files:
        os.unlink(f)

    try:
        result = load_and_mask_raster(merged_tmp.name, boundary_gdf)
    finally:
        os.unlink(merged_tmp.name)

    return result


def set_map_extent(ax, boundary_gdf=None, pad=0.5):
    """Set axis limits to Iran's bounding box with padding."""
    if boundary_gdf is not None:
        bounds = boundary_gdf.total_bounds
        ax.set_xlim(bounds[0] - pad, bounds[2] + pad)
        ax.set_ylim(bounds[1] - pad, bounds[3] + pad)
    else:
        ax.set_xlim(IRAN_EXTENT["minx"], IRAN_EXTENT["maxx"])
        ax.set_ylim(IRAN_EXTENT["miny"], IRAN_EXTENT["maxy"])


def add_title(ax, title):
    """Add a title to the map — large, bold, white on dark."""
    ax.set_title(title, pad=20, **TITLE_FONT)


def add_source(ax, text, right=False):
    """Add source attribution — bottom-left (default) or bottom-right."""
    x = 0.98 if right else 0.02
    ha = "right" if right else "left"
    ax.text(
        x, 0.02, f"Source: {text}",
        transform=ax.transAxes, fontsize=14, color=MUTED_TEXT,
        ha=ha, va="bottom", fontfamily="sans-serif",
        path_effects=TEXT_OUTLINE,
    )


def add_sea_labels(ax):
    """Add water body labels."""
    for lon, lat, name in SEA_LABELS:
        ax.text(
            lon, lat, name,
            fontsize=16, color="#2874A6", fontstyle="italic",
            fontfamily="sans-serif", ha="center", va="center",
            path_effects=TEXT_OUTLINE,
            zorder=10,
        )


def add_water_background(ax):
    """Draw ocean/water bodies as dark blue background."""
    ocean_path = os.path.join(DATA_DIR, "ne_10m_ocean.shp")
    if os.path.exists(ocean_path):
        ocean = gpd.read_file(ocean_path)
        ocean.plot(ax=ax, facecolor=WATER_COLOR, edgecolor="none", zorder=0)


def add_land_context(ax):
    """Draw neighboring land in dark grey for context."""
    land_path = os.path.join(DATA_DIR, "ne_10m_land.shp")
    if os.path.exists(land_path):
        land = gpd.read_file(land_path)
        land.plot(ax=ax, facecolor=NEIGHBOR_LAND_COLOR, edgecolor="none", zorder=1)


def add_colorbar(fig, ax, im, label):
    """Add an inset colorbar with dark background."""
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    cax = inset_axes(ax, width="2.5%", height="35%", loc="right",
                     borderpad=3.0)
    cax.set_facecolor("#F5F5F5")
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label(label, color=TEXT_COLOR, fontsize=12)
    cbar.ax.yaxis.label.set_path_effects(TEXT_OUTLINE)
    cbar.ax.yaxis.set_tick_params(color=TEXT_COLOR)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TEXT_COLOR, fontsize=10)
    for lbl in cbar.ax.yaxis.get_ticklabels():
        lbl.set_path_effects(TEXT_OUTLINE)
    cbar.outline.set_edgecolor("#CCCCCC")
    return cbar


def add_micro_hook(fig, text):
    """Add italic micro-hook text at bottom center to drive swiping."""
    fig.text(
        0.5, 0.025, text,
        fontsize=18, color=ACCENT_COLOR, fontstyle="italic",
        fontfamily="sans-serif", ha="center", va="center",
        alpha=0.9,
    )


def add_slide_number(fig, n):
    """Add 10 progress dots at top — current dot highlighted in cyan."""
    dot_y = 0.965
    total = TOTAL_SLIDES
    spacing = 0.03
    start_x = 0.5 - (total - 1) * spacing / 2

    for i in range(total):
        x = start_x + i * spacing
        if i + 1 == n:
            fig.text(x, dot_y, "●", fontsize=12, color=ACCENT_COLOR,
                     ha="center", va="center", fontfamily="sans-serif")
        else:
            fig.text(x, dot_y, "●", fontsize=10, color="#CCCCCC",
                     ha="center", va="center", fontfamily="sans-serif")


def save_map(fig, filename):
    """Save the figure as a PNG."""
    path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(
        path, dpi=DPI,
        facecolor=fig.get_facecolor(),
    )
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Slide 1: HOOK ─────────────────────────────────────────
def slide_hook():
    print("[01/09] Hook Slide")
    fig, ax = create_text_fig()

    boundary = load_boundary()

    # Draw Iran silhouette centered
    # Transform boundary to fit nicely in the figure
    geom = boundary.union_all()
    bounds = geom.bounds  # minx, miny, maxx, maxy

    # Map geo coords to figure coords
    geo_w = bounds[2] - bounds[0]
    geo_h = bounds[3] - bounds[1]

    # Create a map axis for the silhouette
    map_ax = fig.add_axes([0.1, 0.25, 0.8, 0.55])
    map_ax.set_facecolor(BG_COLOR)
    map_ax.set_axis_off()

    boundary.plot(
        ax=map_ax, facecolor="none", edgecolor=ACCENT_COLOR,
        linewidth=3.0, zorder=5,
    )
    map_ax.set_xlim(bounds[0] - 1, bounds[2] + 1)
    map_ax.set_ylim(bounds[1] - 1, bounds[3] + 1)
    map_ax.set_aspect("equal")

    # Title text
    fig.text(
        0.5, 0.88, "I  R  A  N",
        fontsize=72, color=TEXT_COLOR, fontweight="bold",
        fontfamily="sans-serif", ha="center", va="center",
    )
    fig.text(
        0.5, 0.83, "IN 7 MAPS",
        fontsize=36, color=ACCENT_COLOR, fontweight="bold",
        fontfamily="sans-serif", ha="center", va="center",
    )

    # Subtitle
    fig.text(
        0.5, 0.18, "Geography · Nature · Climate",
        fontsize=22, color=MUTED_TEXT,
        fontfamily="sans-serif", ha="center", va="center",
    )

    add_micro_hook(fig, "Swipe to explore →")
    add_slide_number(fig, 1)

    save_map(fig, "01_hook.png")


# ── Slide 2: Size Comparison with Germany ──────────────────
def map_size_comparison():
    print("[02/09] Size Comparison: Iran vs Germany")
    fig, ax = create_fig()

    boundary = load_boundary()

    add_water_background(ax)
    add_land_context(ax)

    boundary.plot(
        ax=ax, facecolor=LAND_COLOR, edgecolor=BORDER_COLOR,
        linewidth=BORDER_WIDTH, zorder=5,
    )

    deu_path = os.path.join(DATA_DIR, "germany_boundary.shp")
    if not os.path.exists(deu_path):
        raise FileNotFoundError(
            f"Germany shapefile not found: {deu_path}\n"
            "Download GADM Germany data."
        )

    germany = gpd.read_file(deu_path)

    iran_centroid = boundary.union_all().centroid
    deu_centroid = germany.union_all().centroid
    dx = iran_centroid.x - deu_centroid.x
    dy = iran_centroid.y - deu_centroid.y
    germany_shifted = germany.copy()
    germany_shifted["geometry"] = germany_shifted.geometry.translate(xoff=dx, yoff=dy)

    germany_shifted.plot(
        ax=ax, facecolor="#555555", edgecolor="#333333",
        linewidth=1.5, alpha=0.85, zorder=7,
    )

    deu_center = germany_shifted.union_all().centroid
    ax.text(
        deu_center.x, deu_center.y, "Germany",
        fontsize=22, color="#FFFFFF", fontweight="bold",
        fontfamily="sans-serif", ha="center", va="center",
        path_effects=[pe.withStroke(linewidth=3, foreground="#333333")],
        zorder=8,
    )

    iran_area_km2 = 1_648_195
    deu_area_km2 = 357_588
    ratio = iran_area_km2 / deu_area_km2
    ax.text(
        0.02, 0.08,
        f"Iran is {ratio:.1f}× larger",
        transform=ax.transAxes, fontsize=20, color=TEXT_COLOR,
        fontfamily="sans-serif", fontweight="bold",
        va="bottom", ha="left",
        path_effects=TEXT_OUTLINE,
    )

    set_map_extent(ax, boundary)
    add_title(ax, "IRAN — Size Comparison")
    add_sea_labels(ax)
    add_source(ax, "GADM v4.1")

    add_micro_hook(fig, "Now see the terrain →")
    add_slide_number(fig, 2)

    save_map(fig, "02_size_comparison.png")


# ── Slide 4: Topography ───────────────────────────────────
def map_topography():
    print("[03/09] Topography Map")
    fig, ax = create_fig()

    boundary = load_boundary()
    data, transform = load_dem_raster(boundary)

    add_water_background(ax)
    add_land_context(ax)

    # Earth-tone terrain colormap for dark background
    terrain_cmap = LinearSegmentedColormap.from_list(
        "dark_terrain",
        ["#1A3300", "#2D5016", "#6B8E23", "#C8A960", "#D4A574", "#E8D5B0", "#FFFFFF"],
        N=256,
    )

    extent = [
        transform[2],
        transform[2] + transform[0] * data.shape[1],
        transform[5] + transform[4] * data.shape[0],
        transform[5],
    ]
    im = ax.imshow(
        data, cmap=terrain_cmap, extent=extent,
        vmin=np.nanpercentile(data, 2),
        vmax=np.nanpercentile(data, 98),
        zorder=5,
    )

    boundary.plot(ax=ax, facecolor="none", edgecolor=BORDER_COLOR, linewidth=BORDER_WIDTH, alpha=0.6, zorder=6)

    set_map_extent(ax, boundary)
    add_title(ax, "IRAN — Topography")
    add_sea_labels(ax)

    add_colorbar(fig, ax, im, "Elevation (m)")

    add_source(ax, "NASA SRTM 90m / CGIAR-CSI")

    add_micro_hook(fig, "How high is Iran really? →")
    add_slide_number(fig, 3)

    save_map(fig, "03_topography.png")


# ── Slide 5: Elevation Comparison ────────────────────────
def slide_elevation_comparison():
    print("[04/09] Elevation Comparison Slide")
    fig, ax = create_text_fig()
    from matplotlib.patches import Rectangle

    add_slide_number(fig, 4)

    # Title
    fig.text(
        0.5, 0.88, "IRAN — Elevation",
        fontsize=44, color=TEXT_COLOR, fontweight="bold",
        fontfamily="sans-serif", ha="center", va="center",
    )

    # Data
    bars = [
        ("Average Elevation", 1305, "Iran", 263, "Germany"),
        ("Highest Peak", 5610, "Damavand", 2962, "Zugspitze"),
    ]

    y_positions = [0.62, 0.38]
    max_val = 5610
    bar_left = 0.18
    bar_max_w = 0.65
    bar_h = 0.045

    for (group_label, val1, lbl1, val2, lbl2), y_base in zip(bars, y_positions):
        # Group label
        fig.text(
            0.5, y_base + 0.10, group_label,
            fontsize=26, color=MUTED_TEXT, fontweight="bold",
            fontfamily="sans-serif", ha="center", va="center",
        )

        # Iran bar (cyan)
        w1 = bar_max_w * (val1 / max_val)
        rect1 = Rectangle((bar_left, y_base + 0.02), w1, bar_h,
                           facecolor="#2874A6", alpha=0.9, transform=ax.transAxes)
        ax.add_patch(rect1)
        fig.text(
            bar_left + w1 + 0.02, y_base + 0.02 + bar_h / 2,
            f"{val1:,} m", fontsize=20, color="#2874A6", fontweight="bold",
            fontfamily="sans-serif", va="center",
        )
        fig.text(
            bar_left - 0.02, y_base + 0.02 + bar_h / 2,
            lbl1, fontsize=20, color=TEXT_COLOR, fontweight="bold",
            fontfamily="sans-serif", ha="right", va="center",
        )

        # Germany bar (amber)
        w2 = bar_max_w * (val2 / max_val)
        rect2 = Rectangle((bar_left, y_base - 0.04), w2, bar_h,
                           facecolor="#777777", alpha=0.9, transform=ax.transAxes)
        ax.add_patch(rect2)
        fig.text(
            bar_left + w2 + 0.02, y_base - 0.04 + bar_h / 2,
            f"{val2:,} m", fontsize=20, color="#555555", fontweight="bold",
            fontfamily="sans-serif", va="center",
        )
        fig.text(
            bar_left - 0.02, y_base - 0.04 + bar_h / 2,
            lbl2, fontsize=20, color=TEXT_COLOR, fontweight="bold",
            fontfamily="sans-serif", ha="right", va="center",
        )

    # Bold callout
    fig.text(
        0.5, 0.15, "Iran is 5× higher on average",
        fontsize=28, color="#2874A6", fontweight="bold",
        fontfamily="sans-serif", ha="center", va="center",
    )

    # Source
    fig.text(
        0.5, 0.08, "Source: NASA SRTM / BKG",
        fontsize=14, color=MUTED_TEXT,
        fontfamily="sans-serif", ha="center", va="center",
    )

    add_micro_hook(fig, "What covers this high plateau? →")

    save_map(fig, "04_elevation.png")


# ── Slide 6: Vegetation / Land Cover ─────────────────────
def map_vegetation():
    print("[05/09] Land Cover Map")
    fig, ax = create_fig()

    boundary = load_boundary()
    tif_path = os.path.join(DATA_DIR, "iran_vegetation.tif")
    data, transform = load_and_mask_raster(tif_path, boundary)

    add_water_background(ax)
    add_land_context(ax)

    # Saturated vegetation palette for dark background
    veg_colors = {
        10: "#1B8A2A",  # Tree cover — vivid green
        20: "#5A9E3C",  # Shrubland
        30: "#8BC34A",  # Grassland — bright lime
        40: "#FFD54F",  # Cropland — warm gold
        50: "#FF6F00",  # Built-up — amber
        60: "#8D6E63",  # Bare/sparse — warm brown
        70: "#E0E0E0",  # Snow/ice
        80: "#2299DD",  # Water — bright blue
        90: "#26A69A",  # Wetland — teal
        95: "#00695C",  # Mangroves
        100: "#7B6B3A", # Moss/lichen
    }

    unique_vals = sorted(veg_colors.keys())
    colors_list = [veg_colors[v] for v in unique_vals]
    bounds = unique_vals + [unique_vals[-1] + 10]
    cmap = mcolors.ListedColormap(colors_list)
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    extent = [
        transform[2],
        transform[2] + transform[0] * data.shape[1],
        transform[5] + transform[4] * data.shape[0],
        transform[5],
    ]
    ax.imshow(data, cmap=cmap, norm=norm, extent=extent, interpolation="nearest", zorder=5)

    boundary.plot(ax=ax, facecolor="none", edgecolor=BORDER_COLOR, linewidth=BORDER_WIDTH, alpha=0.6, zorder=6)

    set_map_extent(ax, boundary)
    add_title(ax, "IRAN — Land Cover")
    add_sea_labels(ax)

    legend_labels = {
        10: "Tree Cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland",
        50: "Built-up", 60: "Bare / Sparse", 70: "Snow / Ice", 80: "Water",
    }
    from matplotlib.patches import Patch
    patches = [Patch(facecolor=veg_colors[k], edgecolor="#555555", label=v) for k, v in legend_labels.items()]
    leg = ax.legend(
        handles=patches, loc="lower left", fontsize=18,
        facecolor="#FFFFFF", edgecolor="#CCCCCC", labelcolor=TEXT_COLOR,
        framealpha=0.95, handlelength=1.5, handleheight=1.5,
    )
    leg.get_frame().set_linewidth(0.5)

    add_source(ax, "Copernicus CGLS-LC100 v3 (Buchhorn et al. 2020)", right=True)

    add_micro_hook(fig, "How warm is Iran? →")
    add_slide_number(fig, 5)

    save_map(fig, "05_landcover.png")


# ── Slide 9: Population Density ───────────────────────────
def map_population():
    print("[08/09] Population Density Map")
    fig, ax = create_fig()

    boundary = load_boundary()
    tif_path = os.path.join(DATA_DIR, "iran_population.tif")
    data, transform = load_and_mask_raster(tif_path, boundary)

    add_water_background(ax)
    add_land_context(ax)

    data[data <= 0] = np.nan

    extent = [
        transform[2],
        transform[2] + transform[0] * data.shape[1],
        transform[5] + transform[4] * data.shape[0],
        transform[5],
    ]

    log_norm = mcolors.LogNorm(
        vmin=max(np.nanpercentile(data, 5), 0.1),
        vmax=np.nanpercentile(data, 99),
    )

    im = ax.imshow(data, cmap="inferno", norm=log_norm, extent=extent, zorder=5)

    boundary.plot(ax=ax, facecolor="none", edgecolor=BORDER_COLOR, linewidth=BORDER_WIDTH, alpha=0.4, zorder=6)

    set_map_extent(ax, boundary)
    add_title(ax, "IRAN — Population Density")
    add_sea_labels(ax)

    add_colorbar(fig, ax, im, "People per km²")

    add_source(ax, "WorldPop 2020 1km")

    add_micro_hook(fig, "Save & share →")
    add_slide_number(fig, 8)

    save_map(fig, "08_population.png")


# ── Slide 7: Temperature ─────────────────────────────────
def map_temperature():
    print("[06/09] Temperature Map")
    fig, ax = create_fig()

    boundary = load_boundary()
    tif_path = os.path.join(DATA_DIR, "iran_temperature.tif")
    data, transform = load_and_mask_raster(tif_path, boundary)

    # CHELSA: download_data.py already converts °C×10 → °C

    add_water_background(ax)
    add_land_context(ax)

    # Discrete temperature classes
    temp_bounds = [-5, 0, 5, 10, 15, 20, 25, 30]
    temp_colors = ["#2166AC", "#67A9CF", "#D1E5F0", "#FDDBC7", "#EF8A62", "#B2182B", "#67001F"]
    temp_cmap = mcolors.ListedColormap(temp_colors)
    temp_norm = mcolors.BoundaryNorm(temp_bounds, temp_cmap.N)

    extent = [
        transform[2],
        transform[2] + transform[0] * data.shape[1],
        transform[5] + transform[4] * data.shape[0],
        transform[5],
    ]
    im = ax.imshow(
        data, cmap=temp_cmap, norm=temp_norm, extent=extent,
        interpolation="nearest", zorder=5,
    )

    boundary.plot(ax=ax, facecolor="none", edgecolor=BORDER_COLOR, linewidth=BORDER_WIDTH, alpha=0.6, zorder=6)

    set_map_extent(ax, boundary)
    add_title(ax, "IRAN — Temperature")
    add_sea_labels(ax)

    add_colorbar(fig, ax, im, "Annual Mean Temperature (°C)")

    add_source(ax, "CHELSA v2.1 (Karger et al. 2017, 1981–2010)")

    add_micro_hook(fig, "How much rain falls here? →")
    add_slide_number(fig, 6)

    save_map(fig, "06_temperature.png")


# ── Slide 8: Precipitation ──────────────────────────────
def map_precipitation():
    print("[07/09] Precipitation Map")
    fig, ax = create_fig()

    boundary = load_boundary()
    tif_path = os.path.join(DATA_DIR, "iran_precipitation.tif")
    data, transform = load_and_mask_raster(tif_path, boundary)

    add_water_background(ax)
    add_land_context(ax)

    # Discrete precipitation classes (mm/year)
    precip_bounds = [0, 50, 100, 200, 300, 500, 750, 1000, 1500]
    precip_colors = ["#8C510A", "#BF812D", "#DFC27D", "#F6E8C3", "#C7EAE5", "#80CDC1", "#35978F", "#01665E"]
    precip_cmap = mcolors.ListedColormap(precip_colors)
    precip_norm = mcolors.BoundaryNorm(precip_bounds, precip_cmap.N)

    extent = [
        transform[2],
        transform[2] + transform[0] * data.shape[1],
        transform[5] + transform[4] * data.shape[0],
        transform[5],
    ]
    im = ax.imshow(
        data, cmap=precip_cmap, norm=precip_norm, extent=extent,
        interpolation="nearest", zorder=5,
    )

    boundary.plot(ax=ax, facecolor="none", edgecolor=BORDER_COLOR, linewidth=BORDER_WIDTH, alpha=0.6, zorder=6)

    set_map_extent(ax, boundary)
    add_title(ax, "IRAN — Precipitation")
    add_sea_labels(ax)

    add_colorbar(fig, ax, im, "Annual Precipitation (mm)")

    add_source(ax, "CHELSA v2.1 (Karger et al. 2017, 1981–2010)")

    add_micro_hook(fig, "Where do 88 million people live? →")
    add_slide_number(fig, 7)

    save_map(fig, "07_precipitation.png")


# ── Slide 10: CTA ─────────────────────────────────────────
def slide_cta():
    print("[09/09] CTA Slide")
    fig, ax = create_text_fig()

    fig.text(
        0.5, 0.62, "Save this post.",
        fontsize=44, color=TEXT_COLOR, fontweight="bold",
        fontfamily="sans-serif", ha="center", va="center",
    )
    fig.text(
        0.5, 0.52, "Share it with someone",
        fontsize=32, color=MUTED_TEXT,
        fontfamily="sans-serif", ha="center", va="center",
    )
    fig.text(
        0.5, 0.46, "who'd love to see this.",
        fontsize=32, color=MUTED_TEXT,
        fontfamily="sans-serif", ha="center", va="center",
    )

    # Accent line
    ax.plot([0.3, 0.7], [0.38, 0.38], color=ACCENT_COLOR, linewidth=2, alpha=0.6)

    fig.text(
        0.5, 0.32, "@bijanfallah_",
        fontsize=22, color=ACCENT_COLOR,
        fontfamily="sans-serif", ha="center", va="center",
    )

    add_slide_number(fig, 9)

    save_map(fig, "09_cta.png")


# ── Main ──────────────────────────────────────────────────
MAP_FUNCS = {
    1: slide_hook,
    2: map_size_comparison,
    3: map_topography,
    4: slide_elevation_comparison,
    5: map_vegetation,
    6: map_temperature,
    7: map_precipitation,
    8: map_population,
    9: slide_cta,
}


def main():
    selected = None
    if "--map" in sys.argv:
        idx = sys.argv.index("--map") + 1
        if idx < len(sys.argv):
            selected = int(sys.argv[idx])

    print("=" * 50)
    print("Iran Maps Generator")
    print("=" * 50)

    maps_to_run = [selected] if selected else sorted(MAP_FUNCS.keys())

    for m in maps_to_run:
        try:
            MAP_FUNCS[m]()
        except FileNotFoundError as e:
            print(f"  SKIPPED: {e}")
        except Exception as e:
            print(f"  ERROR generating slide {m}: {e}")
            import traceback
            traceback.print_exc()

    print("\nDone!")


if __name__ == "__main__":
    main()
