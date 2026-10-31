"""
Cruise Track Plugin for Folium
Displays cruise stations from GeoJSON with interactive tooltips and popups
"""

import json
import urllib.request
import urllib.error
from folium import FeatureGroup, CircleMarker, PolyLine, Tooltip, Popup
from jinja2 import Template


class CruiseTrack(FeatureGroup):
    """
    A folium plugin to display cruise track stations from GeoJSON data.
    
    Parameters
    ----------
    geojson_file : str
        Path to a local GeoJSON file or URL to a GeoJSON file
    name : str, default 'Cruise Track'
        Name of the feature group layer
    show : bool, default True
        Whether the layer is visible by default
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
    popup_max_width : int, default 300
        Maximum width of the popup in pixels
    
    Examples
    --------
    >>> import folium
    >>> from folium_plugins.cruise_track import CruiseTrack
    >>> 
    >>> # Load from local file
    >>> m = folium.Map(location=[-35, -45], zoom_start=5)
    >>> CruiseTrack('cruise_stations.geojson').add_to(m)
    >>> m.save('map.html')
    >>> 
    >>> # Load from URL
    >>> m = folium.Map(location=[-35, -45], zoom_start=5)
    >>> CruiseTrack('https://example.com/cruise_stations.geojson').add_to(m)
    >>> m.save('map.html')
    
    GeoJSON Format
    --------------
    The GeoJSON file should have the following structure:
    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
          },
          "properties": {
            "name": "Station 1",
            "arrive": "2024-01-15",
            "departure": "2024-01-16",
            "comments": "Station description",
            "depth": "~1336m",
            "duration": "0d 19h 0m"
          }
        }
      ]
    }
    """
    
    # No custom template needed - use default FeatureGroup behavior
    
    def __init__(
        self,
        geojson_file,
        name='Cruise Track',
        show=True,
        marker_color='green',
        marker_radius=8,
        line_color='blue',
        line_weight=2,
        line_opacity=0.5,
        popup_max_width=300,
        overlay=True,
        control=True,
        **kwargs
    ):
        super(CruiseTrack, self).__init__(
            name=name, 
            show=show, 
            overlay=overlay, 
            control=control,
            **kwargs
        )
        
        self.geojson_file = geojson_file
        self.marker_color = marker_color
        self.marker_radius = marker_radius
        self.line_color = line_color
        self.line_weight = line_weight
        self.line_opacity = line_opacity
        self.popup_max_width = popup_max_width
        self._loaded = False
    
    def add_to(self, parent, name=None, index=None):
        """Override add_to to load data when adding to map."""
        if not self._loaded:
            self._load_and_render()
            self._loaded = True
        return super(CruiseTrack, self).add_to(parent, name=name, index=index)
    
    def _load_and_render(self):
        """Load GeoJSON data and create markers and track line."""
        
        # Load data from GeoJSON file or URL
        try:
            if self.geojson_file.startswith(('http://', 'https://')):
                # Load from URL
                import urllib.request
                with urllib.request.urlopen(self.geojson_file) as response:
                    data = json.loads(response.read().decode('utf-8'))
            else:
                # Load from local file
                with open(self.geojson_file, 'r') as f:
                    data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"GeoJSON file not found: {self.geojson_file}")
        except urllib.error.URLError as e:
            raise ValueError(f"Failed to load GeoJSON from URL: {self.geojson_file}. Error: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.geojson_file}: {e}")
        
        # Extract coordinates and properties
        stations = []
        station_info = []
        
        for feature in data.get('features', []):
            coords = feature['geometry']['coordinates']
            # GeoJSON uses [lon, lat], but folium uses [lat, lon]
            lat, lon = coords[1], coords[0]
            stations.append((lat, lon))
            
            # Extract properties
            props = feature.get('properties', {})
            station_info.append({
                'arrive': props.get('arrive', 'N/A'),
                'departure': props.get('departure', 'N/A'),
                'name': props.get('name', 'N/A'),
                'comments': props.get('comments', ''),
                'depth': props.get('depth', ''),
                'duration': props.get('duration', '')
            })
        
        # Add markers with tooltips and popups
        for (lat, lon), info in zip(stations, station_info):
            marker = CircleMarker(
                location=[lat, lon],
                radius=self.marker_radius,
                color=self.marker_color,
                weight=3,
                fill=True,
                fill_color=self.marker_color,
                fill_opacity=0.6,
                opacity=1
            )
            
            # Add tooltip
            tooltip_text = f"{info['name']} - {info['arrive']}"
            Tooltip(tooltip_text).add_to(marker)
            
            # Add popup
            popup_html = f"""
            <b>Station:</b> {info['name']}<br>
            <b>Arrival:</b> {info['arrive']}<br>
            <b>Departure:</b> {info['departure']}<br>
            """
            
            if info.get('depth'):
                popup_html += f"<b>Depth:</b> {info['depth']}<br>"
            
            if info.get('duration'):
                popup_html += f"<b>Duration:</b> {info['duration']}<br>"
            
            if info.get('comments'):
                popup_html += f"<b>Comments:</b> {info['comments']}<br>"
            
            Popup(popup_html, max_width=self.popup_max_width).add_to(marker)
            
            marker.add_to(self)
        
        # Add the cruise track line (after markers so they're on top)
        if len(stations) > 1:
            PolyLine(
                stations,
                color=self.line_color,
                weight=self.line_weight,
                opacity=self.line_opacity
            ).add_to(self)
