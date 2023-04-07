import re
from datetime import datetime
import json
import tdb.db

# This is the format: "2023-04-05T09:59:33"
re_record = re.compile(r'^(\[(\d{4}\-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] )', re.MULTILINE | re.IGNORECASE)


def make_record(text):
    now = datetime.now()
    now = now.isoformat(" ", "seconds")
    return f"[{now}] {text}\n"


def add_record(text):
    record = make_record(text)
    tdb.db.append(record)
    print("Record added successfully!")


def print_records():
    results = []
    results = split_db_records()
    results = [{"date": k.isoformat(" "),  "text": v} for k, v in results.items()]
    print(json.dumps(results, indent=2))


def split_db_records():
    return split_records(tdb.db.get_text())


def split_records(text: str):
    splits = re_record.split(text)
    records = {}
    datekey = None
    for split in splits:
        if match := re_record.match(split):
            datekey = datetime.fromisoformat(match.group(2))
        elif datekey:
            records[datekey] = split
    return records