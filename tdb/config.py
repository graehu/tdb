import tomllib
import shutil
import os

_editors = ["notepad", "gedit -w", "code -w", "emacs -a \"\" -c", "subl -w"]
for editor in _editors:
    editor = editor.split()[0]
    if shutil.which(editor):
        _editor = editor
        break

_default = f"""\
# options: {_editors}
editor = "{_editor}" # command for editor
"""
_filename = os.path.expanduser("~/.tdb/config.toml")

os.makedirs(os.path.dirname(_filename), exist_ok=True)

if not os.path.exists(_filename):
    with open(_filename, "w") as fd: fd.write(_default)

_config = None
_config = tomllib.load(open(_filename, "rb"))

def get_filename(): return _filename
def get(key): return _config.get(key)