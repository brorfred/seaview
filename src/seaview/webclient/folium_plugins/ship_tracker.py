"""
Ship Tracker Plugin for Folium
Combines real-time vessel position tracking with historical track display.
Uses direct JavaScript injection for reliable Realtime layer rendering.
"""

from folium import Map, FeatureGroup, Marker, CircleMarker, DivIcon, Popup
from folium.features import GeoJson, GeoJsonPopup, GeoJsonTooltip
from branca.element import MacroElement, Element
from jinja2 import Template
import requests


class ShipTracker(MacroElement):
    """
    A Folium plugin for ship tracking that combines:
    - Real-time position updates
    - Historical track display (also real-time)
    - Customizable vessel markers
    - Layer control integration
    
    Parameters
    ----------
    realtime_source : str, optional
        URL endpoint for real-time position data (GeoJSON Point)
    track_source : str, optional
        URL endpoint for historical track data (GeoJSON LineString)
    track_data : dict, optional
        Static GeoJSON data for the track (alternative to track_source)
    update_interval : int, default 5000
        Update interval for real-time data in milliseconds
    show_realtime : bool, default True
        Show real-time position layer on load
    show_track : bool, default True
        Show historical track layer on load
    track_style : dict, optional
        Custom styling for the track line
    vessel_name : str, optional
        Name of the vessel for display in popups
    auto_center : bool, default True
        Automatically center map on track bounds
    
    Examples
    --------
    >>> import folium
    >>> from folium_ship_tracker import ShipTracker
    >>> 
    >>> m = folium.Map(location=[0, 0], zoom_start=5)
    >>> tracker = ShipTracker(
    ...     track_source='https://example.com/track.geojson',
    ...     realtime_source='https://example.com/position.geojson',
    ...     vessel_name='R/V Falkor'
    ... )
    >>> tracker.add_to(m)
    >>> m.save('map.html')
    """
    
    _template = Template("""
        {% macro script(this, kwargs) %}
        (function() {
            // Wait for map to be ready
            var checkMap = setInterval(function() {
                if (typeof {{ this._parent.get_name() }} !== 'undefined') {
                    clearInterval(checkMap);
                    initShipTracker_{{ this.get_name() }}();
                }
            }, 100);
            
            function initShipTracker_{{ this.get_name() }}() {
                var map = {{ this._parent.get_name() }};
                
                // Create feature groups
                var trackGroup = L.featureGroup();
                var positionGroup = L.featureGroup();
                
                {% if this.show_track %}
                trackGroup.addTo(map);
                {% endif %}
                {% if this.show_realtime %}
                positionGroup.addTo(map);
                {% endif %}
                
                {% if this.track_source %}
                // Track layer (real-time)
                var trackLayer = L.realtime({
                    url: '{{ this.track_source }}',
                    crossOrigin: true,
                    type: 'json'
                }, {
                    interval: {{ this.update_interval }},
                    getFeatureId: function(feature) {
                        return 'track';
                    },
                    style: function(feature) {
                        return {
                            color: '{{ this.track_color }}',
                            weight: {{ this.track_weight }},
                            opacity: {{ this.track_opacity }},
                            lineJoin: '{{ this.track_line_join }}',
                            lineCap: '{{ this.track_line_cap }}'
                        };
                    },
                    onEachFeature: function(feature, layer) {
                        layer.bindTooltip('{{ this.vessel_name }} Track');
                        
                        {% if this.show_track_markers %}
                        if (feature.geometry.type === 'LineString') {
                            var coords = feature.geometry.coordinates;
                            if (coords && coords.length >= 2) {
                                // Start marker
                                L.circleMarker([coords[0][1], coords[0][0]], {
                                    radius: 8,
                                    color: 'green',
                                    fillColor: 'green',
                                    fillOpacity: 0.8
                                }).bindPopup('<b>{{ this.vessel_name }}</b><br>Track Start')
                                  .bindTooltip('Track Start')
                                  .addTo(map);
                                
                                // End marker
                                L.circleMarker([coords[coords.length-1][1], coords[coords.length-1][0]], {
                                    radius: 8,
                                    color: 'red',
                                    fillColor: 'red',
                                    fillOpacity: 0.8
                                }).bindPopup('<b>{{ this.vessel_name }}</b><br>Track End')
                                  .bindTooltip('Track End')
                                  .addTo(map);
                            }
                        }
                        {% endif %}
                    }
                });
                trackGroup.addLayer(trackLayer);
                {% endif %}
                
                {% if this.realtime_source %}
                // Position layer (real-time)
                var positionLayer = L.realtime({
                    url: '{{ this.realtime_source }}',
                    crossOrigin: true,
                    type: 'json'
                }, {
                    interval: {{ this.update_interval }},
                    getFeatureId: function(feature) {
                        return feature.properties._endpoint || 'vessel';
                    },
                    pointToLayer: function(feature, latlng) {
                        var heading = feature.properties.heading || 0;
                        var speedRaw = feature.properties.speed || 0;
                        
                        // Apply speed conversion factor
                        var speed = speedRaw * {{ this.speed_conversion }};
                        
                        {% if this.boat_color %}
                        // Use custom boat color
                        var boatColor = '{{ this.boat_color }}';
                        {% else %}
                        // Determine boat color based on speed with custom threshold
                        var boatColor = '#d30000';  // Red for stopped
                        if (speed > 0 && speed < {{ this.speed_threshold }}) {
                            boatColor = '#ffa500';  // Orange for slow
                        } else if (speed >= {{ this.speed_threshold }}) {
                            boatColor = '#008000';  // Green for moving
                        }
                        {% endif %}
                        
                        // Create custom boat-shaped icon
                        var icon = L.divIcon({
                            className: 'boat-marker-{{ this.get_name() }}',
                            html: `
                                <div style="transform: rotate(${heading}deg); transform-origin: center;">
                                    <svg width="40" height="40" viewBox="0 0 40 40" style="overflow: visible;">
                                        <!-- Boat hull -->
                                        <path d="M 20 6 L 27 26 L 20 32 L 13 26 Z" 
                                              fill="${boatColor}" 
                                              stroke="white" 
                                              stroke-width="2"
                                              opacity="0.95"/>
                                        <!-- Bow (front) -->
                                        <circle cx="20" cy="6" r="3" fill="white" stroke="${boatColor}" stroke-width="1.5"/>
                                        <!-- Deck details -->
                                        <line x1="16" y1="18" x2="24" y2="18" stroke="white" stroke-width="1.5" opacity="0.7"/>
                                        <line x1="17" y1="23" x2="23" y2="23" stroke="white" stroke-width="1.5" opacity="0.7"/>
                                    </svg>
                                </div>
                            `,
                            iconSize: [40, 40],
                            iconAnchor: [20, 20]
                        });
                        
                        return L.marker(latlng, {icon: icon});
                    },
                    onEachFeature: function(feature, layer) {
                        var props = feature.properties;
                        var speedRaw = props.speed || 0;
                        var speed = speedRaw * {{ this.speed_conversion }};
                        var status = speedRaw === 0 ? '🔴 Stopped' : '🟢 Moving';
                        
                        layer.bindPopup(`
                            <div style="font-family: Arial, sans-serif; min-width: 200px;">
                                <h4 style="margin: 0 0 10px 0;">{{ this.vessel_name }}</h4>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 4px; font-weight: bold;">Status:</td>
                                        <td style="padding: 4px;">${status}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 4px; font-weight: bold;">Speed:</td>
                                        <td style="padding: 4px;">${speed.toFixed(2)} {{ this.speed_unit }}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 4px; font-weight: bold;">Heading:</td>
                                        <td style="padding: 4px;">${props.heading.toFixed(2)}°</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 4px; font-weight: bold;">Time:</td>
                                        <td style="padding: 4px; font-size: 11px;">${new Date(props.influxtime).toLocaleString()}</td>
                                    </tr>
                                </table>
                            </div>
                        `);
                        
                        layer.bindTooltip(`Speed: ${speed.toFixed(1)} {{ this.speed_unit }} | Heading: ${props.heading.toFixed(0)}°`);
                    }
                });
                positionGroup.addLayer(positionLayer);
                {% endif %}
                
                {% if this.add_layer_control %}
                // Add layer control
                L.control.layers({}, {
                    'Ship Track (Historical)': trackGroup,
                    'Real-time Position': positionGroup
                }, {
                    collapsed: false
                }).addTo(map);
                {% endif %}
                
                console.log('Ship tracker initialized');
            }
        })();
        {% endmacro %}
    """)
    
    def __init__(
        self,
        realtime_source=None,
        track_source=None,
        track_data=None,
        update_interval=5000,
        show_realtime=True,
        show_track=True,
        track_style=None,
        vessel_name='Vessel',
        auto_center=True,
        add_layer_control=True,
        show_track_markers=True,
        boat_color=None,  # Custom boat color (overrides speed-based coloring)
        boat_size=None,   # Boat marker size (default: medium)
        speed_threshold=5.5,  # Speed threshold for slow/moving (default: 5.5 knots)
        speed_conversion=1.0,  # Speed conversion factor (e.g., 0.539957 for km/h to knots)
        speed_unit='knots',  # Display unit for speed
        **kwargs
    ):
        super().__init__()
        self._name = 'ShipTracker'
        
        self.realtime_source = realtime_source
        self.track_source = track_source
        self.track_data = track_data
        self.update_interval = update_interval
        self.show_realtime = show_realtime
        self.show_track = show_track
        self.vessel_name = vessel_name
        self.auto_center = auto_center
        self.add_layer_control = add_layer_control
        self.show_track_markers = show_track_markers
        self.boat_color = boat_color
        self.boat_size = boat_size or 'medium'
        self.speed_threshold = speed_threshold
        self.speed_conversion = speed_conversion
        self.speed_unit = speed_unit
        
        # Create feature group names that Folium can reference
        self._track_group_name = f'ship_track_{id(self)}'
        self._position_group_name = f'ship_position_{id(self)}'
        
        # Default track styling
        self.track_style = track_style or {
            'color': '#2E86AB',
            'weight': 3,
            'opacity': 0.8,
            'lineJoin': 'round',
            'lineCap': 'round'
        }
        
        # Extract style properties for template
        self.track_color = self.track_style.get('color', '#2E86AB')
        self.track_weight = self.track_style.get('weight', 3)
        self.track_opacity = self.track_style.get('opacity', 0.8)
        self.track_line_join = self.track_style.get('lineJoin', 'round')
        self.track_line_cap = self.track_style.get('lineCap', 'round')
    
    def render(self, **kwargs):
        super().render(**kwargs)
        
        # Add CSS for boat marker
        css = Element('''
            <style>
                .boat-marker { background: none; border: none; }
            </style>
        ''')
        self._parent.get_root().html.add_child(css)
        
        # Add Leaflet Realtime library
        realtime_js = Element('''
            <script src="https://unpkg.com/leaflet-realtime@2.2.0/dist/leaflet-realtime.js"></script>
        ''')
        self._parent.get_root().html.add_child(realtime_js)
    
    def add_to(self, parent, **kwargs):
        """Add the ship tracker to a map"""
        super().add_to(parent, **kwargs)
        
        # Handle static track data if provided
        if self.track_data and not self.track_source:
            self._add_static_track(parent)
        
        return self
    
    def _add_static_track(self, parent_map):
        """Add static track data using GeoJson"""
        GeoJson(
            self.track_data,
            style_function=lambda feature: self.track_style
        ).add_to(parent_map)
        
        # Add start and end markers
        if self.track_data.get('features'):
            coords = self.track_data['features'][0]['geometry']['coordinates']
            if len(coords) >= 2:
                CircleMarker(
                    location=[coords[0][1], coords[0][0]],
                    radius=8,
                    color='green',
                    fill=True,
                    fillColor='green',
                    fillOpacity=0.8,
                    popup=f'<b>{self.vessel_name}</b><br>Track Start'
                ).add_to(parent_map)
                
                CircleMarker(
                    location=[coords[-1][1], coords[-1][0]],
                    radius=8,
                    color='red',
                    fill=True,
                    fillColor='red',
                    fillOpacity=0.8,
                    popup=f'<b>{self.vessel_name}</b><br>Track End'
                ).add_to(parent_map)
    
    def add_waypoint(self, lat, lon, name, **marker_kwargs):
        """
        Add a waypoint marker to the map
        
        Parameters
        ----------
        lat : float
            Latitude of the waypoint
        lon : float
            Longitude of the waypoint
        name : str
            Name/label for the waypoint
        **marker_kwargs
            Additional arguments passed to folium.Marker
        """
        if hasattr(self, '_parent') and self._parent:
            Marker(
                location=[lat, lon],
                popup=Popup(f'<b>Waypoint:</b> {name}', max_width=200),
                tooltip=name,
                **marker_kwargs
            ).add_to(self._parent)
        
        return self
