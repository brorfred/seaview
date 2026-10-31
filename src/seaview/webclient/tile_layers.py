
import pandas as pd

import folium
from folium.plugins import GroupedLayerControl

BASE_URL = "https://monhegan.unh.edu/cruise/tiles"


def sst_field(dtm="2026-01-10"):
    dtm = pd.to_datetime(dtm)
    dtmstr= str(dtm.date())
    url = f"{BASE_URL}/bioreactors1/ostia/{dtmstr}/" + "{z}/{x}/{y}.png"
    return folium.TileLayer(url,
                            attr="OSTIA 2km SST 10–28°C",
                            name=f"SST {dtm.date()}",
                            control=True,
                            overlay=True)


def ssh_field(dtm="2026-01-10"):
    dtm = pd.to_datetime(dtm)
    dtmstr= str(dtm.date())
    url = f"{BASE_URL}/bioreactors1/ssh/{dtmstr}/" + "{z}/{x}/{y}.png"
    return folium.TileLayer(url,
                            attr="Copernicus 1/8° SSH -0.75–0.75 m",
                            name=f"SSH {dtm.date()}",
                            control=True,
                            overlay=True)

def globcolour_field(dtm="2026-01-10"):
    dtm = pd.to_datetime(dtm)
    dtmstr= str(dtm.date())
    url = f"{BASE_URL}/bioreactors1/globcolour/{dtmstr}/" + "{z}/{x}/{y}.png"
    return folium.TileLayer(url,
                            attr="Globcolour 4km Chl 0.01-100 mg/m3",
                            name=f"SSH {dtm.date()}",
                            control=True,
                            overlay=True)


def add_fields(m):

    def date_fields(field, dstr1, dstr2):
        fglist = []
        for dtm in pd.date_range(dstr1, dstr2):
            dtmstr= str(dtm.date())
            fg = folium.FeatureGroup(name=dtmstr, show=False).add_to(m)
            field(dtm=dtm).add_to(fg)
            fglist.append(fg)
        return fglist

    sshlist = date_fields(ssh_field, "2026-01-08","2026-01-12")
    sstlist = date_fields(sst_field, "2026-01-08","2026-01-12")
    glblist = date_fields(globcolour_field, "2026-01-08","2026-01-12")


    GroupedLayerControl(
        groups={'SSH CMEMS 0.125°  ': sshlist},
        exclusive_groups=False,
        collapsed=False,
    ).add_to(m)

    GroupedLayerControl(
        groups={'SST OSTIA 5km     ': sstlist},
        exclusive_groups=False,
        collapsed=False,
    ).add_to(m)

    GroupedLayerControl(
        groups={'Chl GlobColour 4km': glblist},
        exclusive_groups=False,
        collapsed=False,
    ).add_to(m)
