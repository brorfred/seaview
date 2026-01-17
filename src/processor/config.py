import os
import pathlib

from dynaconf import Dynaconf

USER_DIR = pathlib.Path("~/.config/seastate").expanduser()
USER_DIR.mkdir(parents=True, exist_ok=True)
GLOB_DIR = pathlib.Path("/etc/seastate/")
CURR_DIR = pathlib.Path("./").absolute()

settings_files = [
    GLOB_DIR / "settings.toml",
    GLOB_DIR / ".secrets.toml",
    USER_DIR / "settings.toml",
    USER_DIR / ".secrets.toml",
    CURR_DIR / "settings.toml",
    CURR_DIR / ".secrets.toml"
    ]

extra_file = os.getenv("SEASTATE_SETTINGS_FILE_FOR_DYNACONF")
if extra_file:
    settings_files.append(pathlib.Path(extra_file).absolute())

settings = Dynaconf(
    merge_enabled = True,
    envvar_prefix="SEASTATE",
    DEBUG_LEVEL_FOR_DYNACONF='DEBUG',
    settings_files=settings_files,
    #secrets=[
    #    "/etc/seastate/.secrets.toml",
    #    "~/.config/seastate/.secrets.toml",
    #    "./.seastate.toml",
    #],
    environments=True,
    load_dotenv=True,
)

#print("Loaded files:", settings.loaded_files)
#print("\nSettings:", dict(settings))
