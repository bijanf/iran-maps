"""
Download required datasets for the Iran maps project.

Downloads:
1. GADM administrative boundaries (shapefile)
2. SRTM 90m DEM topography (CGIAR tiles, merged)
3. Copernicus CGLS-LC100 vegetation / land cover (from Zenodo)
4. WorldPop population density
5. W5E5 climate data — temperature & precipitation (IPCC Atlas)

Data sources & licenses:
- GADM: https://gadm.org/ (free for academic/non-commercial use)
- SRTM: NASA / CGIAR-CSI (public domain)
- Copernicus CGLS-LC100: Buchhorn et al. 2020, Zenodo (CC-BY 4.0)
- WorldPop: https://www.worldpop.org/ (CC-BY 4.0)
- W5E5: ISIMIP / IPCC WGI Interactive Atlas (ERA5 adjusted)
"""

import os
import sys
import urllib.request
import zipfile
import shutil

import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def download_file(url, dest_path, description=""):
    """Download a file with progress indication. Returns True on success."""
    if os.path.exists(dest_path):
        print(f"  Already exists: {dest_path}")
        return True
    print(f"  Downloading {description or url}...")
    try:
        def progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                pct = min(100, downloaded * 100 / total_size)
                mb = downloaded / (1024 * 1024)
                total_mb = total_size / (1024 * 1024)
                sys.stdout.write(f"\r  {mb:.0f}/{total_mb:.0f} MB ({pct:.0f}%)")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, dest_path, reporthook=progress)
        print(f"\n  Saved to: {dest_path}")
        return True
    except Exception as e:
        print(f"\n  ERROR downloading {url}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False


# ── 1. GADM Boundary ─────────────────────────────────────────

def download_gadm():
    """Download GADM Iran boundary shapefile."""
    print("\n[1/5] GADM Iran Boundary")
    url = "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_IRN_shp.zip"
    zip_path = os.path.join(DATA_DIR, "gadm41_IRN_shp.zip")
    download_file(url, zip_path, "GADM Iran shapefile")

    shp_path = os.path.join(DATA_DIR, "iran_boundary.shp")
    if not os.path.exists(shp_path):
        print("  Extracting...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(os.path.join(DATA_DIR, "gadm_extract"))
        extract_dir = os.path.join(DATA_DIR, "gadm_extract")
        for f in os.listdir(extract_dir):
            if "IRN_0" in f:
                ext = os.path.splitext(f)[1]
                shutil.copy2(
                    os.path.join(extract_dir, f),
                    os.path.join(DATA_DIR, f"iran_boundary{ext}"),
                )
        for f in os.listdir(extract_dir):
            if "IRN_1" in f:
                ext = os.path.splitext(f)[1]
                shutil.copy2(
                    os.path.join(extract_dir, f),
                    os.path.join(DATA_DIR, f"iran_provinces{ext}"),
                )
        print("  Extracted iran_boundary.shp and iran_provinces.shp")


# ── 2. SRTM DEM ──────────────────────────────────────────────

def download_srtm():
    """Download SRTM 90m DEM tiles from CGIAR-CSI and merge into iran_dem.tif."""
    import rasterio
    from rasterio.merge import merge
    from rasterio.mask import mask as rio_mask
    import geopandas as gpd
    from shapely.geometry import mapping

    print("\n[2/5] SRTM DEM Topography (CGIAR-CSI 90m tiles)")
    dest = os.path.join(DATA_DIR, "iran_dem.tif")
    if os.path.exists(dest):
        print(f"  Already exists: {dest}")
        return

    # CGIAR SRTM v4.1 tile grid:
    # x = floor((lon + 180) / 5) + 1, y = floor((60 - lat) / 5) + 1
    # Iran: ~44°E-63.3°E, ~25.1°N-39.8°N → x=45-49, y=5-7
    tiles_x = range(45, 50)
    tiles_y = range(5, 8)

    tile_dir = os.path.join(DATA_DIR, "srtm_tiles")
    os.makedirs(tile_dir, exist_ok=True)

    tif_paths = []
    for x in tiles_x:
        for y in tiles_y:
            tile_name = f"srtm_{x:02d}_{y:02d}"
            tif_path = os.path.join(tile_dir, f"{tile_name}.tif")

            if os.path.exists(tif_path):
                tif_paths.append(tif_path)
                continue

            zip_url = (
                "https://srtm.csi.cgiar.org/wp-content/uploads/files/"
                f"srtm_5x5/TIFF/{tile_name}.zip"
            )
            zip_path = os.path.join(tile_dir, f"{tile_name}.zip")

            if download_file(zip_url, zip_path, f"SRTM tile {tile_name}"):
                try:
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(tile_dir)
                    if os.path.exists(tif_path):
                        tif_paths.append(tif_path)
                    else:
                        for f in os.listdir(tile_dir):
                            if f.startswith(tile_name) and f.endswith(".tif"):
                                tif_paths.append(os.path.join(tile_dir, f))
                                break
                except zipfile.BadZipFile:
                    print(f"  Bad zip file for {tile_name}, skipping")
                    os.remove(zip_path)

    if not tif_paths:
        print("  ERROR: No SRTM tiles downloaded.")
        return

    print(f"  Merging {len(tif_paths)} tiles...")
    src_files = [rasterio.open(p) for p in tif_paths]
    mosaic, mosaic_transform = merge(src_files)
    for src in src_files:
        src.close()

    # Clip to Iran boundary
    boundary_path = os.path.join(DATA_DIR, "iran_boundary.shp")
    if os.path.exists(boundary_path):
        print("  Clipping to Iran boundary...")
        profile = rasterio.open(tif_paths[0]).profile.copy()
        profile.update(
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=mosaic_transform,
            compress="deflate",
        )
        tmp_path = dest + ".tmp.tif"
        with rasterio.open(tmp_path, "w", **profile) as tmp_dst:
            tmp_dst.write(mosaic)

        boundary = gpd.read_file(boundary_path)
        with rasterio.open(tmp_path) as src:
            boundary_proj = boundary.to_crs(src.crs)
            geometries = [mapping(geom) for geom in boundary_proj.geometry]
            clipped, clipped_transform = rio_mask(
                src, geometries, crop=True, nodata=-32768
            )
            clip_profile = src.profile.copy()
            clip_profile.update(
                height=clipped.shape[1],
                width=clipped.shape[2],
                transform=clipped_transform,
                nodata=-32768,
                compress="deflate",
            )

        with rasterio.open(dest, "w", **clip_profile) as dst:
            dst.write(clipped)
        os.remove(tmp_path)
    else:
        profile = rasterio.open(tif_paths[0]).profile.copy()
        profile.update(
            height=mosaic.shape[1],
            width=mosaic.shape[2],
            transform=mosaic_transform,
            compress="deflate",
        )
        with rasterio.open(dest, "w", **profile) as dst:
            dst.write(mosaic)

    print(f"  Saved merged DEM: {dest}")


# ── 3. Copernicus Vegetation ─────────────────────────────────

def download_vegetation():
    """Download Copernicus CGLS-LC100 land cover and clip to Iran.

    Source: Buchhorn et al. 2020 — Copernicus Global Land Service
    DOI: 10.5281/zenodo.3939038  (CC-BY 4.0)
    Resolution: 100m discrete classification, 23 UN-FAO LCCS classes.

    The global file (~1.7 GB) is downloaded, then clipped to Iran's extent
    and remapped to ESA WorldCover-compatible class values.
    """
    import rasterio
    from rasterio.mask import mask as rio_mask
    from rasterio.windows import from_bounds
    import geopandas as gpd
    from shapely.geometry import mapping

    print("\n[3/5] Copernicus CGLS-LC100 Vegetation / Land Cover")
    dest = os.path.join(DATA_DIR, "iran_vegetation.tif")
    if os.path.exists(dest):
        print(f"  Already exists: {dest}")
        return

    # Download the global discrete classification file from Zenodo
    global_path = os.path.join(DATA_DIR, "copernicus_lc100_global.tif")
    url = (
        "https://zenodo.org/api/records/3939038/files/"
        "PROBAV_LC100_global_v3.0.1_2015-base_Discrete-Classification-map_EPSG-4326.tif/content"
    )
    if not download_file(url, global_path, "Copernicus CGLS-LC100 global (~1.7 GB)"):
        print("  ERROR: Could not download vegetation data.")
        return

    # Clip to Iran extent
    print("  Clipping to Iran...")
    boundary_path = os.path.join(DATA_DIR, "iran_boundary.shp")
    if not os.path.exists(boundary_path):
        print("  ERROR: Boundary shapefile needed for clipping. Run GADM download first.")
        return

    boundary = gpd.read_file(boundary_path)

    with rasterio.open(global_path) as src:
        boundary_proj = boundary.to_crs(src.crs)
        geometries = [mapping(geom) for geom in boundary_proj.geometry]
        clipped, clipped_transform = rio_mask(
            src, geometries, crop=True, nodata=0
        )
        clip_profile = src.profile.copy()
        clip_profile.update(
            height=clipped.shape[1],
            width=clipped.shape[2],
            transform=clipped_transform,
            nodata=0,
            compress="deflate",
        )

    data = clipped[0]

    # Remap Copernicus CGLS-LC100 classes → ESA WorldCover-compatible classes
    # CGLS: 111-116, 121-126 (forest types) → ESA: 10 (Tree cover)
    # CGLS: 200 (Open sea) → ESA: 80 (Water)
    # CGLS: 20,30,40,50,60,70,80,90,100 → same values in ESA WorldCover
    print("  Remapping classes to ESA WorldCover format...")
    remapped = data.copy()
    # All forest types (111-126) → 10 (Tree cover)
    remapped[(data >= 111) & (data <= 126)] = 10
    # Open sea → Water
    remapped[data == 200] = 80

    # Write clipped & remapped result
    clip_profile.update(dtype="uint8")
    with rasterio.open(dest, "w", **clip_profile) as dst:
        dst.write(remapped[np.newaxis, :, :].astype(np.uint8))

    print(f"  Saved: {dest}")
    print("  Source: Copernicus CGLS-LC100 v3.0.1 (2015), CC-BY 4.0")

    # Optionally clean up the large global file
    print(f"  Removing global file to save space...")
    os.remove(global_path)


# ── 4. WorldPop Population ───────────────────────────────────

def download_worldpop():
    """Download WorldPop population density for Iran."""
    print("\n[4/5] WorldPop Population Density")
    url = "https://data.worldpop.org/GIS/Population_Density/Global_2000_2020_1km/2020/IRN/irn_pd_2020_1km.tif"
    dest = os.path.join(DATA_DIR, "iran_population.tif")
    download_file(url, dest, "WorldPop Iran population density 2020")


# ── 5. W5E5 Climate Data ─────────────────────────────────────

def download_climate():
    """Process W5E5 (ERA5 adjusted) climate data from IPCC Atlas and clip to Iran.

    Source: W5E5 v2.0 — ISIMIP (ERA5 bias-adjusted reanalysis, 1980–2015)
    Resolution: 0.5° global grid
    Variables: tas (annual mean temperature, °C), pr (total precipitation, mm/day → mm/yr)

    The user must manually download the data from the IPCC WGI Interactive Atlas:
      https://interactive-atlas.ipcc.ch/
    and place the zip files in the data/ directory.
    """
    import xarray as xr
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.mask import mask as rio_mask
    import geopandas as gpd
    from shapely.geometry import mapping

    print("\n[5/5] W5E5 Climate Data (Temperature & Precipitation)")

    temp_dest = os.path.join(DATA_DIR, "iran_temperature.tif")
    precip_dest = os.path.join(DATA_DIR, "iran_precipitation.tif")

    if os.path.exists(temp_dest) and os.path.exists(precip_dest):
        print(f"  Already exists: {temp_dest}")
        print(f"  Already exists: {precip_dest}")
        return

    boundary_path = os.path.join(DATA_DIR, "iran_boundary.shp")
    if not os.path.exists(boundary_path):
        print("  ERROR: Boundary shapefile needed for clipping. Run GADM download first.")
        return

    # Find W5E5 zip files in data directory
    tas_zip = None
    pr_zip = None
    for f in os.listdir(DATA_DIR):
        fl = f.lower()
        if "w5e5" in fl and "temperature" in fl and f.endswith(".zip"):
            tas_zip = os.path.join(DATA_DIR, f)
        elif "w5e5" in fl and "precipitation" in fl and f.endswith(".zip"):
            pr_zip = os.path.join(DATA_DIR, f)

    if not tas_zip or not pr_zip:
        print("  ERROR: W5E5 climate zip files not found in data/.")
        print("  Download from https://interactive-atlas.ipcc.ch/ and place in data/:")
        print("    - W5E5 Mean temperature .zip")
        print("    - W5E5 Total precipitation .zip")
        return

    boundary = gpd.read_file(boundary_path)

    # Process each variable
    jobs = [
        (tas_zip, "tas", temp_dest, "temperature", 1.0),
        (pr_zip, "pr", precip_dest, "precipitation", 365.25),
    ]

    for zip_path, var_name, dest_path, label, scale_factor in jobs:
        if os.path.exists(dest_path):
            print(f"  Already exists: {dest_path}")
            continue

        print(f"  Processing {label}...")
        extract_dir = os.path.join(DATA_DIR, f"_tmp_{var_name}")
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        nc_path = os.path.join(extract_dir, "map.nc")
        if not os.path.exists(nc_path):
            print(f"  ERROR: map.nc not found in {zip_path}")
            shutil.rmtree(extract_dir)
            continue

        ds = xr.open_dataset(nc_path)
        # Find the data variable (skip 'crs')
        data_var = var_name if var_name in ds else [v for v in ds.data_vars if v != "crs"][0]
        data = ds[data_var].values * scale_factor
        lat = ds["lat"].values
        lon = ds["lon"].values

        # Rasters expect top-to-bottom latitude
        if lat[0] < lat[-1]:
            data = np.flipud(data)
            lat = lat[::-1]

        transform = from_bounds(
            lon.min() - 0.25, lat.min() - 0.25,
            lon.max() + 0.25, lat.max() + 0.25,
            len(lon), len(lat),
        )
        profile = {
            "driver": "GTiff", "dtype": "float32",
            "width": len(lon), "height": len(lat),
            "count": 1, "crs": "EPSG:4326",
            "transform": transform, "nodata": np.nan,
        }

        # Write global, then clip to Iran
        tmp_global = os.path.join(DATA_DIR, f"_tmp_global_{var_name}.tif")
        with rasterio.open(tmp_global, "w", **profile) as dst:
            dst.write(data.astype(np.float32), 1)

        with rasterio.open(tmp_global) as src:
            geoms = [mapping(g) for g in boundary.to_crs(src.crs).geometry]
            clipped, clipped_t = rio_mask(src, geoms, crop=True, nodata=np.nan)
            p = src.profile.copy()
            p.update(
                height=clipped.shape[1], width=clipped.shape[2],
                transform=clipped_t, compress="deflate",
            )
        with rasterio.open(dest_path, "w", **p) as dst:
            dst.write(clipped)

        # Clean up
        ds.close()
        os.remove(tmp_global)
        shutil.rmtree(extract_dir)
        print(f"  Saved: {dest_path}")

    print("  Source: W5E5 v2.0 / ISIMIP (ERA5 adjusted, 1980–2015)")


# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Iran Maps Project - Data Downloader")
    print("=" * 60)
    download_gadm()        # [1/5]
    download_srtm()        # [2/5]
    download_vegetation()  # [3/5]
    download_worldpop()    # [4/5]
    download_climate()     # [5/5]
    print("\n" + "=" * 60)
    print("Done! Check the data/ directory.")
    print("=" * 60)
