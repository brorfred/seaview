"""
Cruise Track Plugin for Folium - Dynamic Version
Fetches GeoJSON data when the HTML is viewed, not during generation
"""

import folium
from folium import MacroElement
from jinja2 import Template


class DynamicCruiseTrack(MacroElement):
    """
    A folium plugin that dynamically loads cruise track data from a URL when the map is viewed.
    
    The GeoJSON is fetched client-side (in the browser), so the HTML always shows the latest data
    from the URL without needing to regenerate the map.
    
    Parameters
    ----------
    geojson_url : str
        URL to the GeoJSON file (must be publicly accessible and support CORS)
    name : str, default 'Cruise Track'
        Name of the layer in the layer control
    marker_color : str, default 'green'
        Color of the station markers
    marker_radius : int, default 8
        Radius of the station markers in pixels
    line_color : str, default 'blue'
        Color of the cruise track line
    line_weight : int, default 2
        Weight of the cruise track line
    line_opacity : float, default 0.5
        Opacity of the cruise track line (0-1)
    show : bool, default True
        Whether the layer is visible by default
    
    Examples
    --------
    >>> import folium
    >>> from folium_plugins.cruise_track_dynamic import DynamicCruiseTrack
    >>> 
    >>> m = folium.Map(location=[-35, -45], zoom_start=5)
    >>> DynamicCruiseTrack('https://example.com/cruise_stations.geojson').add_to(m)
    >>> m.save('map.html')
    
    Notes
    -----
    - The GeoJSON URL must be publicly accessible
    - The server must support CORS (Cross-Origin Resource Sharing)
    - The HTML file will fetch fresh data each time it's opened
    - Requires internet connection to view the map
    """
    
    _template = Template("""
        {% macro script(this, kwargs) %}
            (function() {
                // Create feature group for cruise track
                var cruiseTrackGroup = L.featureGroup();
                cruiseTrackGroup.addTo({{ this._parent.get_name() }});
                
                // Function to create popup HTML
                function createPopupHtml(properties) {
                    var html = '<b>Station:</b> ' + (properties.name || 'N/A') + '<br>' +
                               '<b>Arrival:</b> ' + (properties.arrive || 'N/A') + '<br>' +
                               '<b>Departure:</b> ' + (properties.departure || 'N/A') + '<br>';
                    
                    if (properties.depth) {
                        html += '<b>Depth:</b> ' + properties.depth + '<br>';
                    }
                    if (properties.duration) {
                        html += '<b>Duration:</b> ' + properties.duration + '<br>';
                    }
                    if (properties.comments) {
                        html += '<b>Comments:</b> ' + properties.comments + '<br>';
                    }
                    
                    return html;
                }
                
                // Function to style features
                function styleFeature(feature) {
                    return {
                        color: '{{ this.marker_color }}',
                        fillColor: '{{ this.marker_color }}',
                        weight: 3,
                        opacity: 1,
                        fillOpacity: 0.6,
                        radius: {{ this.marker_radius }}
                    };
                }
                
                // Fetch and display GeoJSON
                fetch('{{ this.geojson_url }}')
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Failed to load GeoJSON: ' + response.statusText);
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Extract coordinates for polyline
                        var coordinates = [];
                        
                        // Add markers
                        data.features.forEach(function(feature) {
                            var coords = feature.geometry.coordinates;
                            var latLng = [coords[1], coords[0]]; // GeoJSON is [lon, lat]
                            coordinates.push(latLng);
                            
                            var props = feature.properties || {};
                            var tooltipText = (props.name || 'Station') + ' - ' + (props.arrive || 'N/A');
                            var popupHtml = createPopupHtml(props);
                            
                            // Create circle marker
                            var marker = L.circleMarker(latLng, styleFeature(feature))
                                .bindTooltip(tooltipText)
                                .bindPopup(popupHtml, {maxWidth: 300});
                            
                            marker.addTo(cruiseTrackGroup);
                        });
                        
                        // Add polyline connecting all stations
                        if (coordinates.length > 1) {
                            L.polyline(coordinates, {
                                color: '{{ this.line_color }}',
                                weight: {{ this.line_weight }},
                                opacity: {{ this.line_opacity }}
                            }).addTo(cruiseTrackGroup);
                        }
                    })
                    .catch(error => {
                        console.error('Error loading cruise track:', error);
                        alert('Failed to load cruise track data. Please check the console for details.');
                    });
                
                // Add to layer control
                var overlays = {};
                overlays['{{ this.name }}'] = cruiseTrackGroup;
                
                // Only add control if it doesn't exist yet
                if (!{{ this._parent.get_name() }}._controlledLayers) {
                    {{ this._parent.get_name() }}._controlledLayers = {};
                }
                {{ this._parent.get_name() }}._controlledLayers['{{ this.name }}'] = cruiseTrackGroup;
                
                {% if this.show %}
                cruiseTrackGroup.addTo({{ this._parent.get_name() }});
                {% endif %}
            })();
        {% endmacro %}
    """)
    
    def __init__(
        self,
        geojson_url,
        name='Cruise Track',
        marker_color='green',
        marker_radius=8,
        line_color='blue',
        line_weight=2,
        line_opacity=0.5,
        show=True
    ):
        super(DynamicCruiseTrack, self).__init__()
        self._name = 'DynamicCruiseTrack'
        
        self.geojson_url = geojson_url
        self.name = name
        self.marker_color = marker_color
        self.marker_radius = marker_radius
        self.line_color = line_color
        self.line_weight = line_weight
        self.line_opacity = line_opacity
        self.show = show
