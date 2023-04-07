import sys
import os
import json
import tempfile
import subprocess
import tdb.tags
import tdb.records
import tdb.config
import tdb.rake
import tdb.db

def main():
    if len(sys.argv) < 2:
        print("Usage: py -m tdb [add|display|tags|find]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "add":
        if sys.stdin.isatty():
            text = " ".join(sys.argv[2:]).strip()
        else:
            text = sys.stdin.read()
        
        if not text:
            temp = tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False)
            temp.close()
            subprocess.run(f"{tdb.config.get('editor')} {temp.name}", shell=True)
            
            if os.path.exists(temp.name):
                text = open(temp.name).read()
                os.remove(temp.name)

        if text:
            tdb.records.add_record(text)
        else:
            print("No text provided. Record not added.")

    elif command == "display":
        tdb.records.print_records()

    elif command == "tags":
        tdb.tags.print_tags()
            

    elif command == "find":

        kw_ext = tdb.rake.Rake()

        if sys.stdin.isatty():
            text = " ".join(sys.argv[2:]).strip()
        else:
            text = sys.stdin.read()
        
        text_kw = kw_ext.run(text)

        records = tdb.records.split_records(tdb.db.get_text())
        results = []
        for k, v in records.items():
            record_kw = kw_ext.run(v)
            result = {"date":k.isoformat(" "), "text":v, "score":0}
            for k1, v1 in record_kw:
                for k2, v2 in text_kw:
                    if tdb.rake.similarity_score(k1, k2) > 0.8:
                        result["score"] += (v1+v2)*0.5
            
            if result["score"] > 0:
                results.append(result)

        results = sorted(results, key=lambda result: result["score"], reverse=True)
        print(json.dumps(results, indent=2))

    elif command == "config":
        tdb.db._skip_shutdown = True
        subprocess.run(f"{tdb.config.get('editor')} {tdb.config.get_filename()}", shell=True)

    elif command == "open":
        tdb.db._skip_shutdown = True
        subprocess.run(f"{tdb.config.get('editor')} {tdb.db.get_filename()}", shell=True)

    elif command == "template":
        template = ""
        if sys.stdin.isatty():
            template = " ".join(sys.argv[2:]).strip()
        else:
            template = sys.stdin.read().strip()
        if os.path.exists(template):
            temp = tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False)
            temp_text = open(template).read() 
            temp.write(temp_text)
            temp.close()
            subprocess.run(f"{tdb.config.get('editor')} {temp.name}", shell=True)
            
            if os.path.exists(temp.name):
                text = open(temp.name).read()
                os.remove(temp.name)
                if tdb.rake.similarity_score(temp_text, text) == 1.0:
                    print("no changes made")
                    return

                if text:
                    tdb.records.add_record(text)
                else:
                    print("No text provided. Record not added.")
        else:
            print(f"'{template}' is not a valid file")

    else:
        print("Invalid command. Try again.")
        sys.exit(1)
    

if __name__ == "__main__":
    main()