
import pandas as pd

from . import tile
from . import layer_config

#def day(dtm):
#    processor_day.day(dtm)



class DateInFutureError(Exception):
    pass

def day(dtm):
    pass

def today():
    dtm = pd.Timestamp.now().normalize()
    tile.all(dtm)
    tile.sync()

def yesterday():
    dtm = pd.Timestamp.now().normalize()-pd.Timedelta(1,"D")
    tile.all(dtm)
    tile.sync()
