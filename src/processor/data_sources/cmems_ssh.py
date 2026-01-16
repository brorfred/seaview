"""

URLs
----
https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_NRT_008_046/description
"""
import os
import glob
import pathlib
import shutil
import zipfile
from concurrent.futures import ThreadPoolExecutor
import copernicusmarine

import pandas as pd
import satpy
import xarray as xr
import copernicusmarine
from satpy import Scene
#from satpy.dataset import DataID, Dataset  #0.59

#os.environ["SATPY_CONFIG_PATH"] =
#from ..readers import copernicus_ssh
#satpy.readers.copernicus_ssh = copernicus_ssh
#satpy.config.set(config_path=[str(pathlib.Path(__file__).parent)+"/",])

from ..area_definitions import rectlinear as rectlin_area
from .. import config
settings = config.settings
#settings = config.settings.from_env("modis_a")

DATADIR = pathlib.Path(settings["data_dir"] + "/copernicus/SSH")
DATADIR.mkdir(parents=True, exist_ok=True)


VERBOSE = True
def vprint(text):
    if VERBOSE:
        print(text)

def filename(dtm="2025-06-03"):
    dtm = pd.to_datetime(dtm)
    return f"copernicus_SSH_{dtm.date()}.nc"

def open_dataset(dtm="2025-06-03"):
    fn = DATADIR / filename(dtm=dtm)
    if not fn.is_file():
        retrieve(dtm=dtm)
    return xr.open_dataset(DATADIR / filename(dtm=dtm))

def open_scene(dtm="2025-06-03", data_var="sla"):
    fn = DATADIR / filename(dtm=dtm)
    vprint(fn)
    if not fn.is_file():
        retrieve(dtm=dtm)
    scn = Scene(filenames=[fn], reader='copernicus_ssh')
    scn.load(['adt', 'sla', 'ugos', 'vgos'])
    return scn

def retrieve(dtm="2025-06-03", force=False, parallel=True):
    """
    """
    if ((DATADIR / filename(dtm)).is_file() and not force):
        return
    elif force:
        (DATADIR / filename(dtm)).unlink(missing_ok=True)
    dtm = pd.to_datetime(dtm)
    vprint(f"Date: {dtm.date()} \nCollection: Sea Surface Height")

    # Define the time and space domains
    dtstart = dtm.normalize().to_pydatetime()
    dtend = (
        dtm.normalize() + pd.Timedelta(1, "d") - pd.Timedelta(1, "s")
    ).to_pydatetime()

    copernicusmarine.subset(
        #dataset_id="cmems_mod_glo_phy_my_0.083deg_P1D-m",
        dataset_id="cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
        #variables=["uo", "vo"],
        minimum_longitude=settings["lon1"],
        maximum_longitude=settings["lon2"],
        minimum_latitude=settings["lat1"],
        maximum_latitude=settings["lat2"],
        start_datetime=dtstart,
        end_datetime=dtend,
        #minimum_depth=0,
        #maximum_depth=30,
        output_filename = filename(dtm),
        output_directory = DATADIR
    )
