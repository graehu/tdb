import re
import csv
import tdb.records


def _safe_re_search(string, position, pattern) -> int:
    match = pattern.search(string, position)
    return match.span()[0] if match else -1


def print_tags():
    import json
    records = tdb.records.split_db_records()
    results = []
    for k, v in records.items():
        tags = find_tags(v)
        if tags: results.append({"date": k.isoformat(" "), "text": v, "tags": tags})
    print(json.dumps(results, indent=2))
    pass


def find_tags(text: str):
    re_tag = re.compile(r'\s@(\w+)')
    re_end = re.compile(r'([\r\n])')
    tags = []
    tag_spans = []
    for match in re_tag.finditer(text):

        tag = match.group(1)
        end = match.span()[1]
        match_start = match.span()[0]
        skip = False

        for span in tag_spans:
            if span[0] < match_start and span[1] > match_start:
                skip = True
                break

        if not skip and len(text) > end+1 and text[end] == ':':
            start = end+1
            end = _safe_re_search(text, start, re_end)
            tag_spans.append((start, end))
            csv_text = text[start:end].strip()
            csv_reader = csv.reader([csv_text], delimiter=',', quotechar='"')
            items = []
            for row in csv_reader:
                for item in row:
                    items.append(item.strip())
            
            tags.append((tag, items))
        elif not skip:
            tags.append((tag, []))

    return tags