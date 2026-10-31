"""
Dynamic Layers Plugin for Folium - Working Version
"""

from branca.element import MacroElement, Template


class DynamicLayers(MacroElement):
    """Add dynamic layer loading to a Folium map."""
    
    def __init__(self, config_file='layer_config.json', refresh_interval=30000, 
                 show_refresh_link=True, position='topleft'):
        super(DynamicLayers, self).__init__()
        self._name = 'DynamicLayers'
        
        self.config_file = config_file
        self.refresh_interval = refresh_interval
        self.show_refresh_link = 'true' if show_refresh_link else 'false'
        self.position = position
        
        # DON'T include <script> tags - Folium adds them automatically
        self._template = Template("""
{% macro script(this, kwargs) %}
(function() {
    const CONFIG_FILE = {{ this.config_file|tojson }};
    const REFRESH_INTERVAL = {{ this.refresh_interval }};
    const SHOW_REFRESH_LINK = {{ this.show_refresh_link }};
    const POSITION = {{ this.position|tojson }};
    
    let dynamicLayers = {}, layerControl = null, leafletMap = null;
    
    async function loadLayerConfig() {
        try {
            const response = await fetch(CONFIG_FILE + '?t=' + Date.now());
            const config = await response.json();
            updateLayers(config);
        } catch (error) {
            console.error('[DynamicLayers]', error);
        }
    }
    
    function updateLayers(config) {
        if (!leafletMap) return;
        
        // Save current layer visibility state BEFORE removing anything
        const visibleLayers = new Set();
        Object.entries(dynamicLayers).forEach(([key, layer]) => {
            if (leafletMap.hasLayer(layer)) {
                visibleLayers.add(key);
            }
        });
        
        console.log('[DynamicLayers] Preserving visibility for:', Array.from(visibleLayers));
        
        // Remove old layers
        Object.values(dynamicLayers).forEach(layer => {
            if (leafletMap.hasLayer(layer)) leafletMap.removeLayer(layer);
        });
        if (layerControl) leafletMap.removeControl(layerControl);
        
        dynamicLayers = {};
        const groupedOverlays = {};
        
        function getDateRange(start, end) {
            const dates = [], d1 = new Date(start), d2 = new Date(end);
            for (let d = new Date(d1); d <= d2; d.setDate(d.getDate() + 1)) {
                dates.push(d.toISOString().split('T')[0]);
            }
            return dates;
        }
        
        config.layers.forEach(layerConfig => {
            const dates = getDateRange(layerConfig.date_range.start, layerConfig.date_range.end);
            const groupName = layerConfig.name;
            groupedOverlays[groupName] = {};
            
            dates.forEach(date => {
                const url = layerConfig.url_template
                    .replace('{base_url}', config.base_url)
                    .replace('{date}', date);
                
                const layer = pmtiles.leafletRasterLayer(new pmtiles.PMTiles(url), {
                    attribution: layerConfig.attribution,
                    opacity: 0.7
                });
                
                const key = layerConfig.id + '_' + date;
                dynamicLayers[key] = layer;
                groupedOverlays[groupName][date] = layer;
            });
        });
        
        // Create control first
        layerControl = L.control.groupedLayers(null, groupedOverlays, {
            collapsed: false, position: POSITION
        }).addTo(leafletMap);
        
        // Then restore visibility - this must happen AFTER control is added
        setTimeout(() => {
            Object.entries(dynamicLayers).forEach(([key, layer]) => {
                if (visibleLayers.has(key)) {
                    console.log('[DynamicLayers] Restoring:', key);
                    layer.addTo(leafletMap);
                }
            });
        }, 50);
        
        if (SHOW_REFRESH_LINK) setTimeout(addRefreshLink, 100);
    }
    
    function addRefreshLink() {
        const el = document.querySelector('.leaflet-control-layers');
        if (el && !el.querySelector('.layer-refresh-link')) {
            const link = document.createElement('a');
            link.className = 'layer-refresh-link';
            link.textContent = '🔄 Refresh layers';
            link.onclick = (e) => { e.preventDefault(); loadLayerConfig(); };
            el.appendChild(link);
        }
    }
    
    function init() {
        const mapVars = Object.keys(window).filter(k => 
            k.startsWith('map_') && window[k] && typeof window[k].addLayer === 'function'
        );
        
        if (mapVars.length > 0) {
            leafletMap = window[mapVars[0]];
            loadLayerConfig();
            if (REFRESH_INTERVAL > 0) setInterval(loadLayerConfig, REFRESH_INTERVAL);
        } else {
            setTimeout(init, 500);
        }
    }
    
    window.refreshDynamicLayers = loadLayerConfig;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => setTimeout(init, 500));
    } else {
        setTimeout(init, 500);
    }
})();
{% endmacro %}

{% macro header(this, kwargs) %}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-groupedlayercontrol@0.6.1/dist/leaflet.groupedlayercontrol.min.css" />
<script src="https://cdn.jsdelivr.net/npm/leaflet-groupedlayercontrol@0.6.1/dist/leaflet.groupedlayercontrol.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/pmtiles@4.5.0/dist/pmtiles.js"></script>
<style>
.leaflet-control-layers { padding-bottom: 0 !important; }
.layer-refresh-link {
    display: block; text-align: center; padding: 8px;
    border-top: 1px solid #ddd; margin-top: 5px; font-size: 12px;
    color: #0078A8; text-decoration: none; cursor: pointer;
}
.layer-refresh-link:hover { background-color: #f4f4f4; text-decoration: underline; }
</style>
{% endmacro %}
""")
