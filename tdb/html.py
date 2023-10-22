import tdb.config
try: import markdown
except: pass
import os
import shutil

_css_file = "/".join((tdb.config._tdb_dir, "style.css"))

if not os.path.exists(_css_file): _css_file = "/".join((os.path.dirname(__file__), "style.css"))

_css = open(_css_file, "r").read()

body = """<html>

      <header>
        <style>
/*inserted from {css_file}*/
{css}
        </style>
    </header>
    <body>
    <div class="entry_spacer"></div>
    <div id="container" class="container">
        <div class="entry_spacer"></div>
{entries}
    </div>
    </body>
</html>
"""
entry = """
    <div class="entry">
        <div class="date">
{date}
        </div>
        <div class="content">
{text}
        </div>
    </div>
    <div class="entry_spacer"></div>
"""

def print_html(entries):
    entries_str = ""
    for in_entry in entries:
        try: in_entry["text"] = markdown.markdown(in_entry["text"], extensions=["extra", "codehilite"])
        except: in_entry = "<pre>"+in_entry+"</pre>"
        entries_str += entry.format_map(in_entry)
    print(body.format_map({"css":_css, "css_file":_css_file, "entries":entries_str}))
