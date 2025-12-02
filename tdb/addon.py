import os
import re
import shlex
import json
import random
import subprocess
import tdb.tags
import tdb.records
import tdb.html
import tdb.config


def get_addon_name(): return "tdb"


def addon_tui(context, text, args):
    return addon_tag(context, text, args)


def addon_tag(context, text, args):
    print(f"tdb:tag {context} : {str((get_addon_name(), args))}")
    try:
        # TODO this used to be args.lower(), make sure removing that didn't break tags.
        split_args = shlex.split(args)
    except ValueError as e:
        split_args = []
    
    if split_args:
        if context in ["tui", "update"]:
            if split_args[0] in ["add", "rm"]: text = tdb.tags.replace_tag(text, (get_addon_name(), args), "") 
            if split_args[0] == "rm": text = remove_tag_cmd(text, split_args[1:])
            elif split_args[0] == "add": text = add_tag_cmd(text, split_args[1:])
            elif split_args[0] == "export": text = export_cmd(text, split_args[1:])
            if  context != "tui" and split_args[0] == "eval": text = eval_cmd(text, args)
            if  context != "tui" and split_args[0] == "python": text = python_cmd(text, args)
            if  context != "tui" and split_args[0] == "cpp": text = cpp_cmd(text, args)
        else:
            if split_args[0] == "random":
                line = f"\n@{get_addon_name()}: random {random.random()}"
                text = tdb.tags.replace_tag(text, (get_addon_name(), args), line)
    else:
        text = tdb.tags.replace_tag(text, (get_addon_name(), args), "")
    return text


def addon_record(context, record):
    # print(f"tdb:record {context} : {str(record)[:-1]}")
    return record


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


def eval_cmd(text, args):
    try:
        args = args.replace("eval", "", 1)
        out = eval(args)
        lines = text.splitlines()
        for line, num in zip(lines, range(0, len(lines))):
            if  line.endswith(args):
                break
        
        if num < len(lines)-1:
            if lines[num+1] != f"eval: {out}":
                lines = lines[:num+1]+[f"eval: {out}"]+lines[1+num:]
        elif num == len(lines)-1:
            lines += [f"eval: {out}"]
        
        text = "\n".join(lines)

        pass
    except Exception as e:
        print(e)
        pass
    return text


def python_cmd(text, args):
    import io
    from contextlib import redirect_stdout
    pattern = re.compile("\`\`\`\s*python\s*(.*?)\s\`\`\`", re.DOTALL | re.IGNORECASE)
    blocks = [block.strip() for block in pattern.findall(text)]
    for block in blocks:
        text = text.replace(block, "MDPYTHON_REPLACEMENT_STRING")
        block = "\n".join([b for b in block.splitlines() if not b.startswith("#tdb:")])
        text = text.replace("MDPYTHON_REPLACEMENT_STRING", block)
        output = ""
        f = io.StringIO()
        with redirect_stdout(f):
            try: exec(block, {}, {})
            except Exception as e:
                print(e)
            output = f.getvalue()
        if output:
            output = "#tdb: "+"\n#tdb: ".join(output.splitlines())
            text = text.replace(block, block+"\n"+output)
    return text


def cpp_cmd(text, args):
    pattern = re.compile("\`\`\`\s*c\+\+\s*(.*?)\s\`\`\`", re.DOTALL | re.IGNORECASE)
    blocks = [block.strip() for block in pattern.findall(text)]
    for block in blocks:
        text = text.replace(block, "MDC++_REPLACEMENT_STRING")
        block = "\n".join([b for b in block.splitlines() if not b.startswith("//tdb:")])
        text = text.replace("MDC++_REPLACEMENT_STRING", block)
        outdir = tdb.config.get_tdb_dir()
        compile_cmd = tdb.config.get("cpp_compile_cmd", "g++ -o")
        compile_cmd = f"{compile_cmd} {outdir}/tdb_temp.bin {outdir}/tdb_temp.cpp"
        output = ""
        with open(f"{outdir}/tdb_temp.cpp", 'w') as source: source.write(block)
        try:
            res = subprocess.run(compile_cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode == 0:
                res = subprocess.run(f"{outdir}/tdb_temp.bin", shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output += res.stdout+res.stderr
            else:
                output += f"failed: '{compile_cmd}'\n"
                output += res.stdout+res.stderr
        except Exception as e: output = str(e)
        
        if output:
            output = "//tdb: "+"\n//tdb: ".join(output.splitlines())
            output = output.strip()
            text = text.replace(block, block+"\n"+output)
    try:
        os.remove(f"{outdir}/tdb_temp.cpp")
        os.remove(f"{outdir}/tdb_temp.bin")
    except Exception as e: pass
    return text


def export_cmd(text, args):
    path : str = args[0]
    out = "\n".join([l for l in text.splitlines() if not l.startswith("@tdb")])
    with open(path, "w+") as file:
        if path.endswith(".html"):
            #TODO this will allow multiple records with the same path to export together.
            #     however, this code runs for each export line, which is not performant.
            #     need a way to dedupe tag commands in some cases.
            records = [r for r in tdb.records.split_records(text) if path in r.text]
            for r in records: r.text = "\n".join([l for l in r.text.splitlines() if not l.startswith("@tdb")])
            tdb.html.print_html(reversed([r for r in records]), file)
        elif path.endswith(".json"):
            records = [r for r in tdb.records.split_records(text) if path in r.text]
            for r in records: r.text = "\n".join([l for l in r.text.splitlines() if not l.startswith("@tdb")])
            res = [r.asdict() for r in records]
            print(json.dumps(res, indent=2), file=file)
        elif path.endswith(".short"):
            out = "".join([str(r).splitlines()[0]+"\n" for r in records])
            print(out.strip(), file=file)
        else:
            file.write(out)
    return text
