import sys
import os
import json
import tempfile
import subprocess
import tdb.tags
import tdb.records
import tdb.config
import tdb.rake

# Set the name of the database file.
db_path = os.path.dirname(__file__)
db_path = os.path.join(db_path, "..", "db.txt")
db_path = os.path.abspath(db_path)

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
            tdb.records.add_record(db_path, text)
        else:
            print("No text provided. Record not added.")

    elif command == "display":
        # Display all records in the database.
        tdb.records.print_records(db_path)

    elif command == "tags":
        with open(db_path) as fd:
            records = tdb.records.split_records(fd.read())
            results = []
            for k, v in records.items():
                results.append({"date": k.isoformat(" "), "text": v, "tags": tdb.tags.find_tags(v)})
            print(json.dumps(results, indent=2))

    elif command == "find":
        
        if not os.path.exists(db_path):
            print("no entries in the db")
            sys.exit(1)

        kw_ext = tdb.rake.Rake()

        if sys.stdin.isatty():
            text = " ".join(sys.argv[2:]).strip()
        else:
            text = sys.stdin.read()
        
        text_kw = kw_ext.run(text)

        with open(db_path) as fd:
            records = tdb.records.split_records(fd.read())
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

    else:
        print("Invalid command. Try again.")
        sys.exit(1)
    

if __name__ == "__main__":
    main()