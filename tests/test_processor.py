"""Tests for the seaview package."""

import math
import tempfile
from pathlib import Path
from unittest.mock import patch

import mercantile
import numpy as np
import pytest
from PIL import Image

from seaview import config
from seaview import area_definitions
from seaview.tilers.rectlinear import (
    SlippyTileGenerator,
    _generate_single_tile,
    _save_tile,
    lonlat_to_webmercator,
)


class TestConfig:
    """Tests for config.py."""

    def test_settings_is_dynaconf_object(self):
        """settings should be a Dynaconf object that supports dict-like access."""
        # Should support dict-style access
        assert hasattr(config.settings, '__getitem__')
        assert hasattr(config.settings, 'get')

    def test_settings_has_required_keys(self):
        """settings should contain all required configuration keys."""
        required_keys = [
            "cruise_name",
            "lat1",
            "lat2",
            "lon1",
            "lon2",
            "tile_dir",
            "remote_html_dir",
            "remote_tile_dir",
            "data_dir",
            "zoom_levels",
        ]
        for key in required_keys:
            assert config.settings.get(key) is not None, f"Missing required key: {key}"

    def test_settings_lat_lon_are_numbers(self):
        """Lat/lon bounds should be numeric."""
        assert isinstance(config.settings["lat1"], (int, float))
        assert isinstance(config.settings["lat2"], (int, float))
        assert isinstance(config.settings["lon1"], (int, float))
        assert isinstance(config.settings["lon2"], (int, float))

    def test_settings_lat_bounds_valid(self):
        """Latitude bounds should be in valid range [-90, 90]."""
        assert -90 <= config.settings["lat1"] <= 90
        assert -90 <= config.settings["lat2"] <= 90
        assert config.settings["lat1"] < config.settings["lat2"], "lat1 should be less than lat2"

    def test_settings_lon_bounds_valid(self):
        """Longitude bounds should be in valid range [-180, 180]."""
        assert -180 <= config.settings["lon1"] <= 180
        assert -180 <= config.settings["lon2"] <= 180
        assert config.settings["lon1"] < config.settings["lon2"], "lon1 should be less than lon2"

    def test_settings_zoom_levels_list(self):
        """zoom_levels should be a list of integers."""
        zoom_levels = config.settings["zoom_levels"]
        assert isinstance(zoom_levels, list)
        assert len(zoom_levels) > 0
        for zoom in zoom_levels:
            assert isinstance(zoom, int)
            assert 0 <= zoom <= 20, "Zoom level should be between 0 and 20"

    def test_settings_paths_are_strings(self):
        """Directory paths should be strings."""
        assert isinstance(config.settings["tile_dir"], str)
        assert isinstance(config.settings["data_dir"], str)
        assert isinstance(config.settings["remote_html_dir"], str)
        assert isinstance(config.settings["remote_tile_dir"], str)

    def test_change_env_function_exists(self):
        """change_env function should exist and be callable."""
        assert callable(config.change_env)


class TestAreaDefinitions:
    """Tests for area_definitions.py."""

    def test_zoom_to_resolution_zoom_0(self):
        """Zoom level 0 should have the coarsest resolution."""
        resolution = area_definitions.zoom_to_resolution_m(0)
        # At zoom 0, resolution is approximately 156543m at equator
        assert 156000 < resolution < 157000

    def test_zoom_to_resolution_zoom_10(self):
        """Zoom level 10 should have finer resolution than zoom 0."""
        res_0 = area_definitions.zoom_to_resolution_m(0)
        res_10 = area_definitions.zoom_to_resolution_m(10)
        assert res_10 < res_0
        # At zoom 10, resolution is approximately 152m
        assert 150 < res_10 < 155

    def test_zoom_to_resolution_doubles_per_zoom(self):
        """Resolution should halve with each zoom level increase."""
        for zoom in range(0, 10):
            res_current = area_definitions.zoom_to_resolution_m(zoom)
            res_next = area_definitions.zoom_to_resolution_m(zoom + 1)
            ratio = res_current / res_next
            assert abs(ratio - 2.0) < 0.001, f"Zoom {zoom} to {zoom+1} ratio was {ratio}"

    def test_webmercator_requires_zoom_or_resolution(self):
        """webmercator() should raise ValueError if neither zoom nor resolution provided."""
        with pytest.raises(ValueError, match="Either 'zoom' or 'resolution_m' must be provided"):
            area_definitions.webmercator(lat1=-10, lat2=10, lon1=-10, lon2=10)

    def test_webmercator_with_zoom(self):
        """webmercator() should create valid AreaDefinition with zoom level."""
        area = area_definitions.webmercator(
            lat1=-10, lat2=10, lon1=-20, lon2=20, zoom=5
        )
        assert area.width > 0
        assert area.height > 0
        assert area.area_extent is not None

    def test_webmercator_with_resolution(self):
        """webmercator() should create valid AreaDefinition with resolution."""
        area = area_definitions.webmercator(
            lat1=-10, lat2=10, lon1=-20, lon2=20, resolution_m=1000
        )
        assert area.width > 0
        assert area.height > 0

    def test_webmercator_higher_zoom_more_pixels(self):
        """Higher zoom levels should result in more pixels."""
        area_low = area_definitions.webmercator(
            lat1=-10, lat2=10, lon1=-20, lon2=20, zoom=3
        )
        area_high = area_definitions.webmercator(
            lat1=-10, lat2=10, lon1=-20, lon2=20, zoom=6
        )
        assert area_high.width > area_low.width
        assert area_high.height > area_low.height

    def test_webmercator_extent_transformation(self):
        """Area extent should be in Web Mercator coordinates (meters)."""
        area = area_definitions.webmercator(
            lat1=-10, lat2=10, lon1=-20, lon2=20, zoom=5
        )
        x_min, y_min, x_max, y_max = area.area_extent
        # Web Mercator coordinates should be large numbers (meters from origin)
        assert abs(x_min) > 1000000  # Approximately 2226389m for 20 degrees
        assert abs(x_max) > 1000000

    def test_nasa_valid_resolutions(self):
        """nasa() should accept valid resolution strings."""
        for res in ["9km", "4km", "1km", "500m"]:
            area = area_definitions.nasa(resolution=res)
            assert area.width > 0
            assert area.height > 0

    def test_nasa_invalid_resolution(self):
        """nasa() should raise ValueError for invalid resolution."""
        with pytest.raises(ValueError, match="Wrong resolution"):
            area_definitions.nasa(resolution="invalid")

    def test_nasa_higher_resolution_more_pixels(self):
        """Higher resolution grids should have more pixels."""
        area_9km = area_definitions.nasa(resolution="9km")
        area_4km = area_definitions.nasa(resolution="4km")
        assert area_4km.width > area_9km.width
        assert area_4km.height > area_9km.height

    def test_nasa_subset_bounds(self):
        """nasa() with subset bounds should have fewer pixels than global."""
        area_global = area_definitions.nasa(resolution="4km")
        area_subset = area_definitions.nasa(
            resolution="4km", lat1=-45, lat2=-10, lon1=-70, lon2=-10
        )
        assert area_subset.width < area_global.width
        assert area_subset.height < area_global.height

    def test_rectlinear_creates_area(self):
        """rectlinear() should create valid AreaDefinition with given shape."""
        area = area_definitions.rectlinear(
            shape=(100, 200), lat1=-45, lat2=-10, lon1=-70, lon2=-10
        )
        assert area.width == 200
        assert area.height == 100

    def test_rectlinear_extent_matches_bounds(self):
        """rectlinear() area extent should match provided bounds."""
        lat1, lat2, lon1, lon2 = -45, -10, -70, -10
        area = area_definitions.rectlinear(
            shape=(100, 200), lat1=lat1, lat2=lat2, lon1=lon1, lon2=lon2
        )
        extent = area.area_extent
        assert extent[0] == lon1
        assert extent[1] == lat1
        assert extent[2] == lon2
        assert extent[3] == lat2


class TestSlippyTileGenerator:
    """Tests for tilers/rectlinear.py SlippyTileGenerator."""

    def test_init_stores_bounds(self):
        """Constructor should store geographic bounds."""
        gen = SlippyTileGenerator(min_lat=-10, max_lat=10, min_lon=-20, max_lon=20)
        assert gen.min_lat == -10
        assert gen.max_lat == 10
        assert gen.min_lon == -20
        assert gen.max_lon == 20

    def test_get_tiles_for_bounds_returns_tiles(self):
        """get_tiles_for_bounds() should return list of tiles."""
        gen = SlippyTileGenerator(min_lat=-10, max_lat=10, min_lon=-20, max_lon=20)
        tiles = gen.get_tiles_for_bounds(zoom=3)
        assert len(tiles) > 0
        # Each tile should have x, y, z attributes
        for tile in tiles:
            assert hasattr(tile, "x")
            assert hasattr(tile, "y")
            assert hasattr(tile, "z")
            assert tile.z == 3

    def test_get_tiles_higher_zoom_more_tiles(self):
        """Higher zoom levels should produce more tiles."""
        gen = SlippyTileGenerator(min_lat=-10, max_lat=10, min_lon=-20, max_lon=20)
        tiles_low = gen.get_tiles_for_bounds(zoom=2)
        tiles_high = gen.get_tiles_for_bounds(zoom=5)
        assert len(tiles_high) > len(tiles_low)

    def test_get_tiles_larger_area_more_tiles(self):
        """Larger geographic areas should produce more tiles at same zoom."""
        gen_small = SlippyTileGenerator(min_lat=-5, max_lat=5, min_lon=-5, max_lon=5)
        gen_large = SlippyTileGenerator(min_lat=-20, max_lat=20, min_lon=-40, max_lon=40)
        tiles_small = gen_small.get_tiles_for_bounds(zoom=4)
        tiles_large = gen_large.get_tiles_for_bounds(zoom=4)
        assert len(tiles_large) > len(tiles_small)

    def test_generate_tiles_creates_files(self):
        """generate_tiles() should create PNG files in the output directory."""
        gen = SlippyTileGenerator(min_lat=-5, max_lat=5, min_lon=-5, max_lon=5)

        # Create simple test data
        lats = np.linspace(-5, 5, 50)
        lons = np.linspace(-5, 5, 50)
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        data = np.sin(lat_grid * 0.1) * np.cos(lon_grid * 0.1)

        with tempfile.TemporaryDirectory() as tmpdir:
            gen.generate_tiles(
                scene_data=data,
                scene_lats=lats,
                scene_lons=lons,
                output_dir=tmpdir,
                zoom_levels=[0, 1],
                num_workers=1,
            )

            # Check that zoom directories were created
            assert (Path(tmpdir) / "0").exists()
            assert (Path(tmpdir) / "1").exists()

            # Check that some PNG files were created
            png_files = list(Path(tmpdir).rglob("*.png"))
            assert len(png_files) > 0

    def test_generate_tiles_handles_descending_coordinates(self):
        """generate_tiles() should correctly handle descending lat/lon arrays."""
        gen = SlippyTileGenerator(min_lat=-5, max_lat=5, min_lon=-5, max_lon=5)

        # Create data with descending latitudes (common in satellite data)
        lats = np.linspace(5, -5, 50)  # Descending
        lons = np.linspace(-5, 5, 50)  # Ascending
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        data = np.sin(lat_grid * 0.1) * np.cos(lon_grid * 0.1)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Should not raise an error
            gen.generate_tiles(
                scene_data=data,
                scene_lats=lats,
                scene_lons=lons,
                output_dir=tmpdir,
                zoom_levels=[0],
                num_workers=1,
            )

            png_files = list(Path(tmpdir).rglob("*.png"))
            assert len(png_files) > 0

    def test_generate_tiles_handles_nan_values(self):
        """generate_tiles() should handle NaN values in data."""
        gen = SlippyTileGenerator(min_lat=-5, max_lat=5, min_lon=-5, max_lon=5)

        lats = np.linspace(-5, 5, 50)
        lons = np.linspace(-5, 5, 50)
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        data = np.sin(lat_grid * 0.1) * np.cos(lon_grid * 0.1)

        # Add NaN values
        data[10:20, 10:20] = np.nan

        with tempfile.TemporaryDirectory() as tmpdir:
            gen.generate_tiles(
                scene_data=data,
                scene_lats=lats,
                scene_lons=lons,
                output_dir=tmpdir,
                zoom_levels=[0],
                num_workers=1,
            )

            png_files = list(Path(tmpdir).rglob("*.png"))
            assert len(png_files) > 0

    def test_generate_tiles_respects_vmin_vmax(self):
        """generate_tiles() should accept vmin and vmax parameters."""
        gen = SlippyTileGenerator(min_lat=-5, max_lat=5, min_lon=-5, max_lon=5)

        lats = np.linspace(-5, 5, 50)
        lons = np.linspace(-5, 5, 50)
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        data = np.sin(lat_grid * 0.1) * np.cos(lon_grid * 0.1)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Should not raise an error with explicit vmin/vmax
            gen.generate_tiles(
                scene_data=data,
                scene_lats=lats,
                scene_lons=lons,
                output_dir=tmpdir,
                zoom_levels=[0],
                num_workers=1,
                vmin=-0.5,
                vmax=0.5,
            )

            png_files = list(Path(tmpdir).rglob("*.png"))
            assert len(png_files) > 0

    def test_generate_tiles_accepts_2d_coordinates(self):
        """generate_tiles() should accept 2D coordinate arrays."""
        gen = SlippyTileGenerator(min_lat=-5, max_lat=5, min_lon=-5, max_lon=5)

        lats_1d = np.linspace(-5, 5, 50)
        lons_1d = np.linspace(-5, 5, 50)
        lon_grid, lat_grid = np.meshgrid(lons_1d, lats_1d)
        data = np.sin(lat_grid * 0.1) * np.cos(lon_grid * 0.1)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Pass 2D coordinate arrays directly
            gen.generate_tiles(
                scene_data=data,
                scene_lats=lat_grid,
                scene_lons=lon_grid,
                output_dir=tmpdir,
                zoom_levels=[0],
                num_workers=1,
            )

            png_files = list(Path(tmpdir).rglob("*.png"))
            assert len(png_files) > 0

    def test_tile_size_constant(self):
        """TILE_SIZE should be 256 (standard slippy map tile size)."""
        assert SlippyTileGenerator.TILE_SIZE == 256


class TestGenerateSingleTile:
    """Tests for the module-level _generate_single_tile function."""

    @staticmethod
    def _render(tmpdir, zoom, tile_x, tile_y, lons, lats, data, **kwargs):
        """Render one tile from lon/lat points and return its RGBA pixels."""
        x_coords, y_coords = lonlat_to_webmercator(lons, lats)
        tile_dir = Path(tmpdir) / str(zoom) / str(tile_x)
        tile_dir.mkdir(parents=True)
        _generate_single_tile(
            zoom, tile_x, tile_y, x_coords, y_coords, data, tmpdir,
            "viridis", 10, -1, 1, False, 5, **kwargs
        )
        return np.array(Image.open(tile_dir / f"{tile_y}.png").convert("RGBA"))

    def test_generates_png_file(self):
        """_generate_single_tile() should create a PNG file."""
        lon_grid, lat_grid = np.meshgrid(np.linspace(-170, 170, 100),
                                         np.linspace(-80, 80, 100))
        with tempfile.TemporaryDirectory() as tmpdir:
            pixels = self._render(tmpdir, 0, 0, 0, lon_grid.ravel(),
                                  lat_grid.ravel(), np.zeros(10000))
            assert (pixels[..., 3] > 0).any()
            assert not list(Path(tmpdir).rglob("*.tmp"))

    def test_empty_tile_for_no_data(self):
        """_generate_single_tile() should create transparent tile when no data in bounds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Tile 5/0/0 is in the northwest corner, far from this data
            pixels = self._render(tmpdir, 5, 0, 0,
                                  np.array([170.0, 171.0, 172.0]),
                                  np.array([80.0, 81.0, 82.0]),
                                  np.array([1.0, 2.0, 3.0]))
            assert (pixels[..., 3] == 0).all()

    def test_coarse_grid_fills_high_zoom_tile(self):
        """A grid coarser than the tile should still reach every tile edge."""
        lon_grid, lat_grid = np.meshgrid(np.arange(-5, 5, 0.125),
                                         np.arange(-5, 5, 0.125))
        lons, lats = lon_grid.ravel(), lat_grid.ravel()
        data = np.zeros(lons.size)
        x_coords, y_coords = lonlat_to_webmercator(lons, lats)
        spacing = float(np.abs(np.diff(np.unique(y_coords))).max())
        tile = mercantile.tile(0.3, 0.3, 11)
        with tempfile.TemporaryDirectory() as tmpdir:
            pixels = self._render(tmpdir, 11, tile.x, tile.y, lons, lats, data,
                                  grid_spacing=spacing)
            assert (pixels[..., 3] > 0).all()

    def test_single_grid_column_gives_blank_tile(self, capsys):
        """Collinear points should give a blank tile, not a qhull error."""
        tile = mercantile.tile(0.3, 0.3, 9)
        lats = np.linspace(0.2, 0.4, 5, dtype=np.float32)
        lons = np.full(5, 0.3, dtype=np.float32)
        with tempfile.TemporaryDirectory() as tmpdir:
            pixels = self._render(tmpdir, 9, tile.x, tile.y, lons, lats,
                                  np.zeros(5, dtype=np.float32))
        assert (pixels[..., 3] == 0).all()
        assert "Error" not in capsys.readouterr().out

    def test_failed_write_leaves_no_tile(self, tmp_path):
        """An interrupted save should not leave a partial tile behind."""
        class FailingImage:
            def save(self, path, format=None):
                Path(path).write_bytes(b"")
                raise OSError("disk full")

        tile_path = tmp_path / "0.png"
        with pytest.raises(OSError):
            _save_tile(FailingImage(), tile_path)
        assert not tile_path.exists()
