import re
from datetime import datetime
import json
import tdb.db
import tdb.tags
import tdb.rake

# This is the format: "2023-04-05 09:59:33"
re_record = re.compile(r'^\[(\d{4}\-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] ?', re.MULTILINE | re.IGNORECASE)

class Record(object):
    text = ""
    date = None
    tags = []
    span = (0,0)
    id = -1
    def __init__(self, text, date, tags, span, id):
        self.text = text
        if isinstance(date, str):
            self.date = datetime.fromisoformat(date)
        else:
            self.date = date
        self.tags = tags
        self.span = span
        self.id = id

    def __str__(self):
        return f"[{self.date.isoformat(' ')}] {self.text}"
    
    def asdict(self):
        return {'text': self.text, 'date': self.date.isoformat(" "), 'tags': self.tags, 'span':self.span, 'id':self.id }


def make_record(date, text):
    date = date.isoformat(" ", "seconds")
    return f"[{date}] {text}\n"


def add_record(text):
    # ensure new records are at least a second apart.
    # else append.
    dates = re_record.findall(tdb.db.get_text())
    last = datetime.fromisoformat(dates[-1])
    now = datetime.now()
    delta = (now-last).seconds+((now-last).microseconds)/1E6
    if  delta > 1.0:
        record = make_record(now, text)
    else:
        record = f"tdb {delta:02.2f}: "+text
    tdb.db.append(record)
    print("Record added successfully!")


def modify_records(records, text):
    new_records = split_records(text)
    found = []
    text = tdb.db.get_text()
    for r1 in new_records:
        modified = None
        new = True
        for r2 in records:
            if str(r1) != str(r2) and r1.date == r2.date:
                modified = r2
                found.append(r2)
                break
            elif r1.date == r2.date:
                found.append(r2)
                new = False
                break
        
        if modified:
            tdb.db.replace(str(r2), str(r1))
        elif new:
            # print(f"new: {r1}")
            tdb.db.append(str(r1))
            pass
    for r1 in records:
        if not r1 in found:
            # print(f"del: {r1}")
            tdb.db.replace(str(r1), "")
            pass
    
    print("Records modified successfully!")


def print_records(options=None):
    results = []
    results = split_db_records(options)
    if options and options["format"] == "json":
        res = [r.asdict() for r in results]
        print(json.dumps(res, indent=2))
    else:
        out = "".join([str(r) for r in results])
        print(out.strip())


def split_db_records(options=None):
    return split_records(tdb.db.get_text(), options)


def split_records(text: str, options=None):
    last = None
    current = None
    id = 0
    id_offset = -1

    filtered = []

    tags = options["tags"] if options else []
    ntags = options["ntags"] if options else []
    span = options["span"] if options else []
    contains = options["contains"] if options else []
    ncontains = options["ncontains"] if options else []

    def append_record():
        nonlocal filtered
        nonlocal last
        nonlocal current
        nonlocal id
        nonlocal id_offset

        if last:
            id += 1
            x,y = last["span"][1], current["span"][0]
            section = text[x:y]
            date = last["date"]
            last["text"] = section
            last["span"] = (x ,y)
            last["id"] = id

            skip = False
            if not skip and span:
                skip = True

                if all(map(lambda x: isinstance(x, int), span)): skip = False
                elif isinstance(span[0], int): skip = False
                elif isinstance(span[1], int):

                    if span[1] >= 0 and date >= span[0]:
                        if id_offset == -1: id_offset = id
                        skip = not (id - id_offset) < span[1]
                    else:
                        skip = span[1] >= 0 and date <= span[0]

                elif span[0] <= date <= span[1]: skip = False

            sec_low = section.lower()

            if not skip and contains: skip = not any([c in sec_low for c in contains])
            if not skip and ncontains: skip = any([c in sec_low for c in ncontains])
            if not skip and tags: skip = not any([tdb.tags.contains_tag(sec_low, t) for t in tags])
            if not skip and ntags: skip = any([tdb.tags.contains_tag(sec_low, t) for t in ntags])
            if not skip: filtered.append(last)

    for match in re_record.finditer(text):
        current = {
            "date": datetime.fromisoformat(match.group(1)),
            "text": "",
            "id": 0,
            "tags": [],
            "span": match.span()
        }
        append_record()
        last = current
    # hack to fix last record text
    current = {"span": [len(text)]}
    append_record()

    id_offset = -1
    end_date = None
    if span:
        # for record in records:
        def post_filter(record):
            nonlocal span
            nonlocal id_offset
            nonlocal id
            nonlocal end_date
            if all(map(lambda x: isinstance(x, int), span)):
                return id+span[0] < record["id"] <= id+span[0]+span[1]

            elif isinstance(span[1], int):
                # tested all the r[1] >= 0 above the given date.
                if span[1] >= 0: return True
                # TODO: fix this logic, 1d,-1 is valid and this doesn't get the right record
                elif span[1] < 0 and record["date"] <= span[0]:
                    if id_offset == -1: id_offset = record["id"]
                    return abs(record["id"]-id_offset) < abs(span[1])

            elif isinstance(span[0], int):
                if span[0] < 0 and (id+span[0]) < record["id"]:
                    if not end_date:
                        if isinstance(span[1], datetime): end_date = span[1]
                        else: end_date = record["date"] + span[1]

                    return record["date"] <= end_date
                
            else: return True
        
        filtered = filter(post_filter, filtered)
    
    filtered = [Record(**r) for r in filtered]
    return filtered


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