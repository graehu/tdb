import shutil
import os

_editors = ["notepad", "gedit -w", "code -w", "emacs -a \"\" -c", "subl -w"]
for editor in _editors:
    editor = editor.split()[0]
    if shutil.which(editor):
        _editor = editor
        break

_tdb_dir = os.path.expanduser("~/.tdb")
_tdb_dir = _tdb_dir.replace("\\", "/")
_db_file = "/".join((_tdb_dir, "db.txt"))
_conf_file = "/".join((_tdb_dir, "config.toml"))
_config = None


_conf_text = f"""\
# path to database
db_file = "{_db_file}"
# options: {_editors}
editor = "{_editor}" # command for editor
"""

os.makedirs(_tdb_dir, exist_ok=True)

if not os.path.exists(_conf_file): open(_conf_file, "w").write(_conf_text)


def get_tdb_dir(): return _tdb_dir
def get_filename(): return _conf_file
def get(key):
    global _config
    if not _config:
        import tomllib
        _config = tomllib.load(open(_conf_file, "rb"))
    return _config.get(key)