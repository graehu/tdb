import tdb.config
import sys
try: import markdown
except: pass
try: import md_mermaid
except: pass
import os

_css_file = "/".join((tdb.config._tdb_dir, "style.css"))

if not os.path.exists(_css_file): _css_file = "/".join((os.path.dirname(__file__), "style.css"))

_css = open(_css_file, "r").read()

body = """<html>
      <header>
         <script src="mermaid.min.js"></script>
         <script src="tdb/html.js"></script>
        <style>
/*inserted from {css_file}*/
{css}
        </style>
    </header>
    <body>
    <div class="entry_spacer"></div>
    <div class="container">
        <input type="text" class="input"></input>
        <div class="entry_spacer"></div>
        <div id="container">
{entries}
        </div>
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

def build_html(entries):
    entries_str = build_html_entries(entries)
    return body.format_map({"css":_css, "css_file":_css_file, "entries":entries_str})


def build_html_entries(entries):
    entries_str = ""
    for in_entry in entries:
        if "markdown" in sys.modules:
            extensions = ["extra", "codehilite"]
            if "md_mermaid" in sys.modules: extensions.append("md_mermaid")
            try: in_entry["text"] = markdown.markdown(in_entry["text"], extensions=extensions)
            except: in_entry["text"] = markdown.markdown(in_entry["text"], extensions=["extra", "codehilite"])
        else:
            in_entry["text"] = "<pre>"+in_entry["text"]+"</pre>"
        entries_str += entry.format_map(in_entry)
    return entries_str


def print_html(entries, file=None):
    print(build_html(entries), file=file)
