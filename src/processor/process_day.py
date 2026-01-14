import pathlib

import numpy as np
import pandas as pd

from .tilers import rectlinear as rectlin_tiler
from .data_sources import cmems_ssh, ostia, globcolour
from . import config
settings = config.settings()


def tile_ssh(dtm, verbose=True):
    rectlin_tiler.VERBOSE = verbose
    dtm = pd.to_datetime(dtm, utc=True)
    ds = cmems_ssh.open_dataset(dtm=dtm)
    tile_base = pathlib.Path(settings["tile_dir"]) / "ssh" / str(dtm.date())
    tile_base.mkdir(parents=True, exist_ok=True)

    generator = rectlin_tiler.SlippyTileGenerator(
        min_lat=float(ds.latitude.min()),
        max_lat=float(ds.latitude.max()),
        min_lon=float(ds.longitude.min()),
        max_lon=float(ds.longitude.max())
    )
    generator.generate_tiles(np.squeeze(ds.sla.data),
                             ds.latitude.data,
                             ds.longitude.data,
                             tile_base,
                             settings["zoom_levels"],
                             cmap="RdBu",
                             vmin=-0.75,
                             vmax=0.75)

def tile_sst(dtm, verbose=True):
    rectlin_tiler.VERBOSE = verbose
    dtm = pd.to_datetime(dtm, utc=True)
    ds = ostia.open_dataset(dtm=dtm)
    tile_base = pathlib.Path(settings["tile_dir"]) / "ostia" / str(dtm.date())
    tile_base.mkdir(parents=True, exist_ok=True)

    generator = rectlin_tiler.SlippyTileGenerator(
        min_lat=float(ds.latitude.min()),
        max_lat=float(ds.latitude.max()),
        min_lon=float(ds.longitude.min()),
        max_lon=float(ds.longitude.max())
    )
    generator.generate_tiles(np.squeeze(ds.analysed_sst.data)-273.15,
                             ds.latitude.data,
                             ds.longitude.data,
                             tile_base,
                             settings["zoom_levels"],
                             cmap="viridis",
                             vmin=10,
                             vmax=28)

def tile_globcolour(dtm, verbose=True):
    rectlin_tiler.VERBOSE = verbose
    dtm = pd.to_datetime(dtm, utc=True)
    ds = globcolour.open_dataset(dtm=dtm)
    tile_base = pathlib.Path(settings["tile_dir"]) / "globcolour" / str(dtm.date())
    tile_base.mkdir(parents=True, exist_ok=True)

    generator = rectlin_tiler.SlippyTileGenerator(
        min_lat=float(ds.latitude.min()),
        max_lat=float(ds.latitude.max()),
        min_lon=float(ds.longitude.min()),
        max_lon=float(ds.longitude.max())
    )
    generator.generate_tiles(np.log(np.squeeze(ds.CHL.data)),
                             ds.latitude.data,
                             ds.longitude.data,
                             tile_base,
                             settings["zoom_levels"],
                             cmap="nipy_spectral",
                             vmin=-4.6,
                             vmax=4.6,
                             levels=50)

def all(dtm):
    print("Process SSH tiles")
    tile_ssh(dtm, verbose=False)
    print("Process SST tiles")
    tile_sst(dtm, verbose=False)
    print("Process globcolour tiles")
    tile_globcolour(dtm, verbose=False)
