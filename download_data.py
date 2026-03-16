"""
Download required datasets for the Iran maps project.

Downloads:
1. GADM administrative boundaries (shapefile)
2. SRTM 90m DEM topography (CGIAR tiles, merged)
3. Copernicus CGLS-LC100 vegetation / land cover (from Zenodo)
4. WorldPop population density
5. CHELSA v2.1 climate data — temperature & precipitation

Data sources & licenses:
- GADM: https://gadm.org/ (free for academic/non-commercial use)
- SRTM: NASA / CGIAR-CSI (public domain)
- Copernicus CGLS-LC100: Buchhorn et al. 2020, Zenodo (CC-BY 4.0)
- WorldPop: https://www.worldpop.org/ (CC-BY 4.0)
- CHELSA: Karger et al. 2017, https://chelsa-climate.org/ (CC-BY 4.0)
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


# ── 5. CHELSA Climate Data ────────────────────────────────────

def download_climate():
    """Download CHELSA v2.1 monthly climatologies and compute annual aggregates.

    Source: CHELSA v2.1 — Karger et al. 2017
    Resolution: 30 arc-seconds (~1 km)
    Variables: tas (monthly mean temperature, °C × 10), pr (monthly precipitation, kg/m²)

    Downloads 12 monthly files per variable. Each global file (~1–3 GB) is
    clipped to Iran immediately after download to conserve disk space, then
    monthly clips are averaged (tas) or summed (pr) into annual rasters.
    """
    import rasterio
    from rasterio.mask import mask as rio_mask
    from rasterio.windows import from_bounds as window_from_bounds
    import geopandas as gpd
    from shapely.geometry import mapping

    print("\n[5/5] CHELSA v2.1 Climate Data (Temperature & Precipitation)")

    temp_dest = os.path.join(DATA_DIR, "iran_temperature.tif")
    precip_dest = os.path.join(DATA_DIR, "iran_precipitation.tif")

    if os.path.exists(temp_dest) and os.path.exists(precip_dest):
        print(f"  Already exists: {temp_dest}")
        print(f"  Already exists: {precip_dest}")
        return

    boundary_path = os.path.join(DATA_DIR, "iran_boundary.shp")
    if not os.path.exists(boundary_path):
        print("  ERROR: Boundary shapefile needed. Run GADM download first.")
        return

    boundary = gpd.read_file(boundary_path)

    chelsa_dir = os.path.join(DATA_DIR, "chelsa")
    os.makedirs(chelsa_dir, exist_ok=True)

    base_url = "https://os.unil.cloud.switch.ch/chelsa02/chelsa/global/climatologies"
    variables = [
        # (var, dest, url_template, unit_scale, agg_method)
        ("tas", temp_dest, f"{base_url}/tas/1981-2010/CHELSA_tas_{{m:02d}}_1981-2010_V.2.1.tif",
         0.1, "mean"),   # CHELSA tas = °C × 10 → divide by 10
        ("pr", precip_dest, f"{base_url}/pr/1981-2010/CHELSA_pr_{{m:02d}}_1981-2010_V.2.1.tif",
         1.0, "sum"),    # CHELSA pr = kg/m²/month (= mm/month) → sum for annual
    ]

    for var_name, dest_path, url_template, scale, agg in variables:
        if os.path.exists(dest_path):
            print(f"  Already exists: {dest_path}")
            continue

        print(f"  Processing {var_name} (12 monthly files)...")
        monthly_clips = []
        clip_profile = None

        for month in range(1, 13):
            url = url_template.format(m=month)
            filename = os.path.basename(url)
            global_path = os.path.join(chelsa_dir, filename)

            # Download if not cached
            if not os.path.exists(global_path):
                if not download_file(url, global_path, f"CHELSA {var_name} month {month:02d}"):
                    print(f"  ERROR: Failed to download month {month}. Aborting {var_name}.")
                    break

            # Clip to Iran boundary
            print(f"    Clipping month {month:02d}...")
            with rasterio.open(global_path) as src:
                boundary_proj = boundary.to_crs(src.crs)
                geoms = [mapping(g) for g in boundary_proj.geometry]
                clipped, clipped_t = rio_mask(src, geoms, crop=True, nodata=np.nan)
                if clip_profile is None:
                    clip_profile = src.profile.copy()
                    clip_profile.update(
                        height=clipped.shape[1], width=clipped.shape[2],
                        transform=clipped_t, dtype="float32",
                        nodata=np.nan, compress="deflate",
                    )

            monthly_clips.append(clipped[0].astype(np.float32) * scale)

            # Remove global file to save disk
            os.remove(global_path)

        if len(monthly_clips) != 12:
            print(f"  ERROR: Only got {len(monthly_clips)}/12 months for {var_name}.")
            continue

        # Aggregate: mean for temperature, sum for precipitation
        stack = np.stack(monthly_clips, axis=0)
        if agg == "mean":
            annual = np.nanmean(stack, axis=0)
        else:
            annual = np.nansum(stack, axis=0)
            # Restore NaN where all months were NaN
            all_nan = np.all(np.isnan(stack), axis=0)
            annual[all_nan] = np.nan

        with rasterio.open(dest_path, "w", **clip_profile) as dst:
            dst.write(annual[np.newaxis, :, :])

        print(f"  Saved: {dest_path}")

    # Clean up empty chelsa dir
    if os.path.exists(chelsa_dir) and not os.listdir(chelsa_dir):
        os.rmdir(chelsa_dir)

    print("  Source: CHELSA v2.1 (Karger et al. 2017, 1981–2010)")


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
