import tdb.config
try: import markdown
except: pass
import os

_css="""

html {
    font-size: 100%;
    overflow-y: scroll;
    -webkit-text-size-adjust: 100%;
    -ms-text-size-adjust: 100%;
}

body {
  background: #aaa;
}

.container {
  margin: auto;
  width: 80%;
  background: #d0d0d0;
  padding: 10px;
  border-radius: 25px;
  border-right:  1px solid #aaa;
  border-left:   1px solid  #aaa;
  box-shadow: 0 30px 40px rgba(0,0,0,.1);
}

.date {
  color: #aaa;
}

.entry {
  margin: auto;
  width: 80%;
  background: #ddd;
  padding: 20px;
  border-radius: 5px;
  border-bottom: 1px solid #aaa;
  overflow-x: auto;
}
.entry_spacer {
  margin: auto;
  width: 80%;
  padding: 10px;
}

.entry pre,
.entry code {
  background: #d0d0d0;
  font-family: Menlo, Monaco, "Courier New", monospace;
  border-radius: 5px;
}
.entry pre {
  padding: .5rem;
  line-height: 1.25;
  overflow-x: scroll;
}
.entry pre,
.entry blockquote {
  page-break-inside: avoid;
}
.entry blockquote {
  border-left: 3px solid #bbb;
  padding-left: 1rem;
}
.entry a,
.entry a:visited {
  color: #444;
}

.entry a:hover,
.entry a:focus,
.entry a:active {
  color: #111;
}
.entry table,
.entry th,
.entry td {
  border: 1px solid black;
  border-collapse: collapse;
}
.entry thead tr {
  background-color: #ddd;
}
.entry table :is(td, th) {
  padding: 0.3em;
}
.entry tbody tr:nth-child(even) {
  background-color: #ddd;
}
.entry tbody tr:nth-child(odd) {
  background-color: #ccc;
}
"""
_css_file = "/".join((tdb.config._tdb_dir, "tdb.css"))
if not os.path.exists(_css_file): open(_css_file, "w+").write(_css)
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
        try: in_entry["text"] = markdown.markdown(in_entry["text"], extensions=["extra"])
        except: in_entry = "<pre>"+in_entry+"</pre>"
        entries_str += entry.format_map(in_entry)
    print(body.format_map({"css":_css, "css_file":_css_file, "entries":entries_str}))
