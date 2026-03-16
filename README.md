# Iran in 8 Maps

An Instagram carousel (1080 x 1350 px, 4:5 ratio) introducing Iran through geography, nature, and climate — 10 slides total.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Slides

| # | Slide | Description |
|---|-------|-------------|
| 1 | Hook | Silhouette + "IRAN IN 8 MAPS" |
| 2 | Political Boundary | GADM national border |
| 3 | Size Comparison | Iran vs Germany overlay |
| 4 | Topography | SRTM elevation terrain |
| 5 | Elevation Comparison | Bar-chart infographic (Iran vs Germany) |
| 6 | Land Cover | Copernicus CGLS-LC100 classification |
| 7 | Temperature | W5E5 annual mean (ERA5 adjusted) |
| 8 | Precipitation | W5E5 annual total (ERA5 adjusted) |
| 9 | Population Density | WorldPop 2020 log-scale heatmap |
| 10 | CTA | Save & share call-to-action |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download / prepare data
python download_data.py

# 3. Generate all 10 slides
python generate_maps.py

# Generate a single slide
python generate_maps.py --map 4
```

Output PNGs land in `output/`.

## Data Sources

| Dataset | Source | License |
|---------|--------|---------|
| Boundaries | [GADM v4.1](https://gadm.org/) | Academic / non-commercial |
| Elevation | [SRTM 90 m](https://srtm.csi.cgiar.org/) (CGIAR-CSI) | Public domain |
| Land Cover | [Copernicus CGLS-LC100 v3](https://zenodo.org/records/3939038) | CC-BY 4.0 |
| Population | [WorldPop 2020 1 km](https://www.worldpop.org/) | CC-BY 4.0 |
| Climate | [W5E5 v2.0 / ISIMIP](https://interactive-atlas.ipcc.ch/) (ERA5 adjusted, 1980–2015) | See ISIMIP terms |
| Context layers | [Natural Earth 10 m](https://www.naturalearthdata.com/) | Public domain |

> **Note:** Climate data (temperature & precipitation) must be downloaded manually from the
> [IPCC WGI Interactive Atlas](https://interactive-atlas.ipcc.ch/) — select W5E5 observations,
> annual mean temperature (tas) and total precipitation (pr), then place the zip files in `data/`.

## Requirements

- Python 3.10+
- geopandas, rasterio, matplotlib, numpy, xarray

See `requirements.txt` for exact packages.

## Project Structure

```
iran_maps/
├── generate_maps.py     # Main map generator (10 slides)
├── download_data.py     # Data download & preprocessing
├── requirements.txt     # Python dependencies
├── data/                # Input data (gitignored)
└── output/              # Generated PNGs (gitignored)
```

## License

MIT
