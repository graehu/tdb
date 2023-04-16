import os
import time
import shlex
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
            tags = tdb.tags.find_tags(cur_text)
            for tag in tags:
                if tag[0] == "tdb" and tag[1]:
                    cur_text = tdb.tags.replace_tag(cur_text, tag, "")
                    args = shlex.split(tag[1].lower())
                    if args[0] == "remove":
                        for arg in args[1:]:
                            if arg.startswith("@"):
                                arg = arg[1:]
                                if arg == "tdb": continue
                                rtag = filter(lambda x: x[0] == arg, tags)
                                rtag = list(rtag)
                                if rtag:
                                    cur_text = tdb.tags.replace_tag(cur_text, rtag[0], "")
            open(temp_file.name, "w").write(cur_text)
            modtime = os.path.getmtime(temp_file.name)
        time.sleep(0.1)
    
    if os.path.exists(temp_file.name):
        text = open(temp_file.name).read()
        os.remove(temp_file.name)
    return text