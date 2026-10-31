# Seaview - A Cruise Support Processor

[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](docs/)

A Python package for generating slippy map tiles from oceanographic satellite data for research cruise support. The processor retrieves near-real-time (NRT) data from Copernicus Marine Service and generates web-ready map tiles for visualization.

## Features

- **Automated Data Retrieval**: Downloads oceanographic data from Copernicus Marine Service and CEDA
  - Sea Surface Height (SSH) from DUACS L4 altimetry
  - Sea Surface Temperature (SST) from OSTIA
  - Chlorophyll concentration from GlobColour
  - Bathymetry from GEBCO
- **Slippy Map Tile Generation**: Creates standard XYZ tiles compatible with Leaflet, OpenLayers, and other web mapping libraries
- **Parallel Processing**: Multi-core tile generation for fast processing
- **Configurable Regions**: Define custom geographic bounds for your cruise area
- **Remote Sync**: Sync tiles to a remote web server via SSH

## Installation

### Using uv (recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package installer and resolver.

```bash
# Clone the repository
git clone https://github.com/brorfred/seaview.git
cd seaview

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Using pip

```bash
git clone https://github.com/brorfred/seaview.git
cd seaview
pip install -e ".[dev]"
```

### Using pixi

This project also supports [pixi](https://pixi.sh) for conda-based dependency management (recommended for complex geospatial dependencies).

```bash
git clone https://github.com/brorfred/seaview.git
cd seaview
pixi install
```

### Using Podman/Docker

Run seaview in a container using Podman (or Docker):

```bash
# Build the container image
podman build -t seaview .

# Run interactively with IPython
podman run --rm -it seaview pixi run ipython

# Run a specific command
podman run --rm seaview pixi run python -c "from seaview import tile; tile.all('2026-01-15')"

# Mount local directories for data persistence
podman run --rm -it \
    -v ~/.config/seaview:/root/.config/seaview:ro \
    -v /path/to/data:/data \
    seaview pixi run ipython
```

#### Save the container to a local file
```bash

# Commit the running container to an image                                  
podman commit seaview seaview:tag                             
                                                                              
# Save the image to a tar file                                                
podman save -o my-seaview.tar seaview:tag                                    
                                                                                
# Load it later
podman load -i seaview.tar
```
This approach preserves image layers, history, entrypoint, env vars, etc. Use if you want a full image.  

#### Export the container to a local file
```bash
podman export seaview -o seaview.tar                      

# Later import the container as an image
podman import seaview.tar seaview:tag
```
This is a flat filesystem snapshot with no metadata included. The result is a smaller file any image config is lost.                                             
**Note:** Replace `podman` with `docker` if using Docker instead.

### Prerequisites

- Python 3.11+
- [Copernicus Marine Service account](https://data.marine.copernicus.eu/) (free registration required)
- Configure your Copernicus credentials:
  ```bash
  copernicusmarine login
  ```

## Quick Start

```python
from seaview import tile

# Generate tiles for a specific date
tile.all("2026-01-15")

# Or generate individual products
tile.ssh("2026-01-15")         # Sea Surface Height
tile.sst("2026-01-15")         # Sea Surface Temperature
tile.globcolour("2026-01-15")  # Chlorophyll
```

## Configuration

Configuration is managed using [Dynaconf](https://www.dynaconf.com/). Create a `settings.toml` file in your project directory:

```toml
[DEFAULT]
base_tile_dir = "/path/to/tile/output/"
base_data_dir = "/path/to/data/cache/"
remote_html_dir = "/var/www/html/cruise/"
remote_server = "yourserver"

# Cruise Specific Information
cruise_name = "your_cruise_name"
lat1 = -55        # Southern boundary
lat2 = -10        # Northern boundary
lon1 = -75        # Western boundary
lon2 = -5         # Eastern boundary
zoom_levels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Directories (use @format for interpolation)
data_dir = "@format {this.base_data_dir}/{this.cruise_name}"
tile_dir = "@format {this.base_tile_dir}/{this.cruise_name}"
remote_tile_dir = "@format {this.remote_html_dir}/tiles/{this.cruise_name}"
```

Settings are loaded from multiple locations (in order of precedence):
1. `/etc/seaview/settings.toml` (system-wide)
2. `~/.config/seaview/settings.toml` (user)
3. `./settings.toml` (project directory)

Environment variables prefixed with `SEAVIEW_` will override settings.

## Project Structure

```
seaview/
├── src/seaview/
│   ├── __init__.py
│   ├── config.py              # Dynaconf settings loader
│   ├── cli.py                 # Command-line interface
│   ├── tile.py                # Main tile generation orchestration
│   ├── layer_config.py        # Web layer configuration management
│   ├── area_definitions.py    # Geographic projection utilities
│   ├── data_sources/          # Data retrieval modules
│   │   ├── cmems_ssh.py       # Sea Surface Height (Copernicus)
│   │   ├── ostia.py           # Sea Surface Temperature (OSTIA)
│   │   ├── globcolour.py      # Chlorophyll (GlobColour)
│   │   └── gebco_bathy.py     # Bathymetry (GEBCO)
│   ├── tilers/
│   │   ├── rectlinear.py      # Slippy tile generator
│   │   └── utils.py           # Tile utility functions
│   └── readers/
│       └── copernicus_ssh.py  # SatPy file handler for SSH
├── docs/                      # MkDocs documentation
├── tests/
│   └── test_processor.py      # Test suite
├── settings.toml              # Configuration file
├── mkdocs.yml                 # Documentation configuration
├── pixi.toml                  # Pixi dependencies
└── pyproject.toml             # Python package configuration
```

## Setup Filesystem on Server

Slippy tiles are millions of small PNG/WebP files organized in z/x/y directory hierarchies, which creates specific I/O patterns. Here are some suggestions to tune EXT4 for this workload according to Claude:
```bash
mkfs.ext4 -b 4096 -O dir_index,extent,sparse_super2 -N 50000000  /dev/disk/by-id/scsi-0HC_Volume_105089638

mount -o defaults,noatime,nodiratime,data=writeback,barrier=0,commit=60 /dev/disk/by-id/scsi-0HC_Volume_105089638 /home/bror/cruise/tiles

echo "/dev/disk/by-id/scsi-0HC_Volume_105089638 /home/bror/cruise/tiles ext4 defaults,noatime,nodiratime,data=writeback,barrier=0,commit=60 0 0" >> /etc/fstab
```
Check with
```bash
sudo findmnt --verify --verbose
```
more detailed information:

1. Format-Time Options (most impactful)
```bash
bashmkfs.ext4 -b 4096 \
  -T largefile4 \          # Fewer inodes (adjust if you have billions of tiles)
  -E stride=8,stripe-width=64 \  # Match your RAID/SSD geometry
  -O dir_index,extent,sparse_super2 \
  /dev/sdX
Increase inode count if you expect hundreds of millions of tiles:
bashmkfs.ext4 -N 50000000 /dev/sdX   # Explicitly set inode count
```

2. Mount Options (`/etc/fstab`)
```bash
/dev/sdX /tiles ext4 defaults,noatime,nodiratime,data=writeback,barrier=0,commit=60 0 2
OptionReasonnoatime / nodiratimeEliminates access-time writes on every tile read — huge windata=writebackFastest journaling mode; safe with barrier=0 on UPS-backed storagebarrier=0Skips write barriers; only safe if you have battery-backed cachecommit=60Batches journal commits (default is 5s)
```

3. Tune Directory Indexing
Tile directories hold thousands of files. Enable dir_index (HTree) if not already on:
```bash
bashtune2fs -O dir_index /dev/sdX
e2fsck -D /dev/sdX   # Rebuild directory indexes
```

4. Readahead Tuning
Tile serving is mostly random small reads, so reduce readahead to avoid wasted I/O:
```bash
bashblockdev --setra 256 /dev/sdX   # 128 KB (default is often 256–512 KB)
```
Make persistent via `/etc/udev/rules.d/60-tiles.rules`:
```bash
ACTION=="add", KERNEL=="sdX", ATTR{bdi/read_ahead_kb}="128"
```

5. Inode Size
If tiles have many extended attributes (e.g., nginx caching metadata), use a larger inode:
```bash
bashmkfs.ext4 -I 256 /dev/sdX   # Default is 256 on modern systems; 
```
verify with dumpe2fs

6. Directory Structure Consideration
EXT4 handles the z/x/y.png hierarchy well, but for very deep zoom levels (z15+), consider splitting the tile store across multiple volumes by zoom level to keep directory sizes manageable.

7. Scheduler (if on spinning disk)
```bash
bashecho mq-deadline > /sys/block/sdX/queue/scheduler
```
For SSDs/NVMe, none or kyber is better.



## API Reference

### tile

Main module for generating tiles.

```python
from seaview import tile

# Generate all products for a date
tile.all(dtm, verbose=False)

# Generate specific products
tile.ssh(dtm, verbose=True)
tile.sst(dtm, verbose=True)
tile.globcolour(dtm, verbose=True)

# Sync tiles to remote server
tile.sync()
```

**Parameters:**
- `dtm`: Date string (e.g., "2026-01-15") or datetime object
- `verbose`: Enable verbose output (default: True for individual functions)
- `force`: Re-generate tiles even if they already exist (default: True)

### layer_config

Manages the `layer_config.json` file for web map layer configuration.

```python
from seaview import layer_config

# Update date ranges from existing tiles
layer_config.update()

# Generate a sample layer_config.json
layer_config.generate_file("./")

# Sync configuration to remote server
layer_config.sync()
```

### area_definitions

Geographic projection and grid utilities.

```python
from seaview import area_definitions

# Get Web Mercator resolution for a zoom level
resolution = area_definitions.zoom_to_resolution_m(zoom=5)

# Create a Web Mercator area definition
area = area_definitions.webmercator(
    lat1=-45, lat2=-10, lon1=-70, lon2=-10,
    zoom=6
)

# Create a NASA rectilinear grid
area = area_definitions.nasa(resolution="4km")
```

### SlippyTileGenerator

Low-level tile generation class.

```python
from seaview.tilers.rectlinear import SlippyTileGenerator

generator = SlippyTileGenerator(
    min_lat=-45,
    max_lat=-10,
    min_lon=-70,
    max_lon=-10
)

generator.generate_tiles(
    scene_data=data_array,        # 2D numpy array
    scene_lats=latitudes,         # 1D or 2D array
    scene_lons=longitudes,        # 1D or 2D array
    output_dir="/path/to/tiles",
    zoom_levels=[0, 1, 2, 3, 4, 5],
    cmap="viridis",               # Matplotlib colormap
    levels=20,                    # Number of contour levels
    vmin=10,                      # Minimum value
    vmax=28,                      # Maximum value
    num_workers=10                # Parallel workers
)
```

## Data Sources

### Sea Surface Height (SSH)

- **Source**: Copernicus Marine Service
- **Dataset**: `cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D`
- **Resolution**: 0.125° (~14 km)
- **Variables**: Sea Level Anomaly (SLA), Absolute Dynamic Topography (ADT), Geostrophic currents
- **Reference**: [SEALEVEL_GLO_PHY_L4_NRT_008_046](https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_NRT_008_046)

### Sea Surface Temperature (SST)

- **Source**: UK Met Office OSTIA via Copernicus Marine Service
- **Dataset**: `METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2`
- **Resolution**: ~5 km
- **Reference**: [SST_GLO_SST_L4_NRT_OBSERVATIONS_010_001](https://data.marine.copernicus.eu/product/SST_GLO_SST_L4_NRT_OBSERVATIONS_010_001)

### Chlorophyll (GlobColour)

- **Source**: Copernicus Marine Service GlobColour
- **Dataset**: `cmems_obs-oc_glo_bgc-plankton_nrt_l3-multi-4km_P1D`
- **Resolution**: 4 km
- **Reference**: [OCEANCOLOUR_GLO_BGC_L3_NRT_009_101](https://data.marine.copernicus.eu/product/OCEANCOLOUR_GLO_BGC_L3_NRT_009_101)

### Bathymetry (GEBCO)

- **Source**: CEDA via OPeNDAP
- **Dataset**: GEBCO 2025 Sub-Ice Topography
- **Resolution**: 15 arc-second (~450m)
- **Reference**: [GEBCO Gridded Bathymetry Data](https://www.gebco.net/data_and_products/gridded_bathymetry_data/)

## Output Format

Generated tiles follow the standard slippy map tile naming convention:

```
{tile_dir}/{product}/{date}/{z}/{x}/{y}.png
```

Example:
```
/data/tiles/bioreactors1/ssh/2026-01-15/5/12/18.png
```

### Layer Configuration

The `layer_config.json` file configures the web map layer panel:

```json
{
  "base_url": "https://yourserver.com/cruise/tiles/cruisename",
  "layers": [
    {
      "id": "ssh",
      "name": "SSH CMEMS 0.125°",
      "url_template": "{base_url}/ssh/{date}/{z}/{x}/{y}.png",
      "attribution": "Copernicus SSH -0.75–0.75 m",
      "date_range": {
        "start": "2026-01-08",
        "end": "2026-01-14"
      }
    }
  ]
}
```

## Running Tests

```bash
# Using uv/pip
pytest tests/ -v

# Using pixi
pixi run python -m pytest tests/ -v
```

## Batch Processing

Process multiple days:

```python
import pandas as pd
from seaview import tile

# Generate tiles for a date range
for date in pd.date_range("2026-01-01", "2026-01-15"):
    print(f"Processing {date.date()}")
    tile.all(date)
```

## Dependencies

Key dependencies managed via pixi:

- **Data handling**: numpy, xarray, pandas, netCDF4
- **Geospatial**: pyresample, pyproj, satpy, mercantile
- **Visualization**: matplotlib, pillow
- **Data access**: copernicusmarine
- **Remote sync**: sysrsync

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes
4. Run tests (`pixi run python -m pytest tests/ -v`)
5. Commit your changes (`git commit -am 'Add new feature'`)
6. Push to the branch (`git push origin feature/new-feature`)
7. Open a Pull Request

## License

[Add your license here]

## Documentation

Full documentation is available in the `docs/` directory and can be built with MkDocs:

```bash
# Install documentation dependencies
pip install mkdocs mkdocs-material mkdocstrings[python]

# Serve documentation locally
mkdocs serve

# Build static documentation
mkdocs build
```

## Acknowledgments

- [Copernicus Marine Service](https://marine.copernicus.eu/) for providing oceanographic data
- [GEBCO](https://www.gebco.net/) for bathymetry data
- [SatPy](https://satpy.readthedocs.io/) for satellite data processing capabilities
- [Pyresample](https://pyresample.readthedocs.io/) for geographic resampling
