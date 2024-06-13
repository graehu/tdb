import sys
import os
import time
import signal
import platform
import tempfile
from datetime import datetime
import tdb.cli
import tdb.tags
import tdb.config
import tdb.records

_last_text = ""
_start_text = ""
_start_time = None

def file_updated(file, context, update_cb):
    global _last_text
    text = open(file).read()
    text = tdb.tags.parse_cmds(context, text)
    if update_cb: text = update_cb(_last_text, text)
    _last_text = text
    open(file, "w").write(text)


def start(name, content="", ext=".txt", update_cb=None):
    global _last_text
    global _start_text
    global _start_time
    _start_time = time.time_ns()
    _start_text = content
    _last_text = content
    name += "-"
    temp_file = tempfile.NamedTemporaryFile(mode="w+", prefix=name, suffix=ext, delete=False)
    print(f"session: {temp_file.name} {datetime.fromtimestamp(int(_start_time/1E9))}")
    temp_file.write(content)
    temp_file.close()
    proc = tdb.cli.popen(f"{tdb.config.get('editor')} {temp_file.name}")
    file_updated(temp_file.name, "start", update_cb)
    modtime = os.path.getmtime(temp_file.name)
    try:
        while proc.poll() == None:
            if modtime < os.path.getmtime(temp_file.name):
                time.sleep(0.1)
                modtime = os.path.getmtime(temp_file.name)
                file_updated(temp_file.name, "update", update_cb)
                modtime = os.path.getmtime(temp_file.name)
            time.sleep(0.1)
        
    except KeyboardInterrupt as e:
        print("\nInterrupt detected!")
    
    file_updated(temp_file.name, "end", update_cb)
    text = ""
    if os.path.exists(temp_file.name):
        text = open(temp_file.name).read()
        os.remove(temp_file.name)
    return text

 
def signal_term_handler(signal, frame):
    if _last_text != _start_text:
        tdb.records.add_record(_last_text, _start_time)
    sys.exit(1)
 
signal.signal(signal.SIGTERM, signal_term_handler)
if platform.system() == "Linux": signal.signal(signal.SIGQUIT, signal_term_handler)