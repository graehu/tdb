import re
import csv
from typing import List, Tuple

def _safe_search(string, position, pattern) -> int:
    match = pattern.search(string, position)
    return match.span()[0] if match else -1


def find_tags(text: str) -> List[Tuple[str, List[str]]]:
    re_tag = re.compile(r'@(\w+)')
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
            end = _safe_search(text, start, re_end)
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

if __name__ == "__main__":
    import os
    import time
    os.chdir(os.path.dirname(__file__))
    with open("test.txt") as fd:
        tag_speed = time.time()
        result = find_tags(fd.read())
        tag_speed = time.time()-tag_speed

    for tag, csv_data in result:
        print(f'{tag}: {csv_data}')
    print(tag_speed)