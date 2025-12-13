import tdb.config
import tdb.tags
import sys
import os
import re
try: import markdown
except: pass

_css_file = "/".join((tdb.config.get_tdb_dir(), "style.css"))
_mermaid_js_file = "/".join((tdb.config.get_tdb_dir(), "mermaid.min.js"))
_mermaid_css_file = "/".join((tdb.config.get_tdb_dir(), "mermaid.css"))

if not os.path.exists(_css_file): _css_file = "/".join((os.path.dirname(__file__), "style.css"))
if not os.path.exists(_mermaid_js_file): _mermaid_js_file = None
if not os.path.exists(_mermaid_css_file): _mermaid_css_file = None

search = """
<div class="entry_spacer"></div>
<div class="entry" id="input_entry">
    <input type="text" class="input" placeholder="search"></input>
</div>
"""

body = """<!DOCTYPE html>
<html>
      <head>
        <meta charset="UTF-8">
        <script src="tdb/html.js"></script>
        {mermaid}
        {css}
    </head>
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
    <div class="entry_spacer">
    <div class="entry">
        <div class="content">
{text}
        </div>
        <div class="date">
{date}
        </div>
    </div>
    </div>
"""

def preprocess_mermaid(text):
    re_mermaid = re.compile(r"^`{3}\s*mermaid\s*$", re.IGNORECASE)
    lines = text.splitlines()
    out_lines = []
    m_start = None
    m_end = None
    in_mermaid_code = False
    for line in lines:
        if not in_mermaid_code:
            m_start = re_mermaid.match(line)
        else:
            m_end = line.startswith("```")
            if m_end: in_mermaid_code = False
        if m_start:
            in_mermaid_code = True
            out_lines.append('<div class="mermaid">')
            m_start = None
        elif m_end:
            out_lines.append('</div>')
            m_end = None
        elif in_mermaid_code: out_lines.append(line.strip())
        else: out_lines.append(line)
    return "\n".join(out_lines)


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
        text = in_entry.text if not in_entry.md_text else in_entry.md_text
        # note: this is really inefficient :)
        for tag in tdb.tags._config:
            colour = tdb.tags.get_colour(tag)
            text = tdb.tags.replace_tag(text, (tag,""), f"<div style='font-style: bold; color: {colour};'>@{tag}</div>")
            
        if "markdown" in sys.modules:
            text = preprocess_mermaid(text)
            text = markdown.markdown(text, extensions=["extra", "codehilite"])
        else:
            text = "<pre>"+text+"</pre>"
        entries_str += entry.format(text=text, date=in_entry.date)
    return entries_str


def print_html(entries, file=None):
    print(build_html(entries), file=file)
