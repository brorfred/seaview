
from . import *

import folium

from .map_generator import (
    map,
    eez_inline,
    add_bling,
    add_ship_track,
    add_bathy_layer,
    add_cruise_track,
    add_fields,
    add_colorbar,
)


def generate_map():
    m = map()
    eez_inline(m)
    add_bling(m)
    add_ship_track(m)
    add_bathy_layer(m)
    add_cruise_track(m, "/bioreactor_stations.geojson", "BioReactors")
    add_cruise_track(m, "/subsea_stations.geojson", "SubSEA", marker="gray")

    add_fields(m)
    add_colorbar(m)
    folium.LayerControl(collapsed=False, attr="test").add_to(m)
    m.save("index.html")
