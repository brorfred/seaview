"""
Interactive Folium Map with Multiple Controllable Colorbars

This script demonstrates how to create a Folium map with multiple colorbars
that can be toggled on/off using the layer control.
"""

import folium
from branca.element import Template, MacroElement
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import base64
from io import BytesIO
import numpy as np


class ColorbarControl(MacroElement):
    """
    A custom Folium control that displays multiple matplotlib colorbars
    in a box on the map. Each colorbar can be toggled via layer control.
    """
    
    def __init__(self, colorbars_config, position='topright'):
        """
        Parameters
        ----------
        colorbars_config : list of dict
            List of colorbar configurations. Each dict should contain:
            - 'name': str, name of the colorbar (for layer control)
            - 'cmap': str or matplotlib colormap, the colormap to use
            - 'vmin': float, minimum value
            - 'vmax': float, maximum value
            - 'label': str, label for the colorbar (optional)
        position : str
            Position on the map ('topright', 'topleft', 'bottomright', 'bottomleft')
        """
        super(ColorbarControl, self).__init__()
        self._name = 'ColorbarControl'
        self.position = position
        self.colorbars_config = colorbars_config
        self.colorbar_images = self._generate_colorbar_images()
        
    def _generate_colorbar_images(self):
        """Generate base64 encoded images for each colorbar"""
        colorbar_images = []
        
        for config in self.colorbars_config:
            # Create figure for colorbar
            fig, ax = plt.subplots(figsize=(1.5, 4))
            fig.subplots_adjust(right=0.5)
            
            # Get colormap
            if isinstance(config['cmap'], str):
                cmap = cm.get_cmap(config['cmap'])
            else:
                cmap = config['cmap']
            
            # Create normalization
            norm = Normalize(vmin=config['vmin'], vmax=config['vmax'])
            
            # Create colorbar
            cb = plt.colorbar(
                cm.ScalarMappable(norm=norm, cmap=cmap),
                cax=ax,
                orientation='vertical'
            )
            
            # Set label if provided
            if 'label' in config:
                cb.set_label(config['label'], rotation=270, labelpad=20)
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', 
                       dpi=100, transparent=True)
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            colorbar_images.append({
                'name': config['name'],
                'image': img_base64,
                'label': config.get('label', config['name'])
            })
        
        return colorbar_images
    
    def _template(self):
        """Generate the HTML template for the colorbar control"""
        
        # Generate HTML for each colorbar
        colorbars_html = ""
        for i, cb_img in enumerate(self.colorbar_images):
            colorbars_html += f"""
            <div id="colorbar_{i}" class="colorbar-item" style="margin-bottom: 10px; display: none;">
                <img src="data:image/png;base64,{cb_img['image']}" 
                     style="width: 100%; height: auto;">
            </div>
            """
        
        template = f"""
        {{% macro html(this, kwargs) %}}
        
        <style>
            .colorbar-box {{
                position: absolute;
                {self.position.replace('top', 'top: 10px;').replace('bottom', 'bottom: 10px;').replace('left', 'left: 10px;').replace('right', 'right: 10px;')}
                background: white;
                padding: 10px;
                border: 2px solid rgba(0,0,0,0.2);
                border-radius: 5px;
                box-shadow: 0 0 15px rgba(0,0,0,0.2);
                z-index: 1000;
                max-width: 200px;
            }}
            
            .colorbar-item {{
                transition: opacity 0.3s;
            }}
        </style>
        
        <div id="colorbar-container" class="colorbar-box">
            <div style="font-weight: bold; margin-bottom: 10px; text-align: center; border-bottom: 1px solid #ddd; padding-bottom: 5px;">
                Colorbars
            </div>
            {colorbars_html}
        </div>
        
        <script>
            // Function to update colorbar visibility
            window.updateColorbarVisibility = function(colorbarId, visible) {{
                var element = document.getElementById(colorbarId);
                if (element) {{
                    element.style.display = visible ? 'block' : 'none';
                }}
            }};
        </script>
        
        {{% endmacro %}}
        """
        
        return template
    
    def render(self, **kwargs):
        """Render the HTML template"""
        figure = self._parent
        assert isinstance(figure, folium.Map), (
            'ColorbarControl can only be added to a Map object.'
        )
        
        super(ColorbarControl, self).render(**kwargs)


def create_colorbar_layer(map_obj, name, colorbar_id):
    """
    Create a dummy layer that controls colorbar visibility.
    This is a workaround since Folium's LayerControl works with map layers.
    """
    # Create a transparent feature group
    fg = folium.FeatureGroup(name=name, show=False)
    
    # Add JavaScript to toggle colorbar when this layer is toggled
    map_obj.get_root().html.add_child(folium.Element(f"""
    <script>
        // Wait for map to be ready
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(function() {{
                // Find the layer control checkbox for this layer
                var inputs = document.querySelectorAll('input[type="checkbox"]');
                inputs.forEach(function(input) {{
                    var label = input.parentElement;
                    if (label && label.textContent.includes('{name}')) {{
                        input.addEventListener('change', function() {{
                            updateColorbarVisibility('colorbar_{colorbar_id}', this.checked);
                        }});
                        // Set initial state
                        updateColorbarVisibility('colorbar_{colorbar_id}', input.checked);
                    }}
                }});
            }}, 500);
        }});
    </script>
    """))
    
    return fg


def main():
    """Create an example map with multiple controllable colorbars"""
    
    # Create base map centered on a location
    m = folium.Map(
        location=[37.7749, -122.4194],  # San Francisco
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Define multiple colorbars
    colorbars_config = [
        {
            'name': 'Temperature',
            'cmap': 'RdYlBu_r',
            'vmin': 0,
            'vmax': 40,
            'label': 'Temperature (°C)'
        },
        {
            'name': 'Precipitation',
            'cmap': 'Blues',
            'vmin': 0,
            'vmax': 100,
            'label': 'Precipitation (mm)'
        },
        {
            'name': 'Elevation',
            'cmap': 'terrain',
            'vmin': 0,
            'vmax': 3000,
            'label': 'Elevation (m)'
        },
        {
            'name': 'Wind Speed',
            'cmap': 'viridis',
            'vmin': 0,
            'vmax': 50,
            'label': 'Wind Speed (km/h)'
        }
    ]
    
    # Add the colorbar control
    colorbar_control = ColorbarControl(colorbars_config, position='topright')
    m.add_child(colorbar_control)
    
    # Create layers for each colorbar (for layer control integration)
    for i, config in enumerate(colorbars_config):
        layer = create_colorbar_layer(m, config['name'], i)
        m.add_child(layer)
    
    # Add some example data overlays (optional - for demonstration)
    # You can add your actual data layers here
    
    # Add example circle markers with colors corresponding to colorbars
    np.random.seed(42)
    for i in range(20):
        lat = 37.7749 + np.random.randn() * 0.1
        lon = -122.4194 + np.random.randn() * 0.1
        temp = np.random.uniform(0, 40)
        
        # Normalize temperature to get color
        norm = Normalize(vmin=0, vmax=40)
        cmap = cm.get_cmap('RdYlBu_r')
        color = plt.matplotlib.colors.rgb2hex(cmap(norm(temp)))
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            popup=f'Temperature: {temp:.1f}°C',
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7
        ).add_to(m)
    
    # Add layer control
    folium.LayerControl(position='topleft').add_to(m)
    
    # Save map
    output_file = '/mnt/user-data/outputs/colorbar_map.html'
    m.save(output_file)
    print(f"Map saved to {output_file}")
    
    return m


if __name__ == '__main__':
    main()
