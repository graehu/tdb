from datetime import datetime, timedelta
import sys
import curses
import shlex
import platform
import subprocess


class ANSICodes:
    black = "\033[0;30m"
    red = "\033[0;31m"
    green = "\033[0;32m"
    brown = "\033[0;33m"
    blue = "\033[0;34m"
    purple = "\033[0;35m"
    cyan = "\033[0;36m"
    light_gray = "\033[0;37m"
    dark_gray = "\033[1;30m"
    light_red = "\033[1;31m"
    light_green = "\033[1;32m"
    yellow = "\033[1;33m"
    light_blue = "\033[1;34m"
    light_purple = "\033[1;35m"
    light_cyan = "\033[1;36m"
    light_white = "\033[1;37m"
    bold = "\033[1m"
    faint = "\033[2m"
    italic = "\033[3m"
    underline = "\033[4m"
    blink = "\033[5m"
    negative = "\033[7m"
    crossed = "\033[9m"
    end = "\033[0m"


def enable_ansi():
    kernel32 = ctypes.windll.kernel32
    ENABLE_PROCESSED_OUTPUT = 0x0001
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    out_handle = kernel32.GetStdHandle(subprocess.STD_OUTPUT_HANDLE)
    # GetConsoleMode fails if the terminal isn't native.
    mode = ctypes.c_int32()
    if kernel32.GetConsoleMode(out_handle, ctypes.byref(mode)) == 0: return
    if not (mode.value & ENABLE_VIRTUAL_TERMINAL_PROCESSING):
        kernel32.SetConsoleMode(out_handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING | ENABLE_PROCESSED_OUTPUT)


if platform.system() == "Windows":
    import ctypes
    enable_ansi()
    

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
    print("-{text}: ".ljust(16)+"This text must not be included.")
    print("\nNote, for options text must be quoted if there are spaces.")


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
    print("running: "+text)
    subprocess.run(text, shell=True)


def popen(text):
    print("running: "+text)
    return subprocess.Popen(text, shell=True)


__curses_lines = []
def __curses_cli(stdscr):
    global __curses_lines
    key = 0
    page_y = 0
    stdscr.clear()
    stdscr.refresh()

    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.curs_set(0)

    while (key != ord('q')):
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        if key == curses.KEY_DOWN: page_y += 1
        elif key == curses.KEY_UP: page_y -= 1

        page_y = max(0, page_y)
        page_y = min(len(__curses_lines)-height, page_y)

        display = __curses_lines[page_y:]
        for num, line in enumerate(display):
            if num >= height-1: break
            stdscr.addstr(num, 0, line[0:width], curses.color_pair(1))
        stdscr.refresh()
        key = stdscr.getch()


def as_less(lines):
    global __curses_lines
    __curses_lines = lines
    curses.wrapper(__curses_cli)