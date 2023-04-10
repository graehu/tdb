import re
from datetime import datetime
import json
import tdb.db
import tdb.tags
import tdb.rake

# This is the format: "2023-04-05 09:59:33"
re_record = re.compile(r'^\[(\d{4}\-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] ', re.MULTILINE | re.IGNORECASE)


def make_record(text):
    now = datetime.now()
    now = now.isoformat(" ", "seconds")
    return f"[{now}] {text}\n"


def add_record(text):
    record = make_record(text)
    tdb.db.append(record)
    print("Record added successfully!")


def print_records(options=None):
    results = []
    results = split_db_records(options)
    for r in results: r.update({"date":r["date"].isoformat(" ")})
    print(json.dumps(results, indent=2))


def split_db_records(options=None):
    return split_records(tdb.db.get_text(), options)


def split_records(text: str, options=None):
    last = None
    current = None
    id = 0
    # TODO: having one id offset will break if I allow multiple ranges
    id_offset = -1
    records = []

    tags = options["tags"] if options else []
    ranges = options["ranges"] if options else []
    contains = options["contains"] if options else []

    def append_record():
        nonlocal records
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
            if not skip and ranges:
                skip = True
                for r in ranges:
                    if all(map(lambda x: isinstance(x, int), r)): # TODO: handle in post filter, needs list len
                        skip = False
                        break
                    elif isinstance(r[0], int): # TODO: handle in post filter, needs list len
                        skip = False
                        break
                    elif isinstance(r[1], int):
                        if r[1] >= 0 and date >= r[0]:
                            if id_offset == -1: id_offset = id
                            if (id - id_offset) < r[1]:
                                skip = False
                                break
                            else:
                                skip = True
                                break
                        elif r[1] >= 0 and date <= r[0]:
                            skip = True
                            break
                        else:
                            skip = False
                            break # TODO: handle in post filter, needs list len
                    elif r[0] <= date <= r[1]:
                        skip = False
                        break
                    if not skip: break
            if not skip and contains: skip = not any([c in section for c in contains])
            if not skip and tags: skip = not any([tdb.tags.contains_tag(section, t) for t in tags])
            if not skip: records.append(last)

    for match in re_record.finditer(text):
        current = {
            "date":datetime.fromisoformat(match.group(1)),
            "text": "",
            "id": 0,
            "span": match.span()
        }
        append_record()
        last = current
    # hack to fix last record text
    current = {"span": [len(text)]}
    append_record()
    final_records = []
    id_offset = -1
    end_date = None
    if ranges:
        for record in records:
            for r in ranges:
                if all(map(lambda x: isinstance(x, int), r)):
                    if id+r[0] < record["id"] <= id+r[0]+r[1]:
                        final_records.append(record)
                        break
                elif isinstance(r[1], int):
                    # tested all the r[1] >= 0 above the given date.
                    if r[1] >= 0:
                        final_records.append(record)

                    elif r[1] < 0 and record["date"] <= r[0]:
                        if id_offset == -1: id_offset = record["id"]
                        if abs(record["id"]-id_offset) < abs(r[1]):
                            final_records.append(record)
                            break
                elif isinstance(r[0], int):
                    if r[0] < 0 and (id+r[0]) < record["id"]:
                        if not end_date:
                            if isinstance(r[1], datetime): end_date = r[1]
                            else: end_date = record["date"] + r[1]
                        if record["date"] <= end_date:
                            final_records.append(record)
                            break
                else:
                    final_records.append(record)
                    break
    else:
        final_records = records
    return final_records


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
