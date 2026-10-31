"""
Folium Firebase Realtime Plugin
================================

A Folium plugin for displaying real-time data from Firebase Realtime Database
on an interactive map.
"""

from branca.element import Figure, JavascriptLink, CssLink, MacroElement
from jinja2 import Template
import folium


class FirebaseRealtime(MacroElement):
    """
    Display real-time Firebase data on a Folium map.
    
    This plugin fetches data from Firebase Realtime Database and displays it
    as markers on a map with automatic updates.
    
    Parameters
    ----------
    firebase_url : str
        The Firebase Realtime Database URL to fetch data from.
    data_path : str, default 'FKt_1min_location'
        The path within each Firebase entry containing location data.
    latitude_field : str, default 'latitude'
        The field name for latitude in the data.
    longitude_field : str, default 'longitude'
        The field name for longitude in the data.
    interval : int, default 60000
        Update interval in milliseconds (default: 60 seconds).
    marker_options : dict, optional
        Options for marker styling (radius, fillColor, color, weight, opacity, fillOpacity).
    popup_fields : list, optional
        List of field names to display in the popup. If None, displays common fields.
    popup_labels : dict, optional
        Dictionary mapping field names to display labels in the popup.
    tooltip_text : str, default 'Click for details'
        Text to display in the tooltip on hover.
    filter_invalid : bool, default True
        If True, filters out fields with value -9999 from the popup.
    
    Examples
    --------
    >>> import folium
    >>> from firebase_realtime import FirebaseRealtime
    >>> 
    >>> m = folium.Map(location=[-42.762, -65.024], zoom_start=15)
    >>> 
    >>> firebase = FirebaseRealtime(
    ...     firebase_url='https://your-db.firebaseio.com/users.json',
    ...     interval=60000,
    ...     marker_options={'fillColor': '#ff0000', 'radius': 10}
    ... )
    >>> firebase.add_to(m)
    >>> m.save('map.html')
    """
    
    _template = Template("""
        {% macro header(this, kwargs) %}
            <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet-realtime/2.2.0/leaflet-realtime.min.js"></script>
        {% endmacro %}
        
        {% macro script(this, kwargs) %}
            var source_{{ this.get_name() }} = function(responseHandler, errorHandler) {
                var url = '{{ this.firebase_url }}';

                fetch(url)
                .then((response) => {
                    return response.json().then((data) => {
                        var features = [];
                        
                        for (var key in data) {
                            if (data.hasOwnProperty(key)) {
                                var entry = data[key];
                                if (entry.{{ this.data_path }}) {
                                    var loc = entry.{{ this.data_path }};
                                    
                                    // Extract all properties
                                    var properties = {
                                        'id': key
                                    };
                                    for (var prop in loc) {
                                        if (loc.hasOwnProperty(prop)) {
                                            properties[prop] = loc[prop];
                                        }
                                    }
                                    
                                    features.push({
                                        'type': 'Feature',
                                        'id': key,
                                        'geometry': {
                                            'type': 'Point',
                                            'coordinates': [loc.{{ this.longitude_field }}, loc.{{ this.latitude_field }}]
                                        },
                                        'properties': properties
                                    });
                                }
                            }
                        }
                        
                        return {
                            'type': 'FeatureCollection',
                            'features': features
                        };
                    })
                })
                .then(responseHandler)
                .catch(errorHandler);
            };

            var realtime_{{ this.get_name() }} = L.realtime(
                source_{{ this.get_name() }},
                {
                    interval: {{ this.interval }},
                    getFeatureId: function(f) { 
                        return f.properties.id; 
                    },
                    pointToLayer: function(feature, latlng) {
                        return L.circleMarker(latlng, {{ this.marker_options_json }});
                    },
                    onEachFeature: function(feature, layer) {
                        var props = feature.properties;
                        var coords = feature.geometry.coordinates;
                        
                        var popupContent = '<div style="font-family: Arial; font-size: 12px; min-width: 200px;">';
                        
                        {% if this.popup_fields %}
                        // Use specified fields
                        {% for field in this.popup_fields %}
                        var value_{{ loop.index }} = props['{{ field }}'];
                        if (value_{{ loop.index }} !== undefined && 
                            {% if this.filter_invalid %}value_{{ loop.index }} !== -9999 && {% endif %}
                            value_{{ loop.index }} !== null) {
                            var label_{{ loop.index }} = '{{ this.popup_labels.get(field, field) }}';
                            
                            {% if field == this.latitude_field or field == this.longitude_field %}
                            popupContent += '<b>' + label_{{ loop.index }} + ':</b> ' + 
                                          value_{{ loop.index }}.toFixed(6) + '<br>';
                            {% else %}
                            popupContent += '<b>' + label_{{ loop.index }} + ':</b> ' + 
                                          value_{{ loop.index }} + '<br>';
                            {% endif %}
                        }
                        {% endfor %}
                        {% else %}
                        // Auto-generate popup from all properties
                        for (var key in props) {
                            if (props.hasOwnProperty(key)) {
                                var value = props[key];
                                if (value !== undefined && 
                                    {% if this.filter_invalid %}value !== -9999 && {% endif %}
                                    value !== null) {
                                    popupContent += '<b>' + key + ':</b> ' + value + '<br>';
                                }
                            }
                        }
                        {% endif %}
                        
                        popupContent += '</div>';
                        
                        layer.bindPopup(popupContent);
                        layer.bindTooltip('{{ this.tooltip_text }}');
                    }
                }
            );
            
            realtime_{{ this.get_name() }}.addTo({{ this._parent.get_name() }});
        {% endmacro %}
    """)
    
    def __init__(
        self,
        firebase_url,
        data_path='FKt_1min_location',
        latitude_field='latitude',
        longitude_field='longitude',
        interval=60000,
        marker_options=None,
        popup_fields=None,
        popup_labels=None,
        tooltip_text='Click for details',
        filter_invalid=True
    ):
        super(FirebaseRealtime, self).__init__()
        self._name = 'FirebaseRealtime'
        
        self.firebase_url = firebase_url
        self.data_path = data_path
        self.latitude_field = latitude_field
        self.longitude_field = longitude_field
        self.interval = interval
        self.tooltip_text = tooltip_text
        self.filter_invalid = filter_invalid
        
        # Default marker options
        default_marker_options = {
            'radius': 10,
            'fillColor': '#ff0000',
            'color': '#000',
            'weight': 2,
            'opacity': 1,
            'fillOpacity': 0.8
        }
        
        if marker_options:
            default_marker_options.update(marker_options)
        
        self.marker_options = default_marker_options
        
        # Convert marker options to JSON string for template
        import json
        self.marker_options_json = json.dumps(self.marker_options)
        
        # Popup configuration
        self.popup_fields = popup_fields
        self.popup_labels = popup_labels if popup_labels else {}


class VesselTracker(FirebaseRealtime):
    """
    Specialized plugin for tracking vessels from Firebase.
    
    This is a convenience class that extends FirebaseRealtime with
    vessel-specific defaults and field mappings.
    
    Parameters
    ----------
    firebase_url : str
        The Firebase Realtime Database URL to fetch vessel data from.
    interval : int, default 60000
        Update interval in milliseconds (default: 60 seconds).
    show_path : bool, default False
        If True, draws a line connecting vessel positions (not yet implemented).
    **kwargs
        Additional arguments passed to FirebaseRealtime.
    
    Examples
    --------
    >>> import folium
    >>> from firebase_realtime import VesselTracker
    >>> 
    >>> m = folium.Map(location=[-42.762, -65.024], zoom_start=15)
    >>> 
    >>> tracker = VesselTracker(
    ...     firebase_url='https://soi-vessel-tracker.firebaseio.com/FKt1/users.json?orderBy="$key"&limitToLast=5',
    ...     interval=60000
    ... )
    >>> tracker.add_to(m)
    >>> m.save('vessel_map.html')
    """
    
    def __init__(
        self,
        firebase_url,
        interval=60000,
        show_path=False,
        **kwargs
    ):
        # Vessel-specific defaults
        vessel_defaults = {
            'data_path': 'FKt_1min_location',
            'popup_fields': [
                'id', 'influxtime', 'latitude', 'longitude', 
                'heading', 'speed', 'airtemp', 'watertemp', 
                'windspeed', 'winddir', 'truewindspeed', 'truewinddir'
            ],
            'popup_labels': {
                'id': 'Vessel ID',
                'influxtime': 'Time',
                'latitude': 'Latitude',
                'longitude': 'Longitude',
                'heading': 'Heading',
                'speed': 'Speed (knots)',
                'airtemp': 'Air Temperature (°C)',
                'watertemp': 'Water Temperature (°C)',
                'windspeed': 'Wind Speed (m/s)',
                'winddir': 'Wind Direction (°)',
                'truewindspeed': 'True Wind Speed (m/s)',
                'truewinddir': 'True Wind Direction (°)',
                'rain': 'Rain (mm)',
                'swlight': 'Shortwave Light',
                'watersalt': 'Water Salinity'
            },
            'tooltip_text': 'Vessel - Click for details',
            'marker_options': {
                'radius': 10,
                'fillColor': '#ff0000',
                'color': '#000',
                'weight': 2,
                'opacity': 1,
                'fillOpacity': 0.8
            }
        }
        
        # Merge with user-provided kwargs
        for key, value in vessel_defaults.items():
            if key not in kwargs:
                kwargs[key] = value
        
        super(VesselTracker, self).__init__(
            firebase_url=firebase_url,
            interval=interval,
            **kwargs
        )
        
        self.show_path = show_path
