import os
import atexit
import tdb.config

_skip_shutdown = True
_db_file = tdb.config.get("db_file")


if not _db_file:
    _db_file = "db.txt"
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


_db_mtime = os.path.getmtime(_db_file)
_db_text = ""
_db_edits = ""

def _init():
    global _db_text
    global _db_edits
    global _skip_shutdown
    if not _db_text:
        _db_text = open(_db_file).read()
        _db_edits = _db_text
        _skip_shutdown = False


def get_filename(): return _db_file
def get_text():
    _init()
    return _db_edits


def append(text):
    global _db_edits
    _init()
    if _db_edits and _db_edits[-1] != "\n":
        _db_edits += "\n"+text
    else:
        _db_edits += text


def insert(text, pos):
    global _db_edits
    _init()
    _db_edits = _db_edits[:pos]+text+_db_edits[pos:]


def serialise():
    global _db_text
    global _db_edits

    # TODO three way merge will be needed
    if _db_edits and _db_mtime != os.path.getmtime(_db_file):
        import difflib
        print("edits detected trying to merge")
        # a_lines = _db_text.splitlines()
        b_lines = [l[:-1] for l in open(get_filename()).readlines()]
        c_lines = _db_edits.splitlines()
        
        # ac_match = difflib.SequenceMatcher(a=a_lines, b=c_lines)
        # ac_opcodes = ac_match.get_opcodes()
        bc_match = difflib.SequenceMatcher(a=b_lines, b=c_lines)
        bc_opcodes = bc_match.get_opcodes()

        output = []
        for tag, i1, i2, j1, j2 in bc_opcodes:
            if tag == "equal": output.extend(b_lines[i1:i2])
            elif tag == "insert": output.extend(c_lines[j1:j2])
            elif tag == "replace":
                # todo: this needs to check if these are within the same entry.
                output.extend(b_lines[i1:i2])
                output.extend(c_lines[j1:j2])

            elif tag == "delete":
                # todo: here we need to see if they were inserted by a_lines
                output.extend(b_lines[i1:i2])
                pass
            print('{:7}   a[{}:{}] --> b[{}:{}]'.format(tag, i1, i2, j1, j2))
        
        open(get_filename(), "w").write("\n".join(output)+"\n")
    else:
        open(get_filename(), "w").write(_db_edits)


@atexit.register
def _shutdown():
    if _skip_shutdown: return
    serialise()