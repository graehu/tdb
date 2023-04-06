import re
import os
from datetime import datetime
import json

# This is the format: "2023-04-05T09:59:33"
re_record = re.compile(r'^(\[(\d{4}\-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] )', re.MULTILINE | re.IGNORECASE)

def add_record(db_file, string):
    now = datetime.now()
    now = now.isoformat(" ", "seconds")
    with open(db_file, "a") as f:
        f.write(f"[{now}] {string}\n")

    print("Record added successfully!")


def print_records(db_file):
    results = []
    if os.path.exists(db_file):
        with open(db_file) as fd:
            results = split_records(fd.read())

        results = [{"date": k.isoformat(" "),  "text": v} for k, v in results.items()]
        print(json.dumps(results, indent=2))
    else: print([])


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