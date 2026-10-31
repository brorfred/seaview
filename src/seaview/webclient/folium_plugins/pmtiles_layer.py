"""
PMTiles raster layer plugin for Folium.
"""

from folium.elements import JSCSSMixin
from folium.map import Layer
from jinja2 import Template


class PMTilesLayer(JSCSSMixin, Layer):
    """Add a raster PMTiles archive to a Folium map."""

    _template = Template("""
{% macro script(this, kwargs) %}
var {{ this.get_name() }} = pmtiles.leafletRasterLayer(
    new pmtiles.PMTiles({{ this.url|tojson }}),
    {attribution: {{ this.attr|tojson }}}
);
{% endmacro %}
""")

    default_js = [
        ("pmtiles", "https://cdn.jsdelivr.net/npm/pmtiles@4.5.0/dist/pmtiles.js"),
    ]

    def __init__(self, url, attr="", name=None, overlay=True, control=True, show=True):
        super().__init__(name=name, overlay=overlay, control=control, show=show)
        self._name = "PMTilesLayer"
        self.url = url
        self.attr = attr
