import shlex
import tdb.tags


def get_addon_name(): return "tdb"

def addon_cmd(context, text, args):
    print(context+" : "+str((get_addon_name(), args)))
    text = tdb.tags.replace_tag(text, (get_addon_name(), args), "")
    try:
        args = shlex.split(args.lower())
    except ValueError as e:
        args = []

    if args:
        if args[0] == "remove":
            tags = tdb.tags.find_tags(text)
            text = remove_tag_cmd(text, args[1:], tags)
        if args[0] == "add":
            print("@tdb: add doesn't work! We'll need access to records here.")
        
    return text


def remove_tag_cmd(text, args, tags):
    for arg in args:
        if arg.startswith("@"):
            arg = arg[1:]
            if arg == "tdb": continue
            rtag = filter(lambda x: x[0] == arg, tags)
            rtag = list(rtag)
            if rtag:
                print(f"@tdb: remove {rtag[0]}")
                text = tdb.tags.replace_tag(text, rtag[0], "")
    return text