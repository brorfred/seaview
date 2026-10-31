"""Tests for the seaview.tilers.archive module."""

import pytest
from pmtiles.reader import MmapSource, Reader
from pmtiles.tile import Compression, TileType

from seaview.tilers.archive import pack_tiles


BOUNDS = (-75.0, -55.0, -5.0, -10.0)


def write_tile(root, z, x, y, data):
    """Write one tile to a z/x/y.png tree."""
    path = root / str(z) / str(x) / f"{y}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


class TestPackTiles:
    """Tests for the pack_tiles function."""

    def test_round_trip(self, tmp_path):
        """Packed tiles should be readable at the same z/x/y."""
        write_tile(tmp_path / "t", 0, 0, 0, b"zero")
        write_tile(tmp_path / "t", 2, 1, 3, b"two")
        archive = tmp_path / "out" / "2025-01-15.pmtiles"

        assert pack_tiles(tmp_path / "t", archive, BOUNDS) == archive

        with open(archive, "rb") as f:
            reader = Reader(MmapSource(f))
            assert reader.get(0, 0, 0) == b"zero"
            assert reader.get(2, 1, 3) == b"two"
            assert reader.get(2, 0, 0) is None
            header = reader.header()
        assert header["tile_type"] == TileType.PNG
        assert header["tile_compression"] == Compression.NONE
        assert (header["min_zoom"], header["max_zoom"]) == (0, 2)
        assert header["min_lon_e7"] == -750000000

    def test_duplicate_tiles_are_stored_once(self, tmp_path):
        """Identical tiles should share one stored copy."""
        for x in range(4):
            write_tile(tmp_path / "t", 2, x, 0, b"same" * 100)
        archive = tmp_path / "a.pmtiles"
        pack_tiles(tmp_path / "t", archive, BOUNDS)

        with open(archive, "rb") as f:
            header = Reader(MmapSource(f)).header()
        assert header["tile_data_length"] == 400

    def test_empty_tree_keeps_existing_archive(self, tmp_path):
        """A tree without tiles should raise and leave the archive alone."""
        (tmp_path / "t").mkdir()
        archive = tmp_path / "a.pmtiles"
        archive.write_bytes(b"old")

        with pytest.raises(ValueError):
            pack_tiles(tmp_path / "t", archive, BOUNDS)
        assert archive.read_bytes() == b"old"

    def test_failed_write_leaves_no_temp_file(self, tmp_path):
        """A failure while packing should leave nothing behind."""
        write_tile(tmp_path / "t", 0, 0, 0, b"zero")
        (tmp_path / "t" / "0" / "0" / "0.png").chmod(0o000)
        archive = tmp_path / "a.pmtiles"

        with pytest.raises(OSError):
            pack_tiles(tmp_path / "t", archive, BOUNDS)
        assert list(tmp_path.glob("a.pmtiles*")) == []
