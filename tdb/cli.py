from datetime import datetime, timedelta
import re
import sys
import shlex
import platform
import subprocess


def _init_colour(r,g,b) -> int:
    if (r, g, b) in _init_colour.cols: return _init_colour.cols[(r, g, b)][0]
    _init_colour.id += 1
    _init_colour.cols[(r, g, b)] = (_init_colour.id, r, g, b)
    return _init_colour.id

_init_colour.cols = {}
_init_colour.id = 16 # index past initial 16 cols.

# todo: do something about the missing colours for curses
ANSICodes = {
    "black" : ["\033[0;30m", (1, _init_colour(0, 0, 0), _init_colour(0, 0, 0))],
    "red" : ["\033[0;31m", (2, _init_colour(1000, 300, 300), _init_colour(0, 0, 0))],
    "green" : ["\033[0;32m", (3, _init_colour(300, 1000, 300), _init_colour(0, 0, 0))],
    "brown" : ["\033[0;33m", (4, _init_colour(588, 295, 300), _init_colour(0, 0, 0))],
    "blue" : ["\033[0;34m", (5, _init_colour(300, 300, 1000), _init_colour(0, 0, 0))],
    "purple" : ["\033[0;35m", (6, _init_colour(1000, 300,1000), _init_colour(0, 0, 0))],
    "cyan" : ["\033[0;36m", (7, _init_colour(300, 1000, 1000), _init_colour(0, 0, 0))],
    "light_gray" : ["\033[0;37m", (8, _init_colour(800, 800, 800), _init_colour(0, 0, 0))],
    "dark_gray" : ["\033[1;30m", (9, _init_colour(600, 600, 600), _init_colour(0, 0, 0))],
    "light_red" : ["\033[1;31m", (10, _init_colour(1000, 400, 400), _init_colour(0, 0, 0))],
    "light_green" : ["\033[1;32m", (11, _init_colour(400,400, 1000), _init_colour(0, 0, 0))],
    "yellow" : ["\033[1;33m", (12, _init_colour(1000, 1000, 300), _init_colour(0, 0, 0))],
    "light_blue" : ["\033[1;34m", (13, _init_colour(400, 400, 1000), _init_colour(0, 0, 0))],
    "light_purple" : ["\033[1;35m", (14, _init_colour(1000, 400, 1000), _init_colour(0, 0, 0))],
    "light_cyan" : ["\033[1;36m", (15, _init_colour(400, 1000, 1000), _init_colour(0, 0, 0))],
    "light_white" : ["\033[1;37m", (16, _init_colour(1000, 1000, 1000), _init_colour(0, 0, 0))],
    "bold" : ["\033[1m", None], #(7, curses.A_BOLD, _init_colour(0, 0, 0))],
    "faint" : ["\033[2m", None], # (8, curses.A_DIM, _init_colour(0, 0, 0))], # todo: test this actually works?
    "italic" : ["\033[3m", None], # (9, curses.A_ITALIC, _init_colour(0, 0, 0))],
    "underline" : ["\033[4m", None],# (10, curses.A_UNDERLINE, _init_colour(0, 0, 0))],
    "blink" : ["\033[5m", None], # (11, curses.A_BLINK, _init_colour(0, 0, 0))],
    "negative" : ["\033[7m", None],# (12, curses.A_REVERSE, _init_colour(0, 0, 0))], # todo: test this actually works?
    "crossed" : ["\033[9m", None], # (13, curses.A_PROTECT, _init_colour(0, 0, 0))], # todo: test this actually works?
    "end" : ["\033[0m", None],
}


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


def open_tui(curses_text):
    try:
        import curses
    except:
        print("Failed to import curses, which is required for tui.")
        if platform.system() == "Windows":
            print("Consider installing windows-curses:")
            print("\tpip install windows-curses")
        return
    def __curses_cli(stdscr):
        nonlocal curses_text
        key = 0
        page_y = 0
        stdscr.clear()
        stdscr.refresh()

        curses.start_color()
        for col in _init_colour.cols.values(): curses.init_color(*col)
        for k, v in ANSICodes.items():
            if k != "end": 
                ANSICodes[k] += [re.compile(f"({re.escape(v[0])})(.*?)({re.escape(ANSICodes['end'][0])})", re.MULTILINE)]
                if v[1]: curses.init_pair(*v[1])
            else: ANSICodes[k] += [None]
        
        col_default = len(ANSICodes)
        col_status = len(ANSICodes)+1
        
        curses.init_pair(col_default, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(col_status, curses.COLOR_BLACK, curses.COLOR_WHITE)

        # for re_pat in [v[-1] for v in ANSICodes.values()]:
        #     if re_pat:
        #         for match in re_pat.finditer(curses_text):
        #             curses_text = curses_text.replace(match.group(0), match.group(2), 1)
                # curses_text = curses_text[0:span[0]]+match.groups()[0]+curses_text[span[1]:]
            # curses_text = re_pat.sub(r"\2", curses_text, 100)

        lines = curses_text.splitlines()
        curses.curs_set(0)

        while (key != ord('q')):
            stdscr.clear()
            height, width = stdscr.getmaxyx()

            if key == curses.KEY_DOWN: page_y += 1
            elif key == curses.KEY_UP: page_y -= 1

            page_y = min(max(0, len(lines)-(height-1)), max(0, page_y))

            display = lines[page_y:]
            for num, line in enumerate(display):
                if num >= height-1: break
                stripped = line
                for v in [v[-1] for v in ANSICodes.values() if v[-1]]:
                    stripped = v.sub(r"\2", stripped)
                
                stripped = stripped[0:width]
                stdscr.addstr(num, 0, stripped, curses.color_pair(col_default))
                
                matches = []
                for k,v in ANSICodes.items():
                    if not v[-1]: continue
                    for match in v[-1].finditer(line):
                        matches.append([match, v])
                
                delta = 0
                matches = sorted(matches, key=lambda x: x[0].span()[0])
                for match, v in matches:
                    try: stdscr.addstr(num, match.span()[0]-delta, match.group(2), curses.color_pair(v[1][0] if v[1] else col_default))
                    except: pass
                    delta += len(match.group(0))-len(match.group(2))
                    line = v[-1].sub(r"\2", line)
                        

            statusbarstr = "Press 'q' to exit | Pos: {}".format(page_y)
            stdscr.attron(curses.color_pair(col_status))
            stdscr.addstr(height-1, 0, statusbarstr)
            stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
            stdscr.attroff(curses.color_pair(col_status))

            stdscr.refresh()
            key = stdscr.getch()
    
    curses.wrapper(__curses_cli)