css="""
html {
    font-size: 100%;
    overflow-y: scroll;
    -webkit-text-size-adjust: 100%;
    -ms-text-size-adjust: 100%;
}

body {
  background: #cccccc;
}

.title {
  text-align: center;
}

.container {
  margin: auto;
  width: 80%;
  background: #d0d0d0;
  padding: 10px;
  border-radius: 25px;
  border-right:  1px solid #000;
  border-left:   1px solid  #000;
}

.entry {
  margin: auto;
  width: 80%;
  background: #ddd;
  padding: 10px;
  border-radius: 25px;
  /*border-top:    1px solid  #ff0;*/
  /*border-right:  2px dashed #f0F;*/
  border-bottom: 1px solid #333;
}
"""

body = """<html>

      <header>
        <style>
{css}
        </style>
    </header>
    <body>
    <div id="container" class="container">
        <h1 class="title">./tdb.py</h1>
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
        <p class="content">
{text}
        </br>
        </p>
    </div>
"""

def print_html(entries):
    entries_str = ""
    for in_entry in entries:
        entries_str += entry.format_map(in_entry)
    print(body.format_map({"css":css, "entries":entries_str}))
