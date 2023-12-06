import sys
import subprocess
import shlex


def get_text():
    if sys.stdin.isatty():
        text = " ".join(sys.argv[2:]).strip()
    else:
        text = sys.stdin.read()
    return text


def get_command(override = ""):
    if override: return shlex.split(override)[0]
    return sys.argv[1]

def print_options():
    print("Options:")
    print("span: ".ljust(16)+"The records to select, example: span:7d is the last 7 days.")
    print("as: ".ljust(16)+"The format to see the records in. Only valid for show currently. [html, json, list, tags]")
    print("@{tag}: ".ljust(16)+"This tag or any others must be included, example: @notes @school, records must have either.")
    print("+@{tag}: ".ljust(16)+"This tag and any others must be included. i.e. +@notes +@school, records must have both.")
    print("-@{tag}: ".ljust(16)+"This tag must not be included. i.e. -@notes @school, records for school, no notes.")
    print("{text}: ".ljust(16)+"This text is optional.")
    print("+{text}: ".ljust(16)+"This text must be included.")
    print("-{text}: ".ljust(16)+"This text must not be included")
    print("\nNote, text must be quoted if there are spaces.")


def parse_options(override = ""):
    if override: splits = shlex.split(override)[1:]
    else: splits = sys.argv[2:]
    ocontains = []
    ncontains = []
    acontains = []
    atags = []
    otags = []
    ntags = []
    span = None
    format = ""
    for split in splits:
        if split.startswith("span:"): span = parse_span(split[len("span:"):].split(",",maxsplit=2))
        elif split.startswith("as:"): format = split[len("as:"):].lower()
        elif split.startswith("+@"): atags.append(split[2:].lower())
        elif split.startswith("-@"): ntags.append(split[2:].lower())
        elif split.startswith("@"): otags.append(split[1:].lower())
        elif split.startswith("+"): acontains.append(split[1:].lower())
        elif split.startswith("-"): ncontains.append(split[1:].lower())
        else: ocontains.append(split.lower())

    return {"otags":otags, "atags":atags, "ntags":ntags,
            "acontains":acontains, "ocontains":ocontains, "ncontains":ncontains,
            "span":span, "as":format}


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


def get_safe_filename():
    return "".join([c for c in "_".join(sys.argv[1:]) if c.isalpha() or c.isdigit() or c in ['_', '-', "+"]]).rstrip()


def run(text):
    print("running "+text)
    subprocess.run(text, shell=True)


def popen(text):
    print("running "+text)
    return subprocess.Popen(text, shell=True)