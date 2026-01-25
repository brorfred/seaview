

from . import config
settings = config.settings

def vprint(string):
    if settings.get("verbose"):
        print(string)
