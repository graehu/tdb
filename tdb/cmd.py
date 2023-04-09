import sys
import subprocess


def get_text():
    if sys.stdin.isatty():
        text = " ".join(sys.argv[2:]).strip()
    else:
        text = sys.stdin.read()
    return text


def get_command():
    return sys.argv[1]


def parse_options():
    splits = sys.argv[2:]
    contains = []
    ranges = []
    tags = []
    for split in splits:
        if split.startswith("-r="):
            split = split[len("-r="):]
            split = split.split(",",maxsplit=2)
            ranges.append(parse_range(split))

        elif split.startswith("-c="):
            split = split[len("-r="):]
            contains.append(split)

        elif split.startswith("@"):
            tags.append(split[1:])
    return {"tags":tags, "ranges":ranges, "contains":contains}


def parse_range(args):
    from datetime import datetime, timedelta
    import re
    now = datetime.now()
    operations = []
    
    for select in args:
        select = select.strip()
        try:
            select = datetime.fromisoformat(select)
            operations.append(select)
        except ValueError:
            units = [re.search("(-?\d+)"+u, select, re.IGNORECASE) for u in ["y","w","d","h","m","s"]]
            units = [int(u.group(1)) if u else 0 for u in units]
            days = units[0]*365+units[1]*7+units[2]
            seconds = units[3]*(60*60)+units[4]*60+units[5]

            if days or seconds:
                if operations:
                    operations.append(operations[0]+timedelta(days=days, seconds=seconds))
                else:
                    operations.append(now+timedelta(days=days, seconds=seconds))
            else:
                try:
                    num = int(select)
                    operations.append(num)
                except ValueError:
                    print("bad record range format: "+select)
                    pass

    if len(operations) == 1: operations.append(now)
    
    return operations


def run(text):
    subprocess.run(text, shell=True)

    
if __name__ == "__main__":
    command, splits = sys.argv[1], sys.argv[2:]
    print(command)
    

