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