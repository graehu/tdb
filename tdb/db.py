import os
import atexit
import tdb.config

_skip_shutdown = True
_db_file = tdb.config.get("db_file")
_db_archive = tdb.config.get("db_archive")
_db_merge_func = None
_db_has_conflicts = False

if not _db_file:
    _db_file = tdb.config.get_tdb_dir()
    _db_file = os.path.join(_db_file, "db.txt")


if not os.path.exists(_db_file):
    from urllib.request import Request, urlopen
    import json
    first_line = "oh hai\n"
    try:
        # At some point in the future people will want this removed. :)
        request = Request('https://icanhazdadjoke.com/', headers={'Accept': 'application/json', 'User-Agent': "tdb"})
        response = urlopen(request).read().decode()
        response = json.loads(response)
        if "joke" in response: first_line = response["joke"]+"\n"
    except Exception as e: pass
    open(_db_file, "w").write(first_line)


if not _db_archive:
    _db_archive = tdb.config.get_tdb_dir()
    _db_archive = os.path.join(_db_archive, "db_archive.txt")


if not os.path.exists(_db_archive):
    open(_db_archive, "w").write("archived entries go here.")


_db_mtime = os.path.getmtime(_db_file)
_db_text = ""
_db_inserts = []

def get_mtime(): return _db_mtime

def _init():
    global _db_text
    global _skip_shutdown
    if not _db_text:
        _db_text = open(_db_file).read()
        _skip_shutdown = False


def get_filename(): return _db_file
def get_archive(): return _db_archive
def get_text():
    _init()
    return _db_text


def set_text(text):
    global _db_text
    _init()
    _db_text = text


def append(text):
    global _db_inserts
    global _db_text
    _init()
    if _db_text and _db_text[-1] != '\n':
        text = '\n'+text
    insert(text, len(_db_text), len(_db_text))

def append_immediate(text): open(get_filename(), "a").write(text)

def replace(old, new):
    global _db_inserts
    _init()
    # print("old:"+str([old]))
    id = _db_text.index(old)
    if id != -1:
        insert(new, id, id+len(old))

def archive(text):
    open(get_archive(), "a").write(text)
    replace(text, "")


def insert(text, start, end):
    global _db_inserts
    _init()
    _db_inserts.append([text, (start, end)])


def perform_inserts():
    global _db_text
    global _db_inserts
    # print(_db_inserts)
    while _db_inserts:
        insert, span =_db_inserts.pop(0)
        delta = len(insert)-(span[1]-span[0])
        # print(delta)
        # print(len(insert))
        # print(_db_text[:span[0]])
        # print("-")
        # print(insert)
        # print("-")
        # print(_db_text[span[1]:])
        _db_text = _db_text[:span[0]] + insert + _db_text[span[1]:]
        _db_inserts = [[i[0], (i[1][0]+delta, i[1][1]+delta)] if i[1][0] >= span[0] else i for i in _db_inserts]
        # print(_db_inserts)
        # print("----------------------------------")

    pass


def serialise():
    global _db_text
    global _db_inserts
    global _db_mtime

    db_head = _db_text if _db_inserts else ""
    perform_inserts()
    db_edits = _db_text if db_head else ""

    # TODO three way merge will be needed
    if _db_mtime != os.path.getmtime(_db_file):
        output = _db_merge_func(db_head, _db_text, open(get_filename()).read())
        open(get_filename(), "w").write(output)
        if _db_has_conflicts:
            print("@tdb_conflict has been added to affected records.")
    elif db_edits:
        open(get_filename(), "w").write(db_edits)

    _db_mtime = os.path.getmtime(_db_file)


@atexit.register
def _shutdown():
    if _skip_shutdown: return
    serialise()