import sys
import os
import tempfile
import tdb.tags
import tdb.records
import tdb.config
import tdb.cmd
import tdb.db

def main():
    if len(sys.argv) < 2:
        print("Usage: py -m tdb [add|show|config|open|template] [text|options]")
        sys.exit(1)

    command = tdb.cmd.get_command()
    options = tdb.cmd.parse_options()

    if command == "add":
        text = tdb.cmd.get_text()
        if not text:
            temp = tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False)
            temp.close()
            tdb.cmd.run(f"{tdb.config.get('editor')} {temp.name}")
            
            if os.path.exists(temp.name):
                text = open(temp.name).read()
                os.remove(temp.name)

        if text:
            tdb.records.add_record(text)
        else:
            print("No text provided. Record not added.")

    elif command == "show":
        tdb.records.print_records(options)

    elif command == "config":
        tdb.cmd.run(f"{tdb.config.get('editor')} {tdb.config.get_filename()}")

    elif command == "open":
        tdb.cmd.run(f"{tdb.config.get('editor')} {tdb.db.get_filename()}")

    elif command == "template":
        template = tdb.cmd.get_text()
        if os.path.exists(template):
            ext = os.path.splitext(template)[1]
            if not ext: ext = "_tdb.txt"
            else: ext = "_tdb"+ext
            temp = tempfile.NamedTemporaryFile(mode="w+", suffix=ext, delete=False)
            temp_text = open(template).read() 
            temp.write(temp_text)
            temp.close()
            tdb.cmd.run(f"{tdb.config.get('editor')} {temp.name}")
            
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