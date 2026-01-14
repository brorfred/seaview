
import pathlib

BASE_TILE_DIR = "/data/slow/web_share/cruise/tiles"

def settings():
    return dict(
        cruise_name = "FALKOR_1",
        lat1 = -55,
        lat2 = -10,
        lon1 = -75,
        lon2 = -5,
        tile_dir = BASE_TILE_DIR + "/falkor1",
        data_dir = "/data/raid/cruise_support/FALKOR_1",
        zoom_levels = [0,1,2,3,4,5,6,7,8,9]
)
