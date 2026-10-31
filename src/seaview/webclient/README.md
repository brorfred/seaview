# Dynamic Layer Loading for Folium Map

This solution provides two approaches for loading GroupedLayerControl data dynamically:

## Approach 1: Configuration File (Simple)

**Best for:** Updating layer configurations between map regenerations

### Files:
- `layer_config.json` - Configuration file for date ranges and layer settings
- `refactored_map.py` - Modified Python script that reads from config file

### Usage:
1. Edit `layer_config.json` to change date ranges or layer settings
2. Run `python refactored_map.py` to regenerate the map
3. The map will reflect the new configuration

### To update layers:
```bash
# Edit the JSON file
nano layer_config.json

# Regenerate the map
python refactored_map.py
```

### Example config update:
```json
{
  "date_ranges": {
    "ssh": {
      "start": "2026-01-12",
      "end": "2026-01-15"
    }
  }
}
```

---

## Approach 2: Flask Server (Advanced - No Page Reload)

**Best for:** True dynamic updates without page reload

### Files:
- `layer_config.json` - Configuration file
- `dynamic_map_server.py` - Flask web server

### Setup:
```bash
pip install flask pandas folium
```

### Usage:
```bash
# Start the server
python dynamic_map_server.py

# Open in browser
http://localhost:5000
```

### How it works:
1. Server serves the map at `/`
2. JavaScript polls `/api/layer-config` every 30 seconds
3. When `layer_config.json` changes, layers update automatically
4. Manual refresh button is also available

### To update layers:
```bash
# Edit the JSON file while server is running
nano layer_config.json

# Layers will update within 30 seconds
# Or click "Refresh Layers" button immediately
```

---

## Configuration File Format

```json
{
  "date_ranges": {
    "ssh": {
      "start": "2026-01-08",
      "end": "2026-01-11"
    },
    "sst": {
      "start": "2026-01-08",
      "end": "2026-01-11"
    },
    "globcolour": {
      "start": "2026-01-08",
      "end": "2026-01-11"
    }
  },
  "layer_settings": {
    "ssh": {
      "name": "SSH CMEMS 0.125°  ",
      "exclusive": false,
      "collapsed": false
    },
    "sst": {
      "name": "SST OSTIA 5km     ",
      "exclusive": false,
      "collapsed": false
    },
    "globcolour": {
      "name": "Chl GlobColour 4km",
      "exclusive": false,
      "collapsed": false
    }
  }
}
```

---

## Comparison

| Feature | Approach 1 | Approach 2 |
|---------|-----------|-----------|
| Setup complexity | Simple | Moderate |
| Page reload needed | Yes | No |
| Real-time updates | No | Yes (30s polling) |
| Dependencies | pandas, folium | + Flask |
| Best for | Periodic updates | Live monitoring |

---

## Advanced: Custom Polling Interval

In `dynamic_map_server.py`, change the polling interval:

```javascript
// Change from 30 seconds to 10 seconds
setInterval(loadLayerConfig, 10000);
```

---

## Troubleshooting

### Approach 1:
- **Layers not updating**: Make sure to run `python refactored_map.py` after editing the config
- **JSON errors**: Validate JSON syntax at jsonlint.com

### Approach 2:
- **Port already in use**: Change port in `app.run(port=5000)` to another number
- **Layers not refreshing**: Check browser console for errors
- **CORS issues**: Make sure tile URLs are accessible from browser

---

## Integration with Your Code

To integrate with your existing module structure:

1. Copy the relevant import at the top:
   ```python
   import json
   ```

2. Replace your `add_fields` function with the one from `refactored_map.py`

3. Create `layer_config.json` in the same directory as your module

4. Update the import in your module if needed:
   ```python
   from .folium_graticule import Graticule
   ```

---

## Future Enhancements

Possible additions:
- WebSocket support for instant updates (no polling)
- Database backend instead of JSON file
- User authentication for multi-user scenarios
- Layer preview thumbnails
- Automated date range updates (e.g., "last 7 days")
