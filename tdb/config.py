import tomllib
import os

_editor = "notepad"
if os.name == "nt": _editor = "notepad"
else: editor = os.environ.get("EDITOR", "nano")

_default = f"""\
editor = "{_editor}" # command for editor\
"""
_filename = os.path.expanduser("~/.tdb/config.toml")

os.makedirs(os.path.dirname(_filename), exist_ok=True)

if not os.path.exists(_filename):
    with open(_filename, "w") as fd: fd.write(_default)

_config = None
_config = tomllib.load(open(_filename, "rb"))

def get(key): return _config.get(key)