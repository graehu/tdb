import shlex
import json
import tdb.tags
import tdb.records
import tdb.html

def get_addon_name(): return "tdb"

def addon_tag(context, text, args):
    print(context+" : "+str((get_addon_name(), args)))
    try:
        # TODO this used to be args.lower(), make sure removing that didn't break tags.
        split_args = shlex.split(args)
    except ValueError as e:
        split_args = []
    
    if split_args:
        if split_args[0] in ["add", "remove"]: text = tdb.tags.replace_tag(text, (get_addon_name(), args), "") 
        if split_args[0] == "remove": text = remove_tag_cmd(text, split_args[1:])
        elif split_args[0] == "add": text = add_tag_cmd(text, split_args[1:])
        elif split_args[0] == "export": text = export_cmd(text, split_args[1:])
    else:
        text = tdb.tags.replace_tag(text, (get_addon_name(), args), "")
    return text

def addon_record(text):
    pass

def add_tag_cmd(text, args):
    records = tdb.records.split_records(text)
    for r in records:
        for arg in args:
            if arg.startswith("@"):
                if not tdb.tags.contains_tag(r.text, arg[1:]):
                    lines = r.text.splitlines()
                    best = -1
                    for index in range(len(lines)-1, 0, -1):
                        if ":" not in lines[index] and lines[index].startswith("@"):
                            best = index
                            break

                    if best != -1:
                        if lines[best] and lines[best][-1] != " ": lines[best] += " "
                        lines[best] += arg
                        r.text = "\n".join(lines)+"\n"
                    else:
                        if len(lines[-1]) > 0: r.text += "\n"
                        r.text += "\n" + arg + "\n\n"

    return "".join([str(r) for r in records])


def remove_tag_cmd(text, args):
    tags = tdb.tags.find_tags(text)
    tags = filter(lambda x: "@"+x[0] in args, tags)
    for tag in tags:
        text = tdb.tags.replace_tag(text, tag, "")
    records = tdb.records.split_records(text)
    for r in records:
        r.text = r.text.rstrip() + "\n"

    return "".join([str(r) for r in records])


def export_cmd(text, args):
    path : str = args[0]
    out = "\n".join([l for l in text.splitlines() if not l.startswith("@tdb")])
    with open(path, "w+") as file:
        if path.endswith(".html"):
            records = tdb.records.split_records(out)
            tdb.html.print_html(reversed([r.asdict() for r in records]), file)
        elif path.endswith(".json"):
            records = tdb.records.split_records(out)
            res = [r.asdict() for r in records]
            print(json.dumps(res, indent=2), file=file)
        elif path.endswith(".short"):
            out = "".join([str(r).splitlines()[0]+"\n" for r in records])
            print(out.strip(), file=file)
        else:
            file.write(out)
    return text