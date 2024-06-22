import re
from datetime import datetime
import time
import json
import tdb.db
import tdb.tags
import tdb.rake
import tdb.html
import tdb.cli
# This is the format: "2023-04-05 09:59:33"
re_iso_record = re.compile(r'^\[tdb:(\d{4}\-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\.\d{6})?)\] ?', re.MULTILINE | re.IGNORECASE)
re_hex_record = re.compile(r'^\[tdb:(0x[\da-f]+)\] ?', re.MULTILINE | re.IGNORECASE)
_record_cache = []
_record_cmds = []
_needs_sort = False
_force_hex = False
_record_mtime = 0

def convert_db_nano_to_micro():
    return # don't call this code atm.
    file_name = tdb.db.get_filename()
    text = open(file_name, "r").read()
    for match in re_hex_record.finditer(text):
        nano = int(match.group(1), 16)
        if int(nano/1E9) > 1E9:
            before = f"[tdb:{(hex(nano))}]"
            nano = int(nano/1E3)
            after = f"[tdb:{(hex(nano))}]"
            print(f"before: {before}\nafter: {after}")
            text = text.replace(before, after, 1)
    open(file_name, "w").write(text)
    

def convert_headers(text):
    out = text
    while m := re_iso_record.search(out):
        d = datetime.fromisoformat(m.group(1))
        d = hex(int(d.timestamp()*1E6))
        out = out[:m.span(1)[0]]+d+out[m.span(1)[1]:]
    return out


class Record(object):
    text = ""
    ending = "\n"
    text_hash = 0
    time = 0
    date = None
    tags = []
    span = (0,0)
    md_text = ""
    def __init__(self, text, time, ending, date, tags, span):
        self.text = text
        if isinstance(date, str):
            self.date = datetime.fromisoformat(date)
        else:
            self.date = date
        self.tags = tags
        self.span = span
        self.time = time
        self.text_hash = hash(text)
        self.ending = ending
        self.md_text = text

    def __str__(self):
        if _force_hex:
            return self.entry()
        else:
            return f"[tdb:{self.iso_str()}] {self.text}"+self.ending

    def iso_str(self): return self.date.isoformat(' ')

    def entry(self):
        return f"[tdb:{hex(self.time)}] {self.text}"+self.ending

    def md(self):
        return f"[tdb:{self.iso_str()}] {self.md_text}"+self.ending

    
    def asdict(self):
        return {'text': self.text, 'time': self.time,
                'date': self.date.isoformat(" "), 'tags': self.tags,
                'span':self.span, "ending":self.ending }


def register_cmd(func):
    global _record_cmds
    _record_cmds.append(func)


def make_record(date, text):
    return f"[tdb:{date}] {text}"


def add_record(text, start_time = None):
    dt = tdb.db.get_mtime()
    ns = start_time if start_time else time.time_ns()
    # convert to microseconds for datetime compliance
    ns = int(ns/1E3)

    if (ns/1E6) - dt > 1.0: ns = int(int(ns/1E6)*1E6)
    # if (ns/1E9) - dt > 1.0: ns = int(int(ns/1E9)*1E9)
    record = make_record(hex(ns), text)
    tdb.db.append_immediate(record)
    tdb.db.archive(record, False)

    return True


def deduplicate_records(in_records):
    dedupe = []
    for r1 in in_records:
        new = True
        for r2 in dedupe:
            if r1.date == r2.date: new = False; break
        if new: dedupe.append(r1)
    return dedupe


def modify_db_records(old_records:list, new_records:list):
    dedupe = deduplicate_records(new_records)
    if len(new_records) != len(dedupe): print("Warning: duplicate dates found. Ignoring those entries.")
    new_records = dedupe
    mods = adds = dels = 0
    def is_datesame(r1, r2): return r1.date == r2.date
    def is_equal(r1, r2): return r1.text_hash == r2.text_hash and is_datesame(r1, r2)
    def is_mod(r1, r2): return not is_equal(r1, r2) and is_datesame(r1, r2)
    def filter_newmods(new_rec):
        for old_rec in old_records:
            if is_mod(new_rec, old_rec): return True
        return False
    
    def filter_oldmods(old_rec):
        for new_rec in new_records:
            if is_mod(new_rec, old_rec): return True
        return False
    
    def filter_adds(new_rec):
        for old_rec in old_records:
            if is_datesame(new_rec, old_rec): return False
        return True
    
    def filter_dels(old_rec):
        for new_rec in new_records:
            if is_datesame(new_rec, old_rec): return False
        return True
    
    
    newmod_list = filter(filter_newmods, new_records)
    oldmod_list = filter(filter_oldmods, old_records)
    add_list = filter(filter_adds, new_records)
    del_list = filter(filter_dels, old_records)

    mod_list = zip(newmod_list, oldmod_list)
    for r1, r2 in mod_list:
        assert(is_datesame(r1, r2))
        for r in _record_cmds: r1 = r("mod", r1)
        tdb.db.replace(r2.entry(), r1.entry()); mods += 1

    for r1 in add_list:
        for r in _record_cmds: r1 = r("add", r1)
        tdb.db.append(r1.entry()); adds+=1
    
    for r1 in del_list:
        tdb.db.archive(r1.entry()); dels+=1
        for r in _record_cmds: r1 = r("del", r1)
    return adds, mods, dels

def archive_records(records: list):
    if records:
        for r1 in records: tdb.db.archive(r1.entry())
        return True
    return False


def merge_records(text_head, text_a, text_b):
    head = split_records(text_head)
    a_db = split_records(text_a)
    b_db = split_records(text_b)
    def handle_conflict(in_record):
        if not tdb.db._db_has_conflicts:
            print("Warning: conflict in ")
            tdb.db._db_has_conflicts = True
        print("\t"+str(in_record).splitlines()[0])
        if "@tdb_conflict" not in in_record.text:
            in_record.text += "\n@tdb_conflict\n\n"
        
    out = []
    while head or a_db or b_db:
        h = head.pop(0) if head else None
        a = a_db.pop(0) if a_db else None
        b = b_db.pop(0) if b_db else None
        # if h: print("h:"+h.entry().splitlines()[0])
        # if a: print("a:"+a.entry().splitlines()[0])
        # if b: print("b:"+b.entry().splitlines()[0])
        # do something so these eventually all reference the same thing?
        if h and a and b and (h.date < a.date or h.date < b.date): 
            while head and h.date < a.date or h.date < b.date:
                if h.date == a.date and h.text != a.text: # change
                    handle_conflict(a)
                    out.append(a)
                elif h.date == b.date and h.text != b.text: # change
                    handle_conflict(b)
                    out.append(b)

                h = head.pop(0)

            if a.date < b.date:
                while a_db and a.date != b.date: a = a_db.pop(0)
            else:
                while b_db and a.date != b.date: b = b_db.pop(0)

        if h and a and b and (h.date == a.date and h.date == b.date):
            if h.text != a.text and h.text == b.text: h.text = a.text
            elif h.text == a.text and h.text != b.text: h.text = b.text
            elif h.text != a.text and h.text != b.text:
                import difflib
                diff = difflib.Differ().compare(a.text.splitlines(keepends=True), b.text.splitlines(keepends=True))
                h.text = "".join([l[2:] if l[0] == " " else l for l in list(diff)])
                handle_conflict(h)
            out.append(h)
            continue
        # don't lose this record
        if a: a_db.append(a)
        if b: b_db.append(b)
        if h: head.append(h)
        break
    
    out = out + head + a_db + b_db
    out = deduplicate_records(out)
    sorted(out, key=lambda x: x.date)
    out = "".join([r.entry() for r in out])
    # print(len(out.splitlines()))
    return out


tdb.db._db_merge_func = merge_records


def stringify_db_records(options:dict=None, ansi_colours=False):
    records = split_db_records(options)
    return stringify_records(records, options, ansi_colours)


def stringify_records(records:list, options:dict=None, ansi_colours=False):
    out = ""
    if options and options["as"] == "json":
        res = [r.asdict() for r in records]
        out = json.dumps(res, indent=2)
    elif options and options["as"] == "raw":
        out = "".join([r.entry() for r in records]).strip()
    elif options and options["as"] == "html":
        out = tdb.html.build_html(list(reversed(records)))
    elif options and options["as"] == "html_entries":
        out = tdb.html.build_html_entries(list(reversed(records)))
    elif options and options["as"] == "list":
        def list_line(record):
            line = str(record).splitlines()[0]
            for t, _ in record.tags:
                if not "@"+t in line: line += " @"+t 
            return line+"\n"
        out = "".join([list_line(r) for r in records])
        out = out.strip()
    elif options and options["as"] == "tags":
        tags = {}
        for r in records:
            for t in r.tags:
                if t[0] in tags: tags[t[0]] += 1
                else: tags[t[0]] = 1
        out = json.dumps(tags, indent=2)
    elif options and options["md"]:
        out = "".join([r.md() for r in records])
        out = out.strip()
    else:
        out = "".join([str(r) for r in records])
        out = out.strip()

    if ansi_colours:
        for tag in tdb.tags.get_coloured():
            if tdb.tags.contains_tag(out, tag):
                col = tdb.cli.ANSICodes[tdb.tags.get_colour(tag)][0]
                end = tdb.cli.ANSICodes["end"][0]
                out = re.sub(f"(?!{re.escape(col)})@"+tag+f"(?!{re.escape(end)})", col+"@"+tag+end, out)
        # TODO: the [tdb:\1] here feels like it could be done better. Also, config colour for tdb header?
        out = re_iso_record.sub(tdb.cli.ANSICodes["light_white"][0]+r"[tdb:\1] "+tdb.cli.ANSICodes["end"][0], out)
        out = re_hex_record.sub(tdb.cli.ANSICodes["light_white"][0]+r"[tdb:\1] "+tdb.cli.ANSICodes["end"][0], out)        

    return out


def print_records(records, options=None):
    print(stringify_records(records, options, tdb.cli.isatty()))

def print_db_records(options=None):
    if records := split_db_records(options):
        print_records(records, options)


def filter_records(records : list, options : list):
    max_id = len(records)
    filtered = records.copy()

    if ctags := tdb.config.get("tags"):
        for tag in ctags:
            tops = [*options["otags"], *options["atags"], *options["ntags"]]
            if "exclude" in ctags[tag] and ctags[tag]["exclude"] and not tag in tops:
                options["ntags"].append(tag)

    dates = options["dates"] if options else []
    span = options["span"].copy() if options else []
    otags = options["otags"] if options else []
    ntags = options["ntags"] if options else []
    atags = options["atags"] if options else []
    acontains = options["acontains"] if options else []
    ocontains = options["ocontains"] if options else []
    ncontains = options["ncontains"] if options else []
    md = options["md"].lower() if options else ""
    re_md = re.compile("(#{1,6}\s+.+)")

    if span:
        if all(map(lambda x: isinstance(x, int), span)):
            span = sorted([span[0], span[0]+span[1]])
            span[0] = min(max(0, span[0]+max_id), max_id)
            span[1] = min(max(0, span[1]+max_id), max_id)
            filtered = filtered[span[0]:span[1]]

        elif isinstance(span[0], int):
            span[0] = min(max(0, span[0]+max_id), max_id)
            filtered = filtered[span[0]:]
            span[1] = next((i for i,v in enumerate(filtered) if v.date >= span[1]), max_id)
            filtered = filtered[:span[1]+span[0]]

        elif isinstance(span[1], int):
            span[0] = next((i for i,v in enumerate(filtered) if v.date >= span[0]), max_id)
            span[1] = min(max(0, span[0]+span[1]), span[1])
            span = sorted([span[0],span[0]+span[1]])
            filtered = filtered[span[0]:span[1]]
        else:
            filtered = [r for r in filtered if span[0] <= r.date <= span[1]]
    
    if dates:
        def date_compare(a:datetime, b:datetime):
            return (
             (a.year == b.year or a.year == 0 or b.year == 0) and
             (a.month == b.month or a.month == 0 or b.month == 0) and
             (a.day == b.day or a.day == 0 or b.day == 0) and
             (a.hour == b.hour or a.hour == 0 or b.hour == 0) and
             (a.minute == b.minute or a.minute == 0 or b.minute == 0) and
             (a.second == b.second or a.second == 0 or b.second == 0) and
             (a.microsecond == b.microsecond or a.microsecond == 0 or b.microsecond == 0)
             )
        
        filtered = [r for r in filtered if any([date_compare(r.date, d) for d in dates])]
    
    out = []
    for record in filtered:
        low_text = record.text.lower()
        flat_tags = [x[0] for x in record.tags]
        skip = False
        if not skip and ocontains: skip = not any([c in low_text for c in ocontains])
        if not skip and acontains: skip = not all([c in low_text for c in acontains])
        if not skip and ncontains: skip = any([c in low_text for c in ncontains])
        if not skip and otags: skip = not any([t in flat_tags for t in otags])
        if not skip and atags: skip = not all([t in flat_tags for t in atags])
        if not skip and ntags: skip = any([t in flat_tags for t in ntags])
        if md:
            md_text = re_md.split(record.text)
            if not md_text[0].startswith("#"): md_text = md_text[1:]
            md_text = zip(md_text[::2], md_text[1::2])
            md_text = [f"{t[0]}\n{t[1]}" for t in md_text if md in t[0].lower()]
            record.md_text = "".join(md_text)
            if not record.md_text: skip = True
        if not skip: out.append(record)

    return out


def sort_db_records():
    global _record_cache
    global _needs_sort
    print("warning: db unordered, attempting sort.")
    tdb.db.set_text("".join([r.entry() for r in _record_cache]))
    _needs_sort = False
    _record_cache = split_records(tdb.db.get_text())
    assert(_needs_sort == False)


def split_db_records(options=None):
    global _record_cache
    global _needs_sort
    global _record_mtime
    if tdb.db._db_mtime != _record_mtime:
        _record_cache = split_records(tdb.db.get_text())
        _record_mtime = tdb.db._db_mtime
    if _needs_sort: sort_db_records()
    if options: return filter_records(_record_cache, options)
    else: return _record_cache


def split_records(text: str):
    global _needs_sort
    text = convert_headers(text)
    last = None
    current = None
    records = []

    def append_record():
        nonlocal records
        nonlocal last
        nonlocal current

        if last:
            x,y = last["span"][1], current["span"][0]
            section = text[x:y]
            tags = tdb.tags.find_tags(section.lower())
            tdb.tags.register(tags)
            last["text"] = section.rstrip()
            last["ending"] = "\n\n" if last["text"].count("\n") > 1 else "\n"
            last["tags"] = tags
            last["span"] = (x ,y)
            records.append(last)

    for match in re_hex_record.finditer(text):
        nano = int(match.group(1), 16)
        
        if int(nano/1E9) > 1E9:
            nano = int(nano/1E3)
        current = {
            "date": datetime.fromtimestamp(nano/1E6),
            "time": nano,
            "text": "",
            "tags": [],
            "span": match.span()
        }
        if last and last["time"] > current["time"]: _needs_sort = True

        append_record()
        last = current
    # hack to fix last record text
    current = {"span": [len(text)]}
    append_record()

    if _needs_sort: records = sorted(records, key=lambda x: x["time"])
    records = [Record(**r) for r in records]
    return records


def find_similar(text):
    kw_ext = tdb.rake.Rake()
    text_kw = kw_ext.run(text)

    records = split_db_records()
    results = []
    for record in records:
        record_kw = kw_ext.run(record["text"])
        for k1, v1 in record_kw:
            for k2, v2 in text_kw:
                if tdb.rake.similarity_score(k1, k2) > 0.8:
                    record["score"] += (v1+v2)*0.5

        if record["score"] > 0:
            results.append(record)

    print(json.dumps(results, indent=2))