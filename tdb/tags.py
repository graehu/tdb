import re
import csv

re_tag = re.compile(r'\s@(\w+)')

def _safe_re_search(string, position, pattern) -> int:
    match = pattern.search(string, position)
    return match.span()[0] if match else -1


def find_tags(text: str):
    #edge case, text can't start with @
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

def contains_tag(text, tag):
    for match in re_tag.finditer(text):
        if match.group(1) == tag:
            return True
    return False

