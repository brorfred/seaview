"""
Folium Ruler Plugin
A Folium plugin to measure distance and bearing between clicked points on a map.
Based on the leaflet-ruler plugin by gokertanrisever.
"""

from folium import MacroElement
from jinja2 import Template


class MeasureControl(MacroElement):
    """
    Add a measurement control to a Folium map that allows users to measure
    distances and bearings between points.
    
    Parameters
    ----------
    position : str, default 'topright'
        Position of the control. Options: 'topleft', 'topright', 'bottomleft', 'bottomright'
    primary_length_unit : str, default 'kilometers'
        Primary unit for distance measurement. Options: 'kilometers', 'miles', 'nauticalmiles', 'meters', 'feet'
    secondary_length_unit : str, default None
        Optional secondary unit for distance measurement
    primary_area_unit : str, default 'sqmeters'
        Primary unit for area measurement. Options: 'sqmeters', 'sqkilometers', 'sqmiles', 'acres', 'hectares'
    secondary_area_unit : str, default None
        Optional secondary unit for area measurement
    active_color : str, default '#ff0000'
        Color of the measurement line and markers
    completed_color : str, default '#0066ff'
        Color of completed measurements
    popup_options : dict, default None
        Options for the measurement popups
    """
    
    _template = Template("""
        {% macro script(this, kwargs) %}
        
        // Add CSS for the ruler control
        var rulerCSS = `
            .leaflet-ruler {
                width: 30px;
                height: 30px;
                background-color: white;
                cursor: pointer;
                background-image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0yMSAzSDNjLS42IDAtMSAuNC0xIDF2MTZjMCAuNi40IDEgMSAxaDE4Yy42IDAgMS0uNCAxLTFWNGMwLS42LS40LTEtMS0xeiI+PC9wYXRoPjxwYXRoIGQ9Ik0yIDh2MTJjMCAuNi40IDEgMSAxaDEyIj48L3BhdGg+PHBhdGggZD0iTTYgNHY0Ij48L3BhdGg+PHBhdGggZD0iTTEwIDR2NGgtNCI+PC9wYXRoPjxwYXRoIGQ9Ik0xNCA0djRoLTQiPjwvcGF0aD48cGF0aCBkPSJNMTggNHY0aC00Ij48L3BhdGg+PC9zdmc+');
                background-size: 20px 20px;
                background-position: center;
                background-repeat: no-repeat;
                border-radius: 4px;
                box-shadow: 0 1px 5px rgba(0,0,0,0.4);
            }
            
            .leaflet-ruler:hover {
                background-color: #f4f4f4;
            }
            
            .leaflet-ruler.ruler-active {
                background-color: #e0e0e0;
            }
            
            .ruler-crosshair {
                cursor: crosshair !important;
            }
            
            .result-tooltip {
                background-color: white !important;
                border: 2px solid {{ this.active_color }} !important;
                border-radius: 4px !important;
                padding: 4px 8px !important;
                font-size: 12px !important;
                font-weight: bold !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
            }
            
            .result-tooltip:before {
                border-top-color: {{ this.active_color }} !important;
            }
        `;
        
        var styleElement = document.createElement('style');
        styleElement.innerHTML = rulerCSS;
        document.head.appendChild(styleElement);
        
        // Ruler Control Definition
        L.Control.Ruler = L.Control.extend({
            options: {
                position: '{{ this.position }}',
                circleMarker: {
                    color: '{{ this.active_color }}',
                    radius: 4,
                    weight: 2,
                    fillOpacity: 0.8
                },
                lineStyle: {
                    color: '{{ this.active_color }}',
                    weight: 3,
                    dashArray: '5, 10'
                },
                lengthUnit: {
                    display: 'km',
                    decimal: 2,
                    factor: null,
                    label: 'Distance:'
                },
                angleUnit: {
                    display: '&deg;',
                    decimal: 2,
                    label: 'Bearing:'
                }
            },
            
            onAdd: function(map) {
                this._map = map;
                this._container = L.DomUtil.create('div', 'leaflet-bar');
                this._link = L.DomUtil.create('a', 'leaflet-ruler', this._container);
                this._link.href = '#';
                this._link.title = 'Measure distances and bearing';
                
                this._isActive = false;
                this._pointLayer = null;
                this._lineLayer = null;
                this._tempLine = null;
                this._points = [];
                this._clickCount = 0;
                this._clickedLatLong = null;
                this._movingLatLong = null;
                
                L.DomEvent.on(this._link, 'click', this._toggle, this);
                L.DomEvent.disableClickPropagation(this._link);
                
                return this._container;
            },
            
            _toggle: function(e) {
                L.DomEvent.preventDefault(e);
                
                if (this._isActive) {
                    this._deactivate();
                } else {
                    this._activate();
                }
            },
            
            _activate: function() {
                this._isActive = true;
                L.DomUtil.addClass(this._link, 'ruler-active');
                L.DomUtil.addClass(this._map._container, 'ruler-crosshair');
                
                this._pointLayer = L.featureGroup().addTo(this._map);
                this._lineLayer = L.featureGroup().addTo(this._map);
                this._tempLine = L.featureGroup().addTo(this._map);
                
                this._map.on('click', this._onClick, this);
                this._map.on('mousemove', this._onMouseMove, this);
                this._map.on('dblclick', this._onDoubleClick, this);
                this._map.on('keydown', this._onKeyDown, this);
            },
            
            _deactivate: function() {
                this._isActive = false;
                L.DomUtil.removeClass(this._link, 'ruler-active');
                L.DomUtil.removeClass(this._map._container, 'ruler-crosshair');
                
                this._map.off('click', this._onClick, this);
                this._map.off('mousemove', this._onMouseMove, this);
                this._map.off('dblclick', this._onDoubleClick, this);
                this._map.off('keydown', this._onKeyDown, this);
                
                if (this._pointLayer) {
                    this._map.removeLayer(this._pointLayer);
                    this._pointLayer = null;
                }
                if (this._lineLayer) {
                    this._map.removeLayer(this._lineLayer);
                    this._lineLayer = null;
                }
                if (this._tempLine) {
                    this._map.removeLayer(this._tempLine);
                    this._tempLine = null;
                }
                
                this._points = [];
                this._clickCount = 0;
                this._clickedLatLong = null;
                this._movingLatLong = null;
            },
            
            _onClick: function(e) {
                this._clickedLatLong = e.latlng;
                this._points.push(this._clickedLatLong);
                
                if (this._clickCount > 0 && this._points.length > 1) {
                    var prevPoint = this._points[this._points.length - 2];
                    var distance = this._getDistance(prevPoint, this._clickedLatLong);
                    var bearing = this._getBearing(prevPoint, this._clickedLatLong);
                    var totalDistance = this._getTotalDistance();
                    
                    var text = this._formatTooltip(distance, bearing, totalDistance);
                    
                    L.circleMarker(this._clickedLatLong, this.options.circleMarker)
                        .bindTooltip(text, {
                            permanent: true,
                            className: 'result-tooltip',
                            direction: 'right'
                        })
                        .addTo(this._pointLayer)
                        .openTooltip();
                    
                    L.polyline([prevPoint, this._clickedLatLong], this.options.lineStyle)
                        .addTo(this._lineLayer);
                } else {
                    L.circleMarker(this._clickedLatLong, this.options.circleMarker)
                        .addTo(this._pointLayer);
                }
                
                this._clickCount++;
            },
            
            _onMouseMove: function(e) {
                if (this._clickCount === 0) return;
                
                this._movingLatLong = e.latlng;
                
                if (this._tempLine) {
                    this._tempLine.clearLayers();
                }
                
                L.polyline([this._clickedLatLong, this._movingLatLong], {
                    ...this.options.lineStyle,
                    opacity: 0.5
                }).addTo(this._tempLine);
            },
            
            _onDoubleClick: function(e) {
                L.DomEvent.preventDefault(e);
                L.DomEvent.stopPropagation(e);
                this._finishPath();
            },
            
            _onKeyDown: function(e) {
                if (e.keyCode === 27) { // Escape key
                    this._finishPath();
                }
            },
            
            _finishPath: function() {
                if (this._tempLine) {
                    this._tempLine.clearLayers();
                }
                this._points = [];
                this._clickCount = 0;
                this._clickedLatLong = null;
                this._movingLatLong = null;
            },
            
            _getDistance: function(latlng1, latlng2) {
                // Haversine formula for distance calculation
                var R = 6371; // Earth's radius in km
                var dLat = this._toRad(latlng2.lat - latlng1.lat);
                var dLon = this._toRad(latlng2.lng - latlng1.lng);
                var lat1 = this._toRad(latlng1.lat);
                var lat2 = this._toRad(latlng2.lat);
                
                var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                        Math.sin(dLon/2) * Math.sin(dLon/2) * Math.cos(lat1) * Math.cos(lat2);
                var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                var distance = R * c;
                
                var factor = this.options.lengthUnit.factor || 1;
                return distance * factor;
            },
            
            _getBearing: function(latlng1, latlng2) {
                var lat1 = this._toRad(latlng1.lat);
                var lat2 = this._toRad(latlng2.lat);
                var dLon = this._toRad(latlng2.lng - latlng1.lng);
                
                var y = Math.sin(dLon) * Math.cos(lat2);
                var x = Math.cos(lat1) * Math.sin(lat2) -
                        Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
                var bearing = this._toDeg(Math.atan2(y, x));
                
                return (bearing + 360) % 360;
            },
            
            _getTotalDistance: function() {
                var total = 0;
                for (var i = 1; i < this._points.length; i++) {
                    total += this._getDistance(this._points[i-1], this._points[i]);
                }
                return total;
            },
            
            _formatTooltip: function(distance, bearing, totalDistance) {
                var distText = this.options.lengthUnit.label + ' ' + 
                              distance.toFixed(this.options.lengthUnit.decimal) + ' ' +
                              this.options.lengthUnit.display;
                
                var bearingText = this.options.angleUnit.label + ' ' +
                                 bearing.toFixed(this.options.angleUnit.decimal) +
                                 this.options.angleUnit.display;
                
                var totalText = 'Total: ' + totalDistance.toFixed(this.options.lengthUnit.decimal) + ' ' +
                               this.options.lengthUnit.display;
                
                return distText + '<br>' + bearingText + '<br>' + totalText;
            },
            
            _toRad: function(deg) {
                return deg * Math.PI / 180;
            },
            
            _toDeg: function(rad) {
                return rad * 180 / Math.PI;
            }
        });
        
        L.control.ruler = function(options) {
            return new L.Control.Ruler(options);
        };
        
        // Add the ruler control to the map
        L.control.ruler({
            position: '{{ this.position }}',
            circleMarker: {
                color: '{{ this.active_color }}',
                radius: 4,
                weight: 2,
                fillOpacity: 0.8
            },
            lineStyle: {
                color: '{{ this.active_color }}',
                weight: 3,
                dashArray: '5, 10'
            },
            lengthUnit: {
                display: '{{ this.length_unit_display }}',
                decimal: {{ this.length_unit_decimal }},
                factor: {{ this.length_unit_factor }},
                label: 'Distance:'
            },
            angleUnit: {
                display: '&deg;',
                decimal: 2,
                label: 'Bearing:'
            }
        }).addTo({{ this._parent.get_name() }});
        
        {% endmacro %}
    """)
    
    def __init__(
        self,
        position='topright',
        primary_length_unit='kilometers',
        secondary_length_unit=None,
        primary_area_unit='sqmeters',
        secondary_area_unit=None,
        active_color='#ff0000',
        completed_color='#0066ff',
        popup_options=None
    ):
        super().__init__()
        self._name = 'MeasureControl'
        self.position = position
        self.active_color = active_color
        self.completed_color = completed_color
        
        # Unit conversions (from kilometers)
        unit_conversions = {
            'kilometers': {'display': 'km', 'factor': 1, 'decimal': 2},
            'meters': {'display': 'm', 'factor': 1000, 'decimal': 2},
            'miles': {'display': 'mi', 'factor': 0.621371, 'decimal': 2},
            'nauticalmiles': {'display': 'nm', 'factor': 0.539957, 'decimal': 2},
            'feet': {'display': 'ft', 'factor': 3280.84, 'decimal': 2},
        }
        
        unit_config = unit_conversions.get(primary_length_unit, unit_conversions['kilometers'])
        self.length_unit_display = unit_config['display']
        self.length_unit_factor = unit_config['factor']
        self.length_unit_decimal = unit_config['decimal']


# For backward compatibility and easier usage
class RulerControl(MeasureControl):
    """Alias for MeasureControl for backward compatibility"""
    pass
