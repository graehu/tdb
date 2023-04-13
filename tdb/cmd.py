import sys
import subprocess


def get_text():
    if sys.stdin.isatty():
        text = " ".join(sys.argv[2:]).strip()
    else:
        text = sys.stdin.read()
    return text


def get_command():
    return sys.argv[1]


def parse_options():
    splits = sys.argv[2:]
    contains = []
    ncontains = []
    span = None
    tags = []
    ntags = []
    format = ""
    for split in splits:
        if split.startswith("span:"):
            split = split[len("span:"):]
            split = split.split(",",maxsplit=2)
            span = parse_span(split)
        elif split.startswith("form:"):
            split = split[len("form:"):]
            format = split.lower()
        elif split.startswith("-@"):
            ntags.append(split[2:].lower())
        elif split.startswith("@"):
            tags.append(split[1:].lower())
        elif split.startswith("-"):
            ncontains.append(split[1:].lower())
        else:
            contains.append(split.lower())

    return {"tags":tags, "ntags":ntags, "span":span, "contains":contains, "ncontains":ncontains, "format":format}


def parse_span(args):
    from datetime import datetime, timedelta
    import re
    now = datetime.now()
    operations = []
    
    for select in args:
        select = select.strip()
        try:
            select = datetime.fromisoformat(select)
            operations.append(select)
        except ValueError:
            units = [re.search("(-?\d+)"+u, select, re.IGNORECASE) for u in ["y","w","d","h","m","s"]]
            units = [int(u.group(1)) if u else 0 for u in units]
            days = units[0]*365+units[1]*7+units[2]
            seconds = units[3]*(60*60)+units[4]*60+units[5]

            if days or seconds:
                if operations:
                    if isinstance(operations[0], int):
                        operations.append(timedelta(days=days, seconds=seconds))
                    else:
                        operations.append(operations[0]+timedelta(days=days, seconds=seconds))
                else:
                    days = abs(days)*-1
                    seconds = abs(seconds)*-1
                    operations.append(now+timedelta(days=days, seconds=seconds))
            else:
                try:
                    num = int(select)
                    if operations:
                        operations.append(num)
                    else:
                        operations.append(abs(num)*-1)
                except ValueError:
                    print("bad record range format: "+select)
                    pass

    if len(operations) == 1: operations.append(now)
    return operations


def run(text):
    subprocess.run(text, shell=True)