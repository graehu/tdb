import shlex
import tdb.tags
import tdb.records


def get_addon_name(): return "tdb"

def addon_cmd(context, text, args):
    print(context+" : "+str((get_addon_name(), args)))
    text = tdb.tags.replace_tag(text, (get_addon_name(), args), "")
    try:
        args = shlex.split(args.lower())
    except ValueError as e:
        args = []

    if args:
        if args[0] == "remove": text = remove_tag_cmd(text, args[1:])
        elif args[0] == "add": text = add_tag_cmd(text, args[1:])
    return text


def add_tag_cmd(text, args):
    records = tdb.records.split_records(text)
    for r in records:
        for arg in args:
            if arg.startswith("@"):
                if not tdb.tags.contains_tag(r.text, arg[1:]):
                    if r.text[-1] != "\n": r.text += "\n"
                    r.text += arg+"\n"

    return "".join([str(r) for r in records])


def remove_tag_cmd(text, args):
    tags = tdb.tags.find_tags(text)
    tags = filter(lambda x: "@"+x[0] in args, tags)
    for tag in tags:
        text = tdb.tags.replace_tag(text, tag, "")
    return text