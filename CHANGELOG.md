# Changelog

All notable changes to this project are documented in this file. The format
is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2026-10-31

### Added

- Printed error message when generating a tile fails.
- Server filesystem setup notes in the README.

### Changed

- Default zoom levels extended to z11, new default SSH colormap, and a wider
  SSH range for the `ecoa` cruise.
- `force` is now passed through to `open_dataset` in the tile functions.
- Data files with under 1% valid coverage are deleted and downloaded again.

### Fixed

- Transparent gaps between tiles at high zoom on coarse grids, and many
  blank tiles at z10 and z11. Existing tiles must be regenerated.
- `qhull` errors for tiles whose data points all lie on one line.
- Partial tile files left behind by interrupted runs.
- Declared `cmap` as a dependency.
- SSH resolution label, from 1/125° to 1/8°.

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

[0.5.1]: https://github.com/brorfred/seastate/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/brorfred/seastate/releases/tag/v0.5.0
