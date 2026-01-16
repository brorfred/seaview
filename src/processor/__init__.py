
import pandas as pd

from . import process_day

#def day(dtm):
#    processor_day.day(dtm)



class DateInFutureError(Exception):
    pass

def day(dtm):
    pass

def today():
    dtm = pd.Timestamp.now().normalize()
    process_day.all(dtm)

def yesterday():
    dtm = pd.Timestamp.now().normalize()-pd.Timedelta(1,"D")
    process_day.all(dtm)
