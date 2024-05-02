import sys
import os
import tomllib
import tdb.db
import tdb.cli
import tdb.tui
import tdb.tags
import tdb.config
import tdb.records
import tdb.session
import tdb.server
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


def import_addons(printout=False):

    if not tdb.config.get("addons"):
        if printout:
            print(f"No addons found in '{tdb.config.get_filename()}'")
            print("@tdb: commands will not work.")
        return

    for e in tdb.config.get("addons"):
        module = import_addon(e)
        if module:
            mod_vars = vars(module)
            if "get_addon_name" in mod_vars:
                if "addon_tag" in mod_vars:
                    if printout: print(f"Registering '@{module.get_addon_name()}' cmds.")
                    tdb.tags.register_cmd(module.get_addon_name(), module.addon_tag)
                if "addon_record" in mod_vars:
                    tdb.records.register_cmd(module.addon_record)
            elif printout:
                print("failed to add '"+str(e)+"'. missing expected interface 'get_addon_name'.")

def edit(options):
    if options:
        import_addons()
        edit_ext = tdb.config.get('edit_ext')
        edit_ext = edit_ext if edit_ext else ".txt"
        records = tdb.records.split_db_records(options)
        content = "".join([str(r) for r in records])
        update_called = False
        def update_db(previous, text):
            nonlocal content
            nonlocal update_called
            update_called = True
            if not text or text[-1] != "\n": text += "\n"
            old_records = tdb.records.split_records(previous)
            new_records = tdb.records.split_records(text)
            adds, mods, dels = tdb.records.modify_db_records(old_records, new_records)
            if adds or mods or dels: print("".ljust(32, "="))
            if adds: print(f"Inserted {adds} record{'s' if adds > 1 else ''}.")
            if mods: print(f"Modified {mods} record{'s' if mods > 1 else ''}.")
            if dels: print(f"Archived {dels} record{'s' if dels > 1 else ''}.")

            tdb.db.serialise()
            dates = [r.date for r in tdb.records.split_records(text)]
            text = "".join([str(r) for r in tdb.records.split_db_records() if r.date in dates])
            content = text
            return text

        text = tdb.session.start("tdb_"+tdb.cli.get_safe_filename(), content, ext=edit_ext, update_cb=update_db)
        if not update_called:
            print("no changes made")
            return
        elif content != text:
            update_db(content, text) # this should never happen.
    else:
        print("no records selected for edit, see options")
        sys.exit(1)

def main(override=""):
    if len(sys.argv) < 2 or "--help" in sys.argv or sys.argv[1] == "help":
        print("# tdb\n\nA text based database with tagging.\n\n```")
        print("Usage: py -m tdb [add | edit | rm | show | tui | template | open | listen] [text | options]")
        print("".ljust(64,"-"))
        print("Commands:")
        print("add:".ljust(16)+"Make a record when text is supplied. Otherwise, open an editor to write one.")
        print("edit:".ljust(16)+"Open an editor with some view of the database, see options.")
        print("rm:".ljust(16)+"Move matching records to the archive.")
        print("show:".ljust(16)+"Print records to the cmdline, see options below.")
        print("tui:".ljust(16)+"Text ui, very similar to 'less' on linux.")
        print("template:".ljust(16)+"Open an editor to write a record with the passed template file as a basis.")
        print("open:".ljust(16)+"Open tdbs files: tdb open ['archive', 'config', 'db']")
        print("listen:".ljust(16)+"Starts a server listening on passed port.")
        print("".ljust(64,"-"))
        tdb.cli.print_options()
        print("```")
        sys.exit(1)
    if "--version" in sys.argv:
        dir = os.path.dirname(__file__)
        print(tomllib.load(open(dir+"/../pyproject.toml", "rb"))["project"]["version"])
        sys.exit(0)

    command = tdb.cli.get_command(override)
    options = tdb.cli.parse_options(override)
    edit_ext = tdb.config.get('edit_ext')
    edit_ext = edit_ext if edit_ext else ".txt"

    if command == "add":
        text = tdb.cli.get_text()
        import_addons(printout=(text == ""))
        if not text:
            text = tdb.session.start("tdb_add", ext=edit_ext)
        if text:
            tdb.records.add_record(text, tdb.session._start_time)
        else:
            print("No text provided. Record not added.")
            sys.exit(1)

    elif command == "show":
        tdb.records.print_db_records(options)
    
    elif command == "tui":
        tdb.tui.open_tui(options, edit)

    elif command == "open":
        if "config" in sys.argv: tdb.cli.run(f"{tdb.config.get('editor')} {tdb.config.get_filename()}")
        elif "db" in sys.argv: tdb.cli.run(f"{tdb.config.get('editor')} {tdb.db.get_filename()}")
        elif "archive" in sys.argv: tdb.cli.run(f"{tdb.config.get('editor')} {tdb.db.get_archive()}")
        else:
            print("can't open '"+" ".join(sys.argv[2:])+"'.\noptions: 'config', 'db', or 'archive'")
            sys.exit(1)
    
    elif command == "rm":
        if options:
            records = tdb.records.split_db_records(options)
            if records:
                tdb.records.print_records(records, {"as":"list"})
                while True:
                    response = input(f"Archive {len(records)} record{'s' if len(records) > 1 else ''}? (y/n): ").lower()
                    if response in ["yes", "y"]: response = True
                    elif response in ["no", "n"]: response = False
                    if isinstance(response, bool): break
                
                if response and tdb.records.archive_records(records):
                    print(f"Archived {len(records)} record{'s' if len(records) > 1 else ''}.")
                else: print("Nothing archived")


            else:
                print("no records matching options.")
            sys.exit(0)
        
        print("archive requires options e.g. @mytag")
        sys.exit(1)

    elif command == "edit":
        edit(options)

    elif command == "template":
        import_addons()
        template = tdb.cli.get_text()
        if os.path.exists(template):
            basename, ext = os.path.splitext(template)
            basename = os.path.basename(basename)
            if not ext: ext = edit_ext
            content = open(template).read()
            text = tdb.session.start("tdb_"+basename, content, ext)
            if content == text:
                print("no changes made")
                return
            if text and tdb.records.add_record(text, tdb.session._start_time):
                print("Record added successfully!")
            else:
                print("No text provided. Record not added.")
        else:
            print(f"'{template}' is not a valid file")
    elif command == "listen":
        port = 8000
        try:
            port = int(options["ocontains"][0])
            del options["ocontains"][0]
        except Exception as e: pass
        tdb.server.start_server(port, options)
    else:
        print("Invalid command. Try again.")
        sys.exit(1)
        
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--profile":
        del sys.argv[1]
        import cProfile
        cProfile.run("main()")
    else:
        main()