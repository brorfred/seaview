"""
Colorbar component for Folium maps.
"""

from branca.element import MacroElement
from jinja2 import Template
from .utils import generate_colorbar_image


class ColorbarBox(MacroElement):
    """
    A customizable colorbar box for Folium maps.

    This class creates a container that displays multiple matplotlib colorbars
    on a Folium map. The box can be positioned in any corner and optionally
    integrated with the LayerControl for show/hide functionality.

    Parameters
    ----------
    position : str, default 'bottomleft'
        Position of the colorbar box. Options: 'topleft', 'topright',
        'bottomleft', 'bottomright'
    title : str, default 'Legend'
        Title displayed at the top of the colorbar box
    name : str, default 'Colorbars'
        Name for layer control integration. If using LayerControl,
        create a FeatureGroup with this exact name to enable toggle functionality
    opacity : float, default 0.95
        Background opacity of the colorbar box. Range: 0.0 (transparent) to 1.0 (opaque)
        Common values:
        - 1.0: Fully opaque (solid white background)
        - 0.95: Nearly opaque (default, slight transparency)
        - 0.85: Semi-transparent (can see map through it)
        - 0.7: More transparent (good for overlay effect)
        - 0.5: Half transparent (very light background)

    Examples
    --------
    Basic usage:

    >>> import folium
    >>> from folium_colorbar import ColorbarBox
    >>>
    >>> m = folium.Map(location=[37.7749, -122.4194], zoom_start=11)
    >>> colorbar_box = ColorbarBox(position='bottomleft', opacity=0.85)
    >>> colorbar_box.add_colorbar('viridis', 0, 100, 'Temperature (°C)')
    >>> m.add_child(colorbar_box)
    >>> m.save('map.html')

    With layer control integration:

    >>> colorbar_box = ColorbarBox(name='Colorbars')
    >>> colorbar_box.add_colorbar('RdYlBu_r', 0, 40, 'Temperature (°C)')
    >>> m.add_child(colorbar_box)
    >>>
    >>> # Create matching FeatureGroup for layer control
    >>> control_layer = folium.FeatureGroup(name='Colorbars', show=True)
    >>> m.add_child(control_layer)
    >>> folium.LayerControl().add_to(m)

    Custom tick positions and labels:

    >>> colorbar_box.add_colorbar(
    ...     'RdYlGn',
    ...     vmin=0, vmax=3,
    ...     label='Air Quality',
    ...     ticks=[0, 1, 2, 3],
    ...     tick_labels=['Good', 'Moderate', 'Unhealthy', 'Hazardous']
    ... )
    """

    # Placeholder template - will be replaced in render()
    _template = Template("{% macro script(this, kwargs) %}{% endmacro %}")

    def __init__(self, position='bottomleft', title='Legend', name='Colorbars', opacity=0.95):
        super(ColorbarBox, self).__init__()
        self._name = 'ColorbarBox'
        self.position = position
        self.title = title
        self.name = name
        self.opacity = max(0.0, min(1.0, opacity))  # Clamp to 0-1 range
        self.colorbars = []
        
    def add_colorbar(self, cmap, vmin, vmax, label='', height=200, width=40,
                     ticks=None, tick_labels=None):
        """
        Add a colorbar to the box.

        Parameters
        ----------
        cmap : str or matplotlib colormap
            The colormap to use (e.g., 'viridis', 'RdYlBu_r', 'plasma')
        vmin : float
            Minimum value for the colorbar scale
        vmax : float
            Maximum value for the colorbar scale
        label : str, optional
            Label text displayed next to the colorbar
        height : int, default 200
            Height of the colorbar in pixels
        width : int, default 40
            Width of the colorbar in pixels
        ticks : list of float, optional
            Custom tick positions. If None, matplotlib will determine ticks automatically.
            Example: [0, 10, 20, 30, 40]
        tick_labels : list of str, optional
            Custom tick labels corresponding to tick positions. If None, uses tick values.
            Example: ['Low', 'Medium', 'High', 'Very High', 'Extreme']
            
        Examples
        --------
        Simple colorbar:
        
        >>> colorbar_box.add_colorbar('viridis', 0, 100, 'Temperature (°C)')
        
        Categorical data:
        
        >>> colorbar_box.add_colorbar(
        ...     'RdYlGn', 0, 3, 'Risk Level',
        ...     ticks=[0, 1, 2, 3],
        ...     tick_labels=['Low', 'Medium', 'High', 'Critical']
        ... )
        
        Percentage scale:
        
        >>> colorbar_box.add_colorbar(
        ...     'Blues', 0, 1, 'Humidity',
        ...     ticks=[0, 0.25, 0.5, 0.75, 1],
        ...     tick_labels=['0%', '25%', '50%', '75%', '100%']
        ... )
        
        Scientific notation:
        
        >>> colorbar_box.add_colorbar(
        ...     'plasma', 0, 1e6, 'Population',
        ...     ticks=[0, 5e5, 1e6],
        ...     tick_labels=['0', '500K', '1M']
        ... )
        """
        img_base64 = generate_colorbar_image(cmap, vmin, vmax, label, height, width, 
                                             ticks, tick_labels)
        self.colorbars.append({
            'image': img_base64,
            'label': label,
            'width': width
        })
        # Regenerate template with new colorbar
        self._template = Template(self._get_template_string())
    
    def _get_position_css(self):
        """Generate CSS position properties based on position string."""
        css_parts = []
        if 'top' in self.position:
            css_parts.append('top: 10px')
        if 'bottom' in self.position:
            css_parts.append('bottom: 60px')
        if 'left' in self.position:
            css_parts.append('left: 10px')
        if 'right' in self.position:
            css_parts.append('right: 10px')
        return '; '.join(css_parts)

    def _get_template_string(self):
        """Generate the JS template string that injects HTML into the map."""
        # Build colorbars HTML as a JS string
        colorbar_items = []
        for cb in self.colorbars:
            # Escape any special characters for JS string
            label = cb['label'].replace("'", "\\'")
            colorbar_items.append(
                f'<div class="colorbar-container">'
                f'<img src="data:image/png;base64,{cb["image"]}" '
                f'alt="{label}">'
                f'</div>'
            )
        colorbar_html = ''.join(colorbar_items)
        position_css = self._get_position_css()

        template_str = f'''
        {{% macro script(this, kwargs) %}}
        (function() {{
            // Wait for map to be ready
            var checkMap = setInterval(function() {{
                if (typeof {{{{ this._parent.get_name() }}}} !== 'undefined') {{
                    clearInterval(checkMap);
                    initColorbarBox();
                }}
            }}, 100);

            function initColorbarBox() {{
                var map = {{{{ this._parent.get_name() }}}};
                var mapContainer = map.getContainer();

                // Create and inject CSS
                var style = document.createElement('style');
                style.textContent = `
                    .colorbar-box {{
                        position: absolute;
                        {position_css};
                        background: rgba(255, 255, 255, {self.opacity});
                        backdrop-filter: blur(10px);
                        padding: 12px 15px;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                        z-index: 1000;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                        pointer-events: auto;
                        resize: both;
                        overflow: hidden;
                        min-width: 100px;
                        min-height: 80px;
                    }}

                    .leaflet-container.leaflet-fullscreen-on .colorbar-box {{
                        z-index: 1000;
                    }}

                    .colorbar-box.hidden {{
                        display: none;
                    }}

                    .colorbar-box-title {{
                        margin: 0 0 10px 0;
                        font-size: 11px;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                        color: #333;
                        opacity: 0.8;
                    }}

                    .colorbar-box-content {{
                        display: flex;
                        flex-direction: row;
                        gap: 4px;
                        align-items: stretch;
                        height: calc(100% - 30px);
                    }}

                    .colorbar-container {{
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        flex: 1;
                        min-width: 0;
                    }}

                    .colorbar-container img {{
                        height: 100%;
                        width: auto;
                        object-fit: contain;
                    }}
                `;
                document.head.appendChild(style);

                // Create colorbar box element
                var colorbarBox = document.createElement('div');
                colorbarBox.className = 'colorbar-box';
                colorbarBox.id = 'colorbar-box-{{{{ this.get_name() }}}}';
                colorbarBox.innerHTML = `
                    <div class="colorbar-box-title">{self.title}</div>
                    <div class="colorbar-box-content">
                        {colorbar_html}
                    </div>
                `;

                // Add to map container
                mapContainer.appendChild(colorbarBox);

                // Layer control integration
                var controlName = '{self.name}';
                setTimeout(function() {{
                    var inputs = document.querySelectorAll('.leaflet-control-layers-overlays input[type="checkbox"]');
                    inputs.forEach(function(input) {{
                        var label = input.parentElement;
                        var labelText = label.textContent.trim();
                        if (labelText === controlName) {{
                            if (!input.checked) {{
                                colorbarBox.classList.add('hidden');
                            }}
                            input.addEventListener('change', function() {{
                                if (this.checked) {{
                                    colorbarBox.classList.remove('hidden');
                                }} else {{
                                    colorbarBox.classList.add('hidden');
                                }}
                            }});
                        }}
                    }});
                }}, 500);

                console.log('Colorbar box initialized');
            }}
        }})();
        {{% endmacro %}}
        '''

        return template_str
    
    def render(self, **kwargs):
        """Render the colorbar box."""
        # Update template with current colorbars before rendering
        self._template = Template(self._get_template_string())
        super().render(**kwargs)
