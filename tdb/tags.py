import re
import tdb.config

re_tag = re.compile(r'\s@(\w+)')
_cmd_tags = {}
_colours = ["red", "green", "brown", "blue", "purple", "cyan", "light_red", "light_green", "yellow", "light_blue", "light_purple", "light_cyan"]

_config = tdb.config.get("tags", {})

def register(tags):
    for tag in tags:
        if not tag[0] in _config:
            _config[tag[0]] = {"colour": _colours[len(_config)%len(_colours)]}


def get_colour(tag) -> str:
    col = _config[tag]["colour"]
    if not col in _colours:
        print(f"warning: '{tag}' has invalid colour '{col}'")
        col = "light_cyan"
        _config[tag]["colour"] = col
    return col


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
            if end == -1: end = len(text)
            tag_spans.append((start, end))
            tags.append((tag, text[start:end].strip()))
            
        elif not skip:
            tags.append((tag, ""))

    return tags

def replace_tag(text: str, tag, repl):
    #edge case, text can't start with @
    if tag[1]:
        pattern = "\s?@"+tag[0]+":\s*"+re.escape(tag[1])
    else:
        pattern = "\s?@"+tag[0]+"(?!\S)"
    re_sub_tag = re.compile(pattern)
    return re_sub_tag.sub(repl, text)


def contains_tag(text, tag):
    text = text.lower()
    tag = tag.lower()
    for match in re_tag.finditer(text):
        if match.group(1) == tag:
            return True
    return False


def register_cmd(tag, func):
    _cmd_tags[tag] = func


def parse_cmds(context, text):
    tags = find_tags(text)
    for tag in tags:
        if tag[0] in _cmd_tags:
            text = _cmd_tags[tag[0]](context, text, tag[1])
    return text

