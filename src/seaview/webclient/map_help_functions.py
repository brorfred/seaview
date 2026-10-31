
import folium
import numpy as np
from branca.element import Template, MacroElement



def add_link_to_layer_control(folium_map, url, text, **style_kwargs):
    """Add a clickable link to the bottom of the layer control."""
    from branca.element import Template, MacroElement

    styles = {
        'font-size': '11px',
        'color': '#0078A8',
        **style_kwargs
    }
    style_str = '; '.join(f'{k}: {v}' for k, v in styles.items())

    if isinstance(url, str):
        link = f'<div><a href="{url}" target="_blank" style="{style_str}">{text}</a></div>'
    else:
        link = ""
        for url,text in zip(url, text):
            link += f'<div><a href="{url}" target="_blank" style="{style_str}">{text}</a></div>'

    template = f"""
    {{% macro script(this, kwargs) %}}
    document.addEventListener('DOMContentLoaded', function() {{
        var layerControl = document.querySelector('.leaflet-control-layers-list');
        if (layerControl) {{
            var link = document.createElement('div');
            link.innerHTML = '{link}';
            link.style.marginTop = '5px';
            link.style.paddingTop = '5px';
            link.style.borderTop = '1px solid #ddd';
            layerControl.appendChild(link);
        }}
    }});
    {{% endmacro %}}
    """

    macro = MacroElement()
    macro._template = Template(template)
    folium_map.get_root().add_child(macro)
