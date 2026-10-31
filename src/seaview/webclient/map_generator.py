import pathlib
import json

import pandas as pd
import folium
import cmasher as cmr
import cmap as cmap_extended

from .. import config

from folium.plugins import GroupedLayerControl
from folium.plugins import MousePosition
from .folium_plugins.realtime_layer import RealtimeLayer
from .folium_plugins.folium_graticule import Graticule
from .folium_plugins.folium_ruler import MeasureControl
from .folium_plugins.dynamic_layers import DynamicLayers
from .folium_plugins.pmtiles_layer import PMTilesLayer
from .folium_plugins.ship_tracker import ShipTracker
from .folium_plugins.cruise_track_dynamic import DynamicCruiseTrack
from .folium_plugins.cruise_track import CruiseTrack
from .folium_plugins.folium_colorbar import ColorbarBox

from .map_help_functions import add_link_to_layer_control

#from .folium_plugins.firebase_realtime import VesselTracker
from folium import JsCode
from branca.element import Element

import requests

#from .tile_layers import add_fields

settings = config.settings


def _resolve_cmap(name, default):
    """Resolve a `cmap` package colormap name (e.g. 'paraview:fast') to matplotlib."""
    if not name:
        return default
    return cmap_extended.Colormap(name).to_matplotlib()

def map():
    m = folium.Map(location=(-20., -31),
                   tiles="Esri.OceanBasemap",
                   zoom_start=6,
                   max_zoom=10,
                   control_scale=True)
    return m

def add_cruise_track(m, geojson_file='/cruise_stations.geojson', name="Cruise Plan", marker="green"):
    fg = folium.FeatureGroup(name=name)
    DynamicCruiseTrack(geojson_file, marker_color=marker).add_to(fg)
    fg.add_to(m)


    #CruiseTrack(geojson_file).add_to(m)



def add_ship_track(m):
    tracker = ShipTracker(
        update_interval=30000,
        track_source='https://soi-vessel-geojson-292717291655.us-central1.run.app/track.geojson',
        realtime_source='https://soi-vessel-geojson-292717291655.us-central1.run.app/latest.geojson',
        vessel_name='R/V Falkor (too)',
        # Grey track
        track_style={
            'color': '#aaa',  # Grey color
            'weight': 2,
            'opacity': 0.7
        },
        # Remove start/end markers
        show_track_markers=False,
        speed_conversion=0.539957,
        speed_unit='knots',
    )
    tracker.add_to(m)


def add_bathy_layer(m):
    attr = (
        '&copy; <a href="https://www.openstreetmap.org/copyright">GEBCO 2025</a> '
    'contributors, &copy; <a href="https://cartodb.com/attributions">GEBCO 2025 2</a>'
    )
    base_url = settings.get("remote_url").rstrip("/") + "/tiles/" + settings.get("cruise_name")
    PMTilesLayer(f"{base_url}/gebco.pmtiles", attr=attr, name="GEBCO 2025",
                 overlay=False, show=False).add_to(m)


def eez_inline(m):
    datadir = pathlib.Path(__file__).parent / 'data'
    with open(datadir / 'world_EEZ.geojson', 'r') as f:
        eez_data = json.load(f)

    #eez_url = 'https://cruise.bror.co/world_EEZ_v12.geojson'
    #eez_data = requests.get(eez_url).json()
    folium.GeoJson(
        eez_data,
        name='EEZ Boundaries',
        show=False,
        style_function=lambda feature: {
            'fillColor': '#3388ff',
            'color': '#3388ff',
            'weight': 2,
            'fillOpacity': 0.1,
            'opacity': 0.4
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['Country'],  # Common fields in Marine Regions data
            #aliases=['EEZ Name:', 'Country:'],
            localize=True
        )
    ).add_to(m)

def eez(m):
    RealtimeLayer(
        source='world_EEZ.geojson',
        name='EEZ zones',
        show=True,  # Test with visible first
        interval=300000,  # Update every 5 minutes
        style={
            'fillColor': '#3388ff',
            'color': '#3388ff',
            'weight': 2,
            'fillOpacity': 0.1,
            'opacity': 0.4
        }
    ).add_to(m)


def graticule(m):
    lat_interval = 1
    lon_interval = 1

    for lat in range(-90, 91, lat_interval):
        folium.PolyLine([[lat, -180],[lat, 180]], weight=0.5, color="#aaa",
).add_to(m)

    for lon in range(-180, 181, lon_interval):
        folium.PolyLine([[-90, lon],[90, lon]], weight=0.5, color="#aaa").add_to(m)


def add_bling(m):
    MousePosition().add_to(m)

    folium.plugins.Fullscreen(
        position="topright",
        title="Full Screen",
        title_cancel="Exit",
        force_separate_button=True,
    ).add_to(m)
    intervals = [
        {'start': 0, 'interval': 30},
        {'start': 3, 'interval': 15},
        {'start': 5, 'interval': 10},
        {'start': 7, 'interval': 5},
        {'start': 9, 'interval': 2},
        {'start': 11, 'interval': 1}
    ]
    Graticule(interval=intervals, color='#666').add_to(m)
    fg = folium.FeatureGroup(name='Night/Day')
    folium.plugins.Terminator().add_to(fg)
    fg.add_to(m)

    MeasureControl(
        position='topright',
        primary_length_unit='nauticalmiles',
        active_color='#00aa00'
    ).add_to(m)


def add_colorbar(m):
    colorbar_box = ColorbarBox(
        position='bottomright',
        title='Legend',
        name='Colorbars',
        opacity=0.7  # 0.0 (transparent) to 1.0 (opaque)
    )

    colorbar_box.add_colorbar(
        cmap=_resolve_cmap(settings["ssh"].get("cmap"), 'RdBu'),
        vmin=settings["ssh"]["vmin"],
        vmax=settings["ssh"]["vmax"],
        label='Sea Surface Height (m)',
        ticks=[-0.20, -0.10, 0, 0.10, 0.20]
    )
    colorbar_box.add_colorbar(
        cmap=_resolve_cmap(settings["ostia"].get("cmap"), 'viridis'),
        vmin=settings["ostia"]["vmin"],
        vmax=settings["ostia"]["vmax"],
        label='Sea Surface Temperature (°C)',
        ticks=[10, 15, 20, 25],
        #tick_labels=['0', '25', '50', '75', '100+']
    )
    colorbar_box.add_colorbar(
        cmap=_resolve_cmap(settings["globcolour"].get("cmap"), 'nipy_spectral'),
        vmin=settings["globcolour"]["vmin"],
        vmax=settings["globcolour"]["vmax"],
        label='Chlorophyll (mg/m3)',
        ticks=[-2.995, -2.30, -0.69, 0, .609, 2.302, 3.912],
        tick_labels=[0.05, 0.1, 0.5, 1, 5, 10, 50]
    )
    colorbar_box.add_colorbar(
        cmap=_resolve_cmap(settings["bathy"].get("cmap"), cmr.ocean),
        vmin=settings["bathy"]["vmin"],
        vmax=settings["bathy"]["vmax"],
        label='Depth (m)',
        ticks=[-5000, -4000, -3000, -2000, -1000],
        tick_labels=[5000, 4000, 3000, 2000, 1000]
    )
    m.add_child(colorbar_box)
    colorbar_control_layer = folium.FeatureGroup(name='Colorbars', show=False)
    m.add_child(colorbar_control_layer)


def add_fields(m):
    DynamicLayers(
        config_file='layer_config.json',
        refresh_interval=300000,  # Auto-refresh every 30 seconds (0 to disable)
        show_refresh_link=True,   # Show refresh link at bottom
        position='topleft'        # 'topleft', 'topright', 'bottomleft', 'bottomright'
    ).add_to(m)
