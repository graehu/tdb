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
  background: #aaaaaa;
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


.entry {
  margin: auto;
  width: 80%;
  background: #ddd;
  padding: 10px;
  border-radius: 25px;
  /*border-top:    1px solid  #ff0;*/
  /*border-right:  2px dashed #f0F;*/
  border-bottom: 1px solid #aaa;
  overflow-x: auto;
}
.entry_spacer {
  margin: auto;
  width: 80%;
  padding: 10px;
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
        <h2 class="date">
{date}
        </h2>
        <pre class="content">
{text}
        </pre>
    </div>
    <div class="entry_spacer"></div>
"""

def print_html(entries):
    entries_str = ""
    for in_entry in entries:
        try:in_entry["text"] = markdown.markdown(in_entry["text"])
        except: pass
        entries_str += entry.format_map(in_entry)
    print(body.format_map({"css":_css, "css_file":_css_file, "entries":entries_str}))
