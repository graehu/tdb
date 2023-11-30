import tdb.config
import sys
try: import markdown
except: pass
try: import md_mermaid
except: pass
import os

_css_file = "/".join((tdb.config._tdb_dir, "style.css"))
_mermaid_js_file = "/".join((tdb.config._tdb_dir, "mermaid.min.js"))
_mermaid_css_file = "/".join((tdb.config._tdb_dir, "mermaid.css"))

if not os.path.exists(_css_file): _css_file = "/".join((os.path.dirname(__file__), "style.css"))
if not os.path.exists(_mermaid_js_file): _mermaid_js_file = None
if not os.path.exists(_mermaid_css_file): _mermaid_css_file = None

search = """
<div class="entry_spacer"></div>
<div class="entry" id="input_entry">
    <input type="text" class="input" placeholder="search"></input>
</div>
"""

body = """<html>
      <header>
         <script src="tdb/html.js"></script>
        {mermaid}
        {css}
    </header>
    <body>
    <div class="entry_spacer"></div>
    <div class="container">
        {search}
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

def build_html(entries, server=False):
    entries_str = build_html_entries(entries)
    if server:
        _css = "<link rel=\"stylesheet\" href=\"tdb/style.css\">\n"
        _mermaid = ""
        if _mermaid_js_file:
            _mermaid = "<script src=\"tdb/mermaid.min.js\"></script>\n"
            _mermaid = _mermaid+"<script>mermaid.initialize({startOnLoad:true});</script>\n"
            _mermaid = _mermaid+"<link rel=\"stylesheet\" href=\"tdb/mermaid.css\">\n" if _mermaid_css_file else ""
        return body.format_map({"css":_css, "mermaid":_mermaid, "entries":entries_str, "search":search})
    else:
        _css = "<style>\n"+open(_css_file).read()+"\n</style>\n"
        _mermaid = ""
        if _mermaid_js_file and _mermaid_css_file:
            _mermaid = "<script>\n"+open(_mermaid_js_file).read()+"\n</script>\n"
            _mermaid = _mermaid+"<script>mermaid.initialize({startOnLoad:true});</script>\n"
            _mermaid = _mermaid+"<style>\n"+open(_mermaid_css_file).read()+"\n</style>\n"
        return body.format_map({"css":_css, "mermaid":_mermaid, "entries":entries_str, "search":""})


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
