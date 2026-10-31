# Changelog

All notable changes to this project are documented in this file. The format
is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-10-31

First tagged release, covering all development to date.

### Added

- Slippy map tiles from SSH (CMEMS), SST (OSTIA), chlorophyll (GlobColour) and
  GEBCO bathymetry.
- OLCI swath tiler and early work on a level 2 tiler.
- Per-cruise configuration in `settings.toml` through dynaconf environments.
- `layer_config.json` generation and date range updates for the web map.
- rsync of tiles to a remote server, always covering the last two days.
- `sea` command line interface, documentation site and test suite.
- Podman/Docker container and usage instructions.

### Changed

- Renamed the package from `seastate` to `seaview`.
- Colormaps are resolved through the `cmap` package.
