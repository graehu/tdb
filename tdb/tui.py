import re
import platform
import tdb.db
import tdb.cli
import tdb.records
import tdb.tags

_cmd_tags = {}

def register_cmd(tag, func):
    _cmd_tags[tag] = func


def parse_cmd(cmdline, text, context="tui"):
    tags = tdb.tags.find_tags(cmdline)
    for tag in tags:
        if tag[0] in _cmd_tags:
            text = _cmd_tags[tag[0]](context, text, tag[1])
    return text

def update_db(previous, text):
    if not text or text[-1] != "\n": text += "\n"
    old_records = tdb.records.split_records(previous)
    new_records = tdb.records.split_records(text)
    tdb.records.modify_db_records(old_records, new_records)


def get_next(text, start, char=" ", forward=True):
    if forward:
        while start < len(text) and text[start] == char: start += 1
        start = text.find(char, start)
        start = start if start > 0 else len(text)

    else:
        while start-1 > 0 and text[start-1] == char: start -= 1
        start = len(text)-text[::-1].find(char, len(text)-start)
        start = start if start < len(text) else 0
    return start


def open_tui(options, edit_cmd, rm_cmd):
    try:
        import curses
    except:
        print("Failed to import curses, which is required for tui.")
        if platform.system() == "Windows":
            print("Consider installing windows-curses:")
            print("\tpip install windows-curses")
        return
    outcmd = ""
    is_linux = platform.system() == "Linux"

    def __curses_cli(stdscr):
        nonlocal outcmd
        nonlocal options

        def switch_call(func, *args):
            curses.reset_shell_mode()
            stdscr.clear()
            stdscr.refresh()
            func(*args)
            curses.reset_prog_mode()
            stdscr.clear()
            stdscr.refresh()

        def print_wait(in_str): switch_call(lambda x=in_str: input(f"'{x}'\npress enter to continue"))
            
        key = 0
        page_y = 0
        query = tdb.cli.get_text()
        last_query = query
        curs_index = len(query)
        text_entry = None
        stdscr.clear()
        stdscr.refresh()

        curses.start_color()
        curses.noecho()
        curses.use_default_colors()
        col_default = len(tdb.cli.ANSICodes)
        col_status = len(tdb.cli.ANSICodes)+1
        curses.init_pair(col_default, tdb.cli._init_colour(800,800,800), -1)
        curses.init_pair(col_status, tdb.cli._init_colour(0,0,0), tdb.cli._init_colour(800,800,800))
        for col in tdb.cli._init_colour.cols.values(): curses.init_color(*col)
        for k, v in tdb.cli.ANSICodes.items():
            if k != "end": 
                tdb.cli.ANSICodes[k] += [re.compile(f"({re.escape(v[0])})(.*?)({re.escape(tdb.cli.ANSICodes['end'][0])})", re.MULTILINE)]
                if v[1]: curses.init_pair(*v[1])
            else: tdb.cli.ANSICodes[k] += [None]
        
        curses_text = tdb.records.stringify_db_records(options, True)
        lines = curses_text.splitlines()
        curses.curs_set(0)

        class Key:
            def backspace(key): return key == (263 if is_linux else 8)
            def delete(key): return key == 330
            def right(key): return key == 261
            def left(key): return key == 260
            def ctrl_backspace(key): return key == (8 if is_linux else 127)
            def ctrl_delete(key): return key == (520 if is_linux else 527)
            def ctrl_left(key): return key == (546 if is_linux else 443)
            def ctrl_right(key): return key == (561 if is_linux else 444)
            def enter(key): return key == 10 or key == 13

        while (key != ord('q')) or text_entry:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            max_y = max(0, len(lines)-(height-1))
            def update_text():
                nonlocal max_y, curses_text, options, lines
                tdb.db.serialise()
                options = tdb.cli.parse_options("tui "+query)
                curses_text = tdb.records.stringify_db_records(options, True)
                lines = curses_text.splitlines()
                max_y = max(0, len(lines)-(height-1))
            
            if text_entry:
                # print_wait(f"pressed {chr(key)} ord {key}")

                if Key.backspace(key): 
                    if curs_index != 0:
                        query = query[:curs_index-1]+query[curs_index:]
                        curs_index -= 1

                elif Key.delete(key):
                    if curs_index != len(query):
                        query = query[:curs_index]+query[curs_index+1:]

                elif Key.ctrl_backspace(key):
                    end = get_next(query, curs_index, forward=False) 
                    if end != curs_index: query = query[:end]+query[curs_index:]; curs_index = end
                    while curs_index-1 > 0 and query[curs_index-1] == ' ': query = query[:curs_index-1]+query[curs_index:]; curs_index -= 1

                elif Key.ctrl_delete(key):
                    end = get_next(query, curs_index) 
                    if end != curs_index: query = query[:curs_index]+query[end:]
                    while curs_index < len(query) and query[curs_index] == ' ': query = query[:curs_index]+query[curs_index+1:]
                     
                elif Key.ctrl_right(key): curs_index = get_next(query, curs_index)
                elif Key.ctrl_left(key): curs_index = get_next(query, curs_index, forward=False) 
                elif Key.left(key): curs_index -= 1
                elif Key.right(key): curs_index += 1
                elif Key.enter(key):
                    if text_entry == "cmd":
                        opts = options
                        opts["as"] = None
                        before = tdb.records.stringify_db_records(opts)
                        after = parse_cmd(" @"+query, before)
                        update_db(before, after)
                        query = last_query
                    update_text()
                    text_entry = None
                    curses.curs_set(0)
                elif key not in [curses.KEY_ENTER, curses.KEY_BACKSPACE]:
                    query = query[:curs_index]+chr(key)+query[curs_index:]
                    curs_index+=1
                curs_index = max(min(len(query), curs_index), 0)
            else:
                if key == curses.KEY_DOWN: page_y += 1
                elif key == curses.KEY_UP: page_y -= 1
                elif key == ord(' '):
                    if max_y == page_y: page_y = 0
                    else: page_y += height-1
                elif key == ord('/'):
                    text_entry = "query"
                    curses.curs_set(2)
                elif key == ord('@'):
                    text_entry = "cmd"
                    last_query = query
                    query = ""
                    curs_index = 0
                    curses.curs_set(2)
                elif key == ord('e'):
                    switch_call(edit_cmd, options, False)
                    update_text()
                elif key == ord('r'):
                    switch_call(rm_cmd, options, False)
                    update_text()
                
            page_y = min(max_y, max(0, page_y))

            display = lines[page_y:]
            for num, line in enumerate(display):
                if num >= height-1: break
                stripped = line
                for v in [v[-1] for v in tdb.cli.ANSICodes.values() if v[-1]]:
                    stripped = v.sub(r"\2", stripped)
                
                stripped = stripped[0:width]
                stdscr.addstr(num, 0, stripped, curses.color_pair(col_default))
                
                matches = []
                for k,v in tdb.cli.ANSICodes.items():
                    if not v[-1]: continue
                    for match in v[-1].finditer(line):
                        matches.append([match, v])
                
                delta = 0
                matches = sorted(matches, key=lambda x: x[0].span()[0])
                for match, v in matches:
                    try: stdscr.addstr(num, match.span()[0]-delta, match.group(2), curses.A_BOLD|curses.color_pair((v[1][0]) if v[1] else col_default))
                    except: pass
                    delta += len(match.group(0))-len(match.group(2))
                    line = v[-1].sub(r"\2", line)
                        
            opchar = "@" if text_entry == "cmd" else "/"
            stdscr.addstr(height-1, 0, f"{opchar}{query}", (curses.A_BOLD|curses.A_ITALIC if text_entry else 0)|curses.color_pair(col_status))
            statusbarstr = f" | '@' to enter cmd | 'e' to edit | 'r' to rm | 'space': down | 'q': to exit | pos: {page_y}/{max_y}"
            stdscr.attron(curses.color_pair(col_status))
            stdscr.addstr(height-1, len(f"/{query}"), statusbarstr)
            stdscr.addstr(height-1, len(f"/{query}")+len(statusbarstr), " " * (width - (len(f"/{query}")+len(statusbarstr)) - 1))
            stdscr.attroff(curses.color_pair(col_status))
            stdscr.move(height-1, curs_index+1)

            stdscr.refresh()
            key = stdscr.getch()
    
    curses.wrapper(__curses_cli)