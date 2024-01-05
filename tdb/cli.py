from datetime import datetime, timedelta
import sys
import subprocess
import shlex
import platform


class Colours:
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"


if platform.system == "Windows":
    kernel32 = __import__("ctypes").windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    del kernel32


def isatty():
    return sys.stdout.isatty()


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
    dates = []
    ocontains = []
    ncontains = []
    acontains = []
    atags = []
    otags = []
    ntags = []
    span = []
    format = ""
    if splits:
        for split in splits:
            if split.startswith("span:"): span = parse_span(split[len("span:"):].split(",",maxsplit=2))
            elif split.startswith("as:"): format = split[len("as:"):].lower()
            elif split.startswith("+@"): atags.append(split[2:].lower())
            elif split.startswith("-@"): ntags.append(split[2:].lower())
            elif split.startswith("@"): otags.append(split[1:].lower())
            elif split.startswith("+"): acontains.append(split[1:].lower())
            elif split.startswith("-"): ncontains.append(split[1:].lower())
            else:
                try: dates.append(datetime.fromisoformat(split))
                except ValueError: ocontains.append(split.lower())

    return {"dates":dates, "otags":otags, "atags":atags, "ntags":ntags,
            "acontains":acontains, "ocontains":ocontains, "ncontains":ncontains,
            "span":span, "as":format}


def parse_span(args):
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