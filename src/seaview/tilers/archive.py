"""Pack slippy map tile trees into PMTiles archives.

A PMTiles archive holds all tiles of a product and day in a single file that
a web map reads directly through HTTP range requests.
"""
from pathlib import Path
from typing import Tuple

from pmtiles.tile import Compression, TileType, zxy_to_tileid
from pmtiles.writer import write


def pack_tiles(tile_dir, archive_path,
               bounds: Tuple[float, float, float, float]) -> Path:
    """Write a z/x/y.png tile tree to a PMTiles archive.

    The archive is written next to its final path and moved into place when
    complete, so an interrupted run never leaves a partial archive.

    Parameters
    ----------
    tile_dir : str or pathlib.Path
        Directory holding the tiles as {z}/{x}/{y}.png.
    archive_path : str or pathlib.Path
        Path of the archive to write.
    bounds : tuple of float
        Geographic bounds as (min_lon, min_lat, max_lon, max_lat).

    Returns
    -------
    pathlib.Path
        The path of the written archive.
    """
    archive_path = Path(archive_path)
    tiles = sorted(
        (zxy_to_tileid(int(path.parts[-3]), int(path.parts[-2]), int(path.stem)), path)
        for path in Path(tile_dir).glob("*/*/*.png")
    )
    if not tiles:
        raise ValueError(f"No tiles found in {tile_dir}")

    min_lon, min_lat, max_lon, max_lat = bounds
    header = {
        "tile_type": TileType.PNG,
        "tile_compression": Compression.NONE,
        "min_lon_e7": int(min_lon * 1e7),
        "min_lat_e7": int(min_lat * 1e7),
        "max_lon_e7": int(max_lon * 1e7),
        "max_lat_e7": int(max_lat * 1e7),
        "center_zoom": 0,
        "center_lon_e7": int((min_lon + max_lon) / 2 * 1e7),
        "center_lat_e7": int((min_lat + max_lat) / 2 * 1e7),
    }

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = archive_path.with_suffix(".pmtiles.tmp")
    try:
        with write(str(tmp_path)) as writer:
            for tile_id, path in tiles:
                writer.write_tile(tile_id, path.read_bytes())
            writer.finalize(header, {})
        tmp_path.replace(archive_path)
    finally:
        tmp_path.unlink(missing_ok=True)
    return archive_path
