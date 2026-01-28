
from pyproj import Transformer

import numpy as np
from typing import Tuple, Optional, List

from . import config
settings = config.settings

class DataObjectError(BaseException):
    """Exception raised when the opening of a data object fails.

    This error is raised when attempting to retireve or open a data
    object. The reason can both be that the retreival failed or that
    the underlying fiel is corrupt.
    """
    pass



def vprint(string, level=3):
    if settings.get("verbose") and (level>=3):
        print(string)



# Web Mercator transformer (lon/lat to x/y meters)
_transformer_to_webmerc = Transformer.from_crs(
    "EPSG:4326", "EPSG:3857", always_xy=True
)
def lonlat_to_webmercator(lons: np.ndarray, lats: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Transform longitude/latitude arrays to Web Mercator coordinates.

    Parameters
    ----------
    lons : numpy.ndarray
        Longitude values in degrees.
    lats : numpy.ndarray
        Latitude values in degrees.

    Returns
    -------
    tuple of numpy.ndarray
        (x, y) coordinates in Web Mercator meters.
    """
    x, y = _transformer_to_webmerc.transform(lons, lats)
    return x.astype(np.float32), y.astype(np.float32)
