import re
import shlex

re_tag = re.compile(r'\s@(\w+)')
_cmd_tags = {}

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
        pattern = "\s?@"+tag[0]
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
    print(f"Registering '@{tag}' cmds.")
    _cmd_tags[tag] = func


def parse_cmds(context, text, records):
    tags = find_tags(text)
    for tag in tags:
        if tag[0] in _cmd_tags:
            text = _cmd_tags[tag[0]](context, text, records, tags, tag[1])
    return text


def remove_tag_cmd(text, args, tags):
    for arg in args:
        if arg.startswith("@"):
            arg = arg[1:]
            if arg == "tdb": continue
            rtag = filter(lambda x: x[0] == arg, tags)
            rtag = list(rtag)
            if rtag:
                print(f"@tdb: remove {rtag[0]}")
                text = replace_tag(text, rtag[0], "")
    return text


def tag_cmds(context, text, records, tags, args):
    print(context+" : "+str(("tdb", args)))
    text = replace_tag(text, ("tdb", args), "")
    
    try:
        args = shlex.split(args.lower())
    except ValueError as e:
        args = []
        pass

    if args:
        if args[0] == "remove":
            text = remove_tag_cmd(text, args[1:], tags)
        if args[0] == "add":
            print("@tdb: add doesn't work! We'll need access to records here.")
        
    return text

register_cmd("tdb", tag_cmds)