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

__addons_imported = False
def import_addons(printout=False):
    global __addons_imported
    if __addons_imported: return
    __addons_imported = True
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
                if "addon_tui" in mod_vars:
                    tdb.tui.register_cmd(module.get_addon_name(), module.addon_tui)
                if "addon_record" in mod_vars:
                    tdb.records.register_cmd(module.addon_record)
            elif printout:
                print("failed to add '"+str(e)+"'. missing expected interface 'get_addon_name'.")


def edit(options, can_exit=True):
    if options:
        import_addons()
        edit_ext = tdb.config.get('edit_ext')
        edit_ext = edit_ext if edit_ext else ".txt"
        records = tdb.records.split_db_records(options)
        md_options = tdb.cli.parse_options("simple")
        md_options["md"] = options["md"]
        content = "".join([r.md() for r in records])
        update_called = False
        # TODO: this previous isn't needed now.
        def update_db(previous, text):
            nonlocal content
            nonlocal update_called
            nonlocal records
            update_called = True
            if not text or text[-1] != "\n": text += "\n"
            
            new_records = tdb.records.split_records(text)
            
            if md_options["md"]:
                new_records = tdb.records.filter_records(new_records, md_options)
                for r1 in records:
                    for r2 in new_records:
                        if r1.is_samedate(r2):
                            mds = zip(r1.md_text, r2.md_text)
                            r2.text = r1.text
                            for m1, m2 in mds: r2.text = r2.text.replace(m1, m2)
                            r2.text_hash = hash(r2.text)
                            break
                
            adds, mods, dels = tdb.records.modify_db_records(records, new_records)
            if adds or mods or dels: print("".ljust(32, "="))
            if adds: print(f"Inserted {adds} record{'s' if adds > 1 else ''}.")
            if mods: print(f"Modified {mods} record{'s' if mods > 1 else ''}.")
            if dels: print(f"Archived {dels} record{'s' if dels > 1 else ''}.")

            tdb.db.serialise()
            dates = [r.date for r in tdb.records.split_records(text)]
            records = [r for r in tdb.records.split_db_records(md_options) if r.date in dates]
            text = "".join([r.md() for r in records])
            content = text
            return text

        text = tdb.session.start("tdb_"+tdb.cli.get_safe_filename(), content, ext=edit_ext, update_cb=update_db)
        if not update_called:
            print("no changes made")
            return
        elif content != text:
            update_db(content, text) # this should never happen.
    elif can_exit:
        print("no records selected for edit, see options")
        sys.exit(1)

def rm(options, can_exit=True):
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
        if can_exit: sys.exit(0)

    print("archive requires options e.g. @mytag")
    if can_exit: sys.exit(1)


def main(override=""):
    if len(sys.argv) < 2 or "--help" in sys.argv or sys.argv[1] == "help":
        print("# tdb\n\nA text based database with tagging.\n\n```")
        print("Usage: py -m tdb [add | edit | record | rm | show | tui | template | open | listen] [text | options]")
        print("".ljust(64,"-"))
        print("Commands:")
        print("add:".ljust(16)+"Make a record when text is supplied. Otherwise, open an editor to write one.")
        print("edit:".ljust(16)+"Open an editor with some view of the database, see options.")
        print("record:".ljust(16)+"Make a record when text is supplied, immediately open it for edit.")
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
    elif command == "record":
        text = tdb.cli.get_text()
        if text:
            import datetime
            ms = tdb.records.add_record(text, tdb.session._start_time)
            out = datetime.datetime.fromtimestamp(ms/1E6)
            override = tdb.cli.parse_options("")
            override["dates"].append(out)
            edit(override)
        else:
            print("No text provided. Record not added.")
            sys.exit(1)
            pass
    elif command == "show":
        tdb.records.print_db_records(options)
    
    elif command == "tui":
        import_addons()
        tdb.tui.open_tui(options, edit, rm)

    elif command == "open":
        if "config" in sys.argv: tdb.cli.run(f"{tdb.config.get('editor')} {tdb.config.get_filename()}")
        elif "db" in sys.argv: tdb.cli.run(f"{tdb.config.get('editor')} {tdb.db.get_filename()}")
        elif "archive" in sys.argv: tdb.cli.run(f"{tdb.config.get('editor')} {tdb.db.get_archive()}")
        else:
            print("can't open '"+" ".join(sys.argv[2:])+"'.\noptions: 'config', 'db', or 'archive'")
            sys.exit(1)
    
    elif command == "rm":
        rm(options)
        # if options:
        #     records = tdb.records.split_db_records(options)
        #     if records:
        #         tdb.records.print_records(records, {"as":"list"})
        #         while True:
        #             response = input(f"Archive {len(records)} record{'s' if len(records) > 1 else ''}? (y/n): ").lower()
        #             if response in ["yes", "y"]: response = True
        #             elif response in ["no", "n"]: response = False
        #             if isinstance(response, bool): break
                
        #         if response and tdb.records.archive_records(records):
        #             print(f"Archived {len(records)} record{'s' if len(records) > 1 else ''}.")
        #         else: print("Nothing archived")


        #     else:
        #         print("no records matching options.")
        #     sys.exit(0)
        
        # print("archive requires options e.g. @mytag")
        # sys.exit(1)

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
    elif len(sys.argv) > 1 and sys.argv[1] == "--timed": 
        import time
        import datetime
        del sys.argv[1]
        start = time.time()
        main()
        print(f"time: {datetime.timedelta(seconds=time.time()-start)}")     
    else:
        main()
