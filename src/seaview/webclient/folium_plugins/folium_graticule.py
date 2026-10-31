"""
Folium Plugin for Leaflet.Graticule
Adds a coordinate grid (graticule) to Folium maps
"""

from branca.element import MacroElement
from jinja2 import Template


class Graticule(MacroElement):
    """
    Add a Leaflet.Graticule layer to display coordinate grid lines on the map.

    Parameters
    ----------
    interval : float or list of dict, default 20.0
        The spacing between grid lines in degrees. Can be either:
        - A single float value for fixed interval at all zoom levels
        - A list of dicts with 'start' (zoom level) and 'interval' (degrees) keys
          to specify different intervals at different zoom levels
    show_label : bool, default True
        Whether to show coordinate labels on the grid lines
    opacity : float, default 1.0
        Opacity of the grid lines (0.0 to 1.0)
    weight : float, default 0.8
        Width of the grid lines in pixels
    color : str, default '#111'
        Color of the grid lines (CSS color)
    font : str, default '12px Verdana'
        Font for coordinate labels
    font_color : str, default '#111'
        Color of coordinate labels (CSS color)
    dash_array : str or None, default None
        Dash pattern for grid lines (e.g., '5, 5' for dashed lines)
    zone_label_style : bool, default False
        Whether to use zone-style labels (e.g., '60°N' instead of '60')

    Examples
    --------
    >>> import folium
    >>> from folium_graticule import Graticule
    >>>
    >>> # Fixed interval
    >>> m = folium.Map(location=[45.5, -122.5], zoom_start=4)
    >>> Graticule(interval=10.0, show_label=True).add_to(m)
    >>> m.save('map_with_graticule.html')
    >>>
    >>> # Zoom-based intervals
    >>> m2 = folium.Map(location=[0, 0], zoom_start=2)
    >>> intervals = [
    ...     {'start': 0, 'interval': 30},
    ...     {'start': 4, 'interval': 10},
    ...     {'start': 6, 'interval': 5},
    ...     {'start': 8, 'interval': 1}
    ... ]
    >>> Graticule(interval=intervals).add_to(m2)
    >>> m2.save('map_with_zoom_intervals.html')
    """

    _template = Template("""
        {% macro script(this, kwargs) %}
            // Load Leaflet.Graticule plugin
            (function() {
                if (typeof L.Graticule === 'undefined') {
                    // Leaflet.Graticule plugin code
                    L.Graticule = L.GeoJSON.extend({
                        options: {
                            interval: 20,
                            showLabel: true,
                            opacity: 1,
                            weight: 0.8,
                            color: '#111',
                            font: '12px Verdana',
                            fontColor: '#111',
                            dashArray: null,
                            zoneLabel: false
                        },

                        initialize: function(options) {
                            L.Util.setOptions(this, options);
                            this._layers = {};

                            // Handle zoom intervals - store original config
                            if (Array.isArray(this.options.interval)) {
                                this._zoomIntervals = this.options.interval.sort(function(a, b) {
                                    return a.start - b.start;
                                });
                                // Don't create graticule yet - wait for onAdd to get map zoom
                                this._needsInit = true;
                            } else {
                                // Fixed interval - create graticule now
                                if (this.options.sphere) {
                                    this.addData(this._getSphericalGraticule());
                                } else {
                                    this.addData(this._getGraticule());
                                }
                            }
                        },

                        _getCurrentInterval: function(zoom) {
                            if (!this._zoomIntervals) {
                                return this.options.interval;
                            }

                            var interval = this._zoomIntervals[0].interval;
                            for (var i = 0; i < this._zoomIntervals.length; i++) {
                                if (zoom >= this._zoomIntervals[i].start) {
                                    interval = this._zoomIntervals[i].interval;
                                } else {
                                    break;
                                }
                            }
                            return interval;
                        },

                        _redrawGraticule: function() {
                            if (!this._map) return;

                            var currentZoom = this._map.getZoom();
                            var newInterval = this._getCurrentInterval(currentZoom);

                            if (newInterval !== this.options.interval) {
                                this.options.interval = newInterval;
                                this.clearLayers();

                                if (this.options.sphere) {
                                    this.addData(this._getSphericalGraticule());
                                } else {
                                    this.addData(this._getGraticule());
                                }

                                if (this._labels) {
                                    this._updateLabels();
                                }
                            }
                        },

                        _getGraticule: function() {
                            var interval = this.options.interval;
                            var features = [];

                            // Latitude lines
                            for (var lat = -90; lat <= 90; lat += interval) {
                                features.push({
                                    type: 'Feature',
                                    geometry: {
                                        type: 'LineString',
                                        coordinates: [[-180, lat], [180, lat]]
                                    },
                                    properties: {
                                        value: lat,
                                        direction: 'lat'
                                    }
                                });
                            }

                            // Longitude lines
                            for (var lon = -180; lon < 180; lon += interval) {
                                features.push({
                                    type: 'Feature',
                                    geometry: {
                                        type: 'LineString',
                                        coordinates: [[lon, -90], [lon, 90]]
                                    },
                                    properties: {
                                        value: lon,
                                        direction: 'lon'
                                    }
                                });
                            }

                            return {
                                type: 'FeatureCollection',
                                features: features
                            };
                        },

                        _getSphericalGraticule: function() {
                            var interval = this.options.interval;
                            var features = [];

                            for (var lat = -90; lat <= 90; lat += interval) {
                                var coords = [];
                                for (var lon = -180; lon <= 180; lon += 5) {
                                    coords.push([lon, lat]);
                                }
                                features.push({
                                    type: 'Feature',
                                    geometry: {
                                        type: 'LineString',
                                        coordinates: coords
                                    },
                                    properties: {
                                        value: lat,
                                        direction: 'lat'
                                    }
                                });
                            }

                            for (var lon = -180; lon < 180; lon += interval) {
                                var coords = [];
                                for (var lat = -90; lat <= 90; lat += 5) {
                                    coords.push([lon, lat]);
                                }
                                features.push({
                                    type: 'Feature',
                                    geometry: {
                                        type: 'LineString',
                                        coordinates: coords
                                    },
                                    properties: {
                                        value: lon,
                                        direction: 'lon'
                                    }
                                });
                            }

                            return {
                                type: 'FeatureCollection',
                                features: features
                            };
                        },

                        onAdd: function(map) {
                            // Call parent onAdd first to set up the layer
                            L.GeoJSON.prototype.onAdd.call(this, map);

                            // If using zoom intervals, initialize graticule now that we have map
                            if (this._needsInit) {
                                var currentZoom = map.getZoom();
                                this.options.interval = this._getCurrentInterval(currentZoom);

                                if (this.options.sphere) {
                                    this.addData(this._getSphericalGraticule());
                                } else {
                                    this.addData(this._getGraticule());
                                }

                                this._needsInit = false;
                            }

                            if (this.options.showLabel) {
                                this._labels = L.layerGroup();
                                this._labels.addTo(map);
                                this._updateLabels();
                                map.on('move', this._updateLabels, this);
                            }

                            // Listen for zoom events to update interval
                            if (this._zoomIntervals) {
                                map.on('zoomend', this._redrawGraticule, this);
                            }
                        },

                        onRemove: function(map) {
                            L.GeoJSON.prototype.onRemove.call(this, map);
                            if (this._labels) {
                                map.removeLayer(this._labels);
                                map.off('move', this._updateLabels, this);
                            }

                            // Remove zoom event listener
                            if (this._zoomIntervals) {
                                map.off('zoomend', this._redrawGraticule, this);
                            }
                        },

                        _updateLabels: function() {
                            if (!this._labels) return;

                            var map = this._map;
                            var bounds = map.getBounds();

                            this._labels.clearLayers();

                            var self = this;
                            this.eachLayer(function(layer) {
                                var props = layer.feature.properties;
                                var coords = layer.feature.geometry.coordinates;

                                if (props.direction === 'lat') {
                                    var point = L.latLng(props.value, bounds.getCenter().lng);
                                    if (bounds.contains(point)) {
                                        self._addLabel(point, self._formatLabel(props.value, 'lat'));
                                    }
                                } else {
                                    var point = L.latLng(bounds.getCenter().lat, props.value);
                                    if (bounds.contains(point)) {
                                        self._addLabel(point, self._formatLabel(props.value, 'lon'));
                                    }
                                }
                            });
                        },

                        _formatLabel: function(value, direction) {
                            if (this.options.zoneLabel) {
                                if (direction === 'lat') {
                                    return Math.abs(value) + '°' + (value >= 0 ? 'N' : 'S');
                                } else {
                                    return Math.abs(value) + '°' + (value >= 0 ? 'E' : 'W');
                                }
                            }
                            return value + '°';
                        },

                        _addLabel: function(latLng, text) {
                            var icon = L.divIcon({
                                className: 'leaflet-graticule-label',
                                html: '<span style="color: ' + this.options.fontColor +
                                      '; font: ' + this.options.font +
                                      '; white-space: nowrap;">' + text + '</span>',
                                iconSize: [0, 0]
                            });
                            L.marker(latLng, {icon: icon, interactive: false}).addTo(this._labels);
                        },

                        style: function(feature) {
                            return {
                                color: this.options.color,
                                opacity: this.options.opacity,
                                weight: this.options.weight,
                                dashArray: this.options.dashArray,
                                interactive: false
                            };
                        }
                    });

                    L.graticule = function(options) {
                        return new L.Graticule(options);
                    };
                }

                // Add graticule to map
                var graticule_{{ this.get_name() }} = L.graticule({
                    interval: {{ this.interval|tojson }},
                    showLabel: {{ this.show_label|tojson }},
                    opacity: {{ this.opacity }},
                    weight: {{ this.weight }},
                    color: {{ this.color|tojson }},
                    font: {{ this.font|tojson }},
                    fontColor: {{ this.font_color|tojson }},
                    {% if this.dash_array %}dashArray: {{ this.dash_array|tojson }},{% endif %}
                    zoneLabel: {{ this.zone_label_style|tojson }},
                    sphere: {{ this.sphere|tojson }}
                });

                graticule_{{ this.get_name() }}.addTo({{ this._parent.get_name() }});
            })();
        {% endmacro %}
    """)

    def __init__(
        self,
        interval=20.0,
        show_label=True,
        opacity=1.0,
        weight=0.8,
        color='#111',
        font='12px Verdana',
        font_color='#111',
        dash_array=None,
        zone_label_style=False,
        sphere=False
    ):
        super().__init__()
        self._name = 'Graticule'

        self.interval = interval
        self.show_label = show_label
        self.opacity = opacity
        self.weight = weight
        self.color = color
        self.font = font
        self.font_color = font_color
        self.dash_array = dash_array
        self.zone_label_style = zone_label_style
        self.sphere = sphere
