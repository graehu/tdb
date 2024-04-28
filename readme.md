# tdb

A text based database with tagging.

```
Usage: py -m tdb [add | edit | rm | show | tui | template | open | listen] [text | options]
----------------------------------------------------------------
Commands:
add:            Make a record when text is supplied. Otherwise, open an editor to write one.
edit:           Open an editor with some view of the database, see options.
rm:             Move matching records to the archive.
show:           Print records to the cmdline, see options below.
tui:            Text ui, very similar to 'less' on linux.
template:       Open an editor to write a record with the passed template file as a basis.
open:           Open tdbs files: tdb open ['archive', 'config', 'db']
listen:         Starts a server listening on passed port.
----------------------------------------------------------------
Options:
span:           The records to select, example: span:7d is the last 7 days.
as:             The format to see the records in. Only valid for show currently. [html, json, list, tags]
@{tag}:         This tag or any others must be included, example: @notes @school, records must have either.
+@{tag}:        This tag and any others must be included. i.e. +@notes +@school, records must have both.
-@{tag}:        This tag must not be included. i.e. -@notes @school, records for school, no notes.
{text}:         This text is optional.
+{text}:        This text must be included.
-{text}:        This text must not be included.

Note, for options text must be quoted if there are spaces.
```
