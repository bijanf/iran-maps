# Iran Maps & Visualizations

A collection of Instagram-ready map visualizations and carousel posts about Iran — geography, climate, geopolitics.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Projects

### 1. Iran in 8 Maps — Instagram Carousel
10-slide carousel (1080x1350px, 4:5 ratio) introducing Iran through geography, nature, and climate.

```bash
python generate_maps.py
```

| # | Slide | Description |
|---|-------|-------------|
| 1 | Hook | Silhouette + "IRAN IN 8 MAPS" |
| 2 | Political Boundary | GADM national border |
| 3 | Size Comparison | Iran vs Germany overlay |
| 4 | Topography | SRTM elevation terrain |
| 5 | Elevation Comparison | Bar-chart infographic |
| 6 | Land Cover | Copernicus CGLS-LC100 |
| 7 | Temperature | W5E5 annual mean |
| 8 | Precipitation | W5E5 annual total |
| 9 | Population Density | WorldPop 2020 heatmap |
| 10 | CTA | Save & share |

### 2. Iran War Analysis — Instagram Carousel
5-slide HTML carousel (1080x1080px) analyzing the Iran 2026 conflict — who the players are, why ceasefire fails, and Western responsibility.

```bash
python export_carousel.py
```

Requires Playwright (`pip install playwright && playwright install chromium`).

### 3. Strait of Hormuz
Two-slide carousel: overview map with coastline highlight + bathymetry zoom with NOAA ETOPO depth bands.

### 4. Iran 4,000km Strike Radius
Two-slide carousel: geodesic range circle from Tehran reaching European capitals + bilingual text card.

```bash
python generate_slides.py
```

### 5. Tehran–Berlin Climate Comparison
Story-format plots comparing temperature and precipitation between Tehran and Berlin.

```bash
python generate_story_plots.py
```

## Quick Start

```bash
pip install -r requirements.txt
python download_data.py
python generate_maps.py
```

Output PNGs land in `output/`.

## Data Sources

| Dataset | Source | License |
|---------|--------|---------|
| Boundaries | [GADM v4.1](https://gadm.org/) | Academic / non-commercial |
| Elevation | [SRTM 90 m](https://srtm.csi.cgiar.org/) | Public domain |
| Land Cover | [Copernicus CGLS-LC100 v3](https://zenodo.org/records/3939038) | CC-BY 4.0 |
| Population | [WorldPop 2020 1 km](https://www.worldpop.org/) | CC-BY 4.0 |
| Climate | [W5E5 v2.0 / ISIMIP](https://interactive-atlas.ipcc.ch/) | See ISIMIP terms |
| Bathymetry | [NOAA ETOPO](https://www.ncei.noaa.gov/products/etopo-global-relief-model) | Public domain |
| Context layers | [Natural Earth 10 m](https://www.naturalearthdata.com/) | Public domain |

## Project Structure

```
iran_maps/
├── generate_maps.py        # Main 10-slide map generator
├── generate_slides.py      # Strike radius carousel
├── generate_story_plots.py # Tehran–Berlin climate stories
├── iran_carousel_v2.html   # War analysis carousel (HTML)
├── export_carousel.py      # Playwright PNG exporter
├── download_data.py        # Data download & preprocessing
├── requirements.txt        # Python dependencies
├── data/                   # Input data (gitignored)
└── output/                 # Generated PNGs (gitignored)
```

## License

MIT
