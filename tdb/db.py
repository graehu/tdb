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
_db_inserts = []

def _init():
    global _db_text
    global _skip_shutdown
    if not _db_text:
        _db_text = open(_db_file).read()
        _skip_shutdown = False


def get_filename(): return _db_file
def get_text():
    _init()
    return _db_text


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


def insert(text, start, end):
    global _db_inserts
    _init()
    _db_inserts.append([text, (start, end)])


def serialise():
    global _db_text
    global _db_inserts

    db_edits = _db_text if _db_inserts else ""
    while _db_inserts:
        insert, span =_db_inserts.pop(0)
        delta = len(insert)-(span[1]-span[0])
        # print(len(insert))
        # print(db_edits[:span[0]])
        # print("-")
        # print(insert)
        # print("-")
        # print(db_edits[span[1]:])
        db_edits = db_edits[:span[0]] + insert + db_edits[span[1]:]
        _db_inserts = [[i[0], (i[1][0]+delta, i[1][1]+delta)] if i[1][0] > span[0] else i for i in _db_inserts]
        # print(_db_inserts)

    # TODO three way merge will be needed
    if _db_inserts and _db_mtime != os.path.getmtime(_db_file):
        import difflib
        print("edits detected trying to merge")
        # a_lines = _db_text.splitlines()
        b_lines = [l[:-1] for l in open(get_filename()).readlines()]
        c_lines = db_edits.splitlines()
        
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
    elif db_edits:
        open(get_filename(), "w").write(db_edits)


@atexit.register
def _shutdown():
    if _skip_shutdown: return
    serialise()