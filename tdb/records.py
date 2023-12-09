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
    time = 0
    date = None
    tags = []
    span = (0,0)
    def __init__(self, text, time, date, tags, span):
        self.text = text
        if isinstance(date, str):
            self.date = datetime.fromisoformat(date)
        else:
            self.date = date
        self.tags = tags
        self.span = span
        self.time = time

    def __str__(self):
        if _force_hex:
            return self.entry()
        else:
            return f"[tdb:{self.iso_str()}] {self.text}"

    def iso_str(self): return self.date.isoformat(' ')

    def entry(self):
        return f"[tdb:{hex(self.time)}] {self.text}"
    
    def asdict(self):
        return {'text': self.text, 'time': self.time, 'date': self.date.isoformat(" "), 'tags': self.tags, 'span':self.span }


def register_cmd(func):
    global _record_cmds
    _record_cmds.append(func)
    pass


def make_record(date, text):
    return f"\n[tdb:{date}] {text}"


def add_record(text):
    dt = tdb.db.get_mtime()
    ns = time.time_ns()
    # convert to microseconds for datetime compliance
    ns = int(ns/1E3)

    if (ns/1E6) - dt > 1.0: ns = int(int(ns/1E6)*1E6)
    # if (ns/1E9) - dt > 1.0: ns = int(int(ns/1E9)*1E9)
    record = make_record(hex(ns), text)
    tdb.db.append_immediate(record)
    tdb.db.archive(record, False)

    print("Record added successfully!")
    for r in _record_cmds: r(text)


def deduplicate_records(in_records):
    dedupe = []
    for r1 in in_records:
        new = True
        for r2 in dedupe:
            if r1.date == r2.date: new = False; break
        if new: dedupe.append(r1)
    return dedupe


def modify_db_records(previous, current):
    records = split_records(previous)
    new_records = split_records(current)
    dedupe = deduplicate_records(new_records)
    if len(new_records) != len(dedupe): print("Warning: duplicate dates found. Ignoring those entries.")
    new_records = dedupe
    found = []
    mods = adds = dels = 0
    for r1 in new_records:
        modified = None
        new = True
        for r2 in records:
            if str(r1) != str(r2) and r1.iso_str() == r2.iso_str():
                modified = r2
                found.append(r2)
                new = False
                break
            elif r1.iso_str() == r2.iso_str():
                found.append(r2)
                new = False
                break
        
        if modified:
            tdb.db.replace(r2.entry(), r1.entry()); mods += 1
        elif new:
            # print(f"new: {r1}")
            # for r2 in records:
            #     print((r1.iso_str()," != ",r2.iso_str()))
            tdb.db.append(r1.entry()); adds+=1
            pass
    for r1 in records:
        if not r1 in found:
            # print(f"del: {r1}")
            tdb.db.archive(r1.entry()); dels+=1
            pass
    
    if adds or mods or dels: print("".ljust(32, "="))
    if adds: print(f"Inserted {adds} record{'s' if adds > 1 else ''}.")
    if mods: print(f"Modified {mods} record{'s' if mods > 1 else ''}.")
    if dels: print(f"Archived {dels} record{'s' if dels > 1 else ''}.")
    
    for r in _record_cmds: r(current)


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

def stringify_records(options=None):
    results = []
    results = split_db_records(options)
    out = ""
    if options and options["as"] == "json":
        res = [r.asdict() for r in results]
        out = json.dumps(res, indent=2)
    elif options and options["as"] == "html":
        out = tdb.html.build_html(list(reversed(results)))
    elif options and options["as"] == "html_entries":
        out = tdb.html.build_html_entries(list(reversed(results)))
    elif options and options["as"] == "list":
        out = "".join([str(r).splitlines()[0]+"\n" for r in results])
        out = out.strip()
    elif options and options["as"] == "tags":
        tags = {}
        for r in results:
            for t in r.tags:
                if t[0] in tags: tags[t[0]] += 1
                else: tags[t[0]] = 1
        out = json.dumps(tags, indent=2)
    else:
        out = "".join([str(r) for r in results])
        out = out.strip()
    return out


def print_records(options=None):
    if out := stringify_records(options): print(out)


def filter_records(records : list, options : list):
    max_id = len(records)-1
    filtered = records.copy()

    dates = options["dates"] if options else []
    span = options["span"].copy() if options else []
    otags = options["otags"] if options else []
    ntags = options["ntags"] if options else []
    atags = options["atags"] if options else []
    acontains = options["acontains"] if options else []
    ocontains = options["ocontains"] if options else []
    ncontains = options["ncontains"] if options else []

    if span:
        if all(map(lambda x: isinstance(x, int), span)):
            span = sorted([span[0], span[0]+span[1]])
            span[0] = min(max(0, span[0]+max_id+1), max_id)
            span[1] = min(max(0, span[1]+max_id+1), max_id)
            filtered = filtered[span[0]:span[1]]

        elif isinstance(span[0], int):
            span[0] = min(max(0, span[0]+max_id+1), max_id)
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
            last["text"] = section
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