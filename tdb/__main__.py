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
        print("Usage: py -m tdb [add | show | config | edit | template] [text | options]")
        sys.exit(1)
    
    command = tdb.cmd.get_command()
    options = tdb.cmd.parse_options()

    if command == "add":
        text = tdb.cmd.get_text()
        if not text:
            
            temp = tempfile.NamedTemporaryFile(mode="w+", prefix="tdb_add_", suffix=".txt", delete=False)
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

    elif command == "edit":
        if any(options.values()):
            records = tdb.records.split_db_records(options)
            records_text = "".join([str(r) for r in records])
            temp = tempfile.NamedTemporaryFile(mode="w+", prefix="tdb_edit_", suffix=".txt", delete=False)
            temp.write(records_text)
            temp.close()
            tdb.cmd.run(f"{tdb.config.get('editor')} {temp.name}")
            
            if os.path.exists(temp.name):
                text = open(temp.name).read()
                os.remove(temp.name)
                if tdb.rake.similarity_score(records_text, text) == 1.0:
                    print("no changes made")
                    return
                else:
                    tdb.records.modify_records(records, text)
        else:
            tdb.cmd.run(f"{tdb.config.get('editor')} {tdb.db.get_filename()}")

    elif command == "template":
        template = tdb.cmd.get_text()
        if os.path.exists(template):
            basename, ext = os.path.splitext(template)
            basename = os.path.basename(basename)
            if not ext: ext = ".txt"
            temp = tempfile.NamedTemporaryFile(mode="w+", prefix=f"{basename}_", suffix=ext, delete=False)
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