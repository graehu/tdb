import os
import time
import tempfile
import tdb.cmd
import tdb.tags
import tdb.config

def start(name, content="", ext=".txt"):
    text = ""
    name += "-"
    temp_file = tempfile.NamedTemporaryFile(mode="w+", prefix=name, suffix=ext, delete=False)
    temp_file.write(content)
    temp_file.close()
    proc = tdb.cmd.popen(f"{tdb.config.get('editor')} {temp_file.name}")
    modtime = os.path.getmtime(temp_file.name)
    while proc.poll() == None:
        if modtime < os.path.getmtime(temp_file.name):
            time.sleep(0.1)
            modtime = os.path.getmtime(temp_file.name)
            cur_text = open(temp_file.name).read()
            cur_text = tdb.tags.parse_cmds(cur_text)
            open(temp_file.name, "w").write(cur_text)
            modtime = os.path.getmtime(temp_file.name)
        time.sleep(0.1)
    
    if os.path.exists(temp_file.name):
        text = open(temp_file.name).read()
        os.remove(temp_file.name)
    return text