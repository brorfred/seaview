"""
Realtime Layer Plugin for Folium
A proper wrapper for leaflet-realtime that correctly handles layer control names and visibility.
"""

from folium import FeatureGroup
from branca.element import Element
from jinja2 import Template


class RealtimeLayer(FeatureGroup):
    """
    A Folium plugin for displaying realtime GeoJSON data with proper layer control support.

    This plugin extends FeatureGroup to ensure proper layer control integration,
    then injects JavaScript to populate the group with realtime data.

    Parameters
    ----------
    source : str
        URL to the GeoJSON data source
    name : str, default 'Realtime Layer'
        Name to display in the layer control
    show : bool, default True
        Whether the layer is visible by default
    interval : int, default 60000
        Update interval in milliseconds
    style : dict, optional
        Style options for the GeoJSON features
    get_feature_id : str, optional
        JavaScript function to get unique feature ID
    remove_missing : bool, default False
        Whether to remove features that are no longer in the source

    Examples
    --------
    >>> import folium
    >>> from folium_plugins.realtime_layer import RealtimeLayer
    >>>
    >>> m = folium.Map(location=[0, 0], zoom_start=5)
    >>> RealtimeLayer(
    ...     source='https://example.com/data.geojson',
    ...     name='My Layer',
    ...     show=False,
    ...     interval=30000
    ... ).add_to(m)
    >>> m.save('map.html')
    """

    _template = Template("""
        {% macro script(this, kwargs) %}
            var {{ this.get_name() }} = L.featureGroup();

            // Create and configure the realtime layer
            var {{ this.get_name() }}_realtime = L.realtime(
                '{{ this.source }}',
                {
                    interval: {{ this.interval }},
                    start: true,
                    removeMissing: {{ this.remove_missing | tojson }},
                    {% if this.get_feature_id %}
                    getFeatureId: {{ this.get_feature_id }},
                    {% endif %}
                    {% if this.style %}
                    style: function(feature) {
                        return {{ this.style | tojson }};
                    },
                    {% endif %}
                }
            );

            // Add the realtime layer's container (where features are stored) to our feature group
            {{ this.get_name() }}.addLayer({{ this.get_name() }}_realtime);
        {% endmacro %}
    """)

    def __init__(
        self,
        source,
        name='Realtime Layer',
        show=True,
        interval=60000,
        style=None,
        get_feature_id=None,
        remove_missing=False,
        overlay=True,
        control=True,
        **kwargs
    ):
        super().__init__(
            name=name,
            show=show,
            overlay=overlay,
            control=control,
            **kwargs
        )

        self.source = source
        self.interval = interval
        self.style = style
        self.get_feature_id = get_feature_id
        self.remove_missing = remove_missing
        self._show = show

    def render(self, **kwargs):
        # Add the leaflet-realtime library before rendering
        if self._parent is not None:
            js = Element('''
                <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet-realtime/2.2.0/leaflet-realtime.js"></script>
            ''')
            self._parent.get_root().html.add_child(js)

        super().render(**kwargs)
