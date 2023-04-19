import sys
import os
import tdb.tags
import tdb.records
import tdb.session
import tdb.config
import tdb.cli
import tdb.db

import importlib.util

_dirname = os.path.dirname(__file__)
_dirname = _dirname.replace("\\", "/")

def import_addon(file_path):
    basename = os.path.basename(file_path)
    if file_path == basename:
        file_path = "/".join((_dirname, file_path))
    if os.path.exists(file_path):
        basename, _ = os.path.splitext(basename)
        spec = importlib.util.spec_from_file_location("tdb.addon."+basename, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    return None


def import_addons():

    if not tdb.config.get("addons"):
        print(f"No addons found in '{tdb.config.get_filename()}'")
        print("@tdb: commands will not work.")
        return

    for e in tdb.config.get("addons"):
        module = import_addon(e)
        if module:
            mod_vars = vars(module)
            if "get_addon_name" in mod_vars and "addon_cmd" in mod_vars:
                tdb.tags.register_cmd(module.get_addon_name(), module.addon_cmd)
            else:
                print("failed to add '"+str(e)+"'. missing expected interface 'get_addon_name' and 'addon_cmd'.")


def main():
    if len(sys.argv) < 2:
        print("Usage: py -m tdb [add | show | config | edit | template] [text | options]")
        sys.exit(1)
    
    command = tdb.cli.get_command()
    options = tdb.cli.parse_options()

    if command == "add":
        import_addons()
        text = tdb.cli.get_text()
        if not text:
            text = tdb.session.start("tdb_add")
        if text:
            tdb.records.add_record(text)
        else:
            print("No text provided. Record not added.")

    elif command == "show":
        tdb.records.print_records(options)

    elif command == "config":
        tdb.cli.run(f"{tdb.config.get('editor')} {tdb.config.get_filename()}")

    elif command == "edit":
        import_addons()
        if any(options.values()):
            records = tdb.records.split_db_records(options)
            content = "".join([str(r) for r in records])
            text = tdb.session.start("tdb_edit", content)
            if content == text:
                print("no changes made")
                return
            else:
                tdb.records.modify_records(records, text)
        else:
            tdb.cli.run(f"{tdb.config.get('editor')} {tdb.db.get_filename()}")

    elif command == "template":
        import_addons()
        template = tdb.cli.get_text()
        if os.path.exists(template):
            basename, ext = os.path.splitext(template)
            basename = os.path.basename(basename)
            if not ext: ext = ".txt"
            content = open(template).read()
            text = tdb.session.start("tdb_edit", content, ext)
            
            if content == text:
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