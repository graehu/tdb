import sys
import os
import tomllib
import tdb.db
import tdb.cli
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


def import_addons():

    if not tdb.config.get("addons"):
        print(f"No addons found in '{tdb.config.get_filename()}'")
        print("@tdb: commands will not work.")
        return

    for e in tdb.config.get("addons"):
        module = import_addon(e)
        if module:
            mod_vars = vars(module)
            if "get_addon_name" in mod_vars:
                if "addon_tag" in mod_vars:
                    tdb.tags.register_cmd(module.get_addon_name(), module.addon_tag)
                if "addon_record" in mod_vars:
                    tdb.records.register_cmd(module.addon_record)
            else:
                print("failed to add '"+str(e)+"'. missing expected interface 'get_addon_name'.")


def main():
    if len(sys.argv) < 2 or "--help" in sys.argv:
        print("# tdb\n\nA text based database with tagging.\n\n```")
        print("Usage: py -m tdb [add | edit | template | show | config | archive | listen] [text | options]")
        print("".ljust(64,"-"))
        print("Commands:")
        print("add:".ljust(16)+"Make a record when text is supplied. Otherwise, open an editor to write one.")
        print("edit:".ljust(16)+"Open an editor with some view of the database, see options.")
        print("template:".ljust(16)+"Open an editor to write a record with the passed template file as a basis.")
        print("config:".ljust(16)+"Open tdbs config file.")
        print("archive:".ljust(16)+"Open tdbs archive. Check here if you lose a record.")
        print("listen:".ljust(16)+"Starts a server listening on passed port.")
        print("".ljust(64,"-"))
        tdb.cli.print_options()
        print("```")
        sys.exit(0)
    if "--version" in sys.argv:
        dir = os.path.dirname(__file__)
        print(tomllib.load(open(dir+"/../pyproject.toml", "rb"))["project"]["version"])
        sys.exit(0)
    command = tdb.cli.get_command()
    options = tdb.cli.parse_options()
    edit_ext = tdb.config.get('edit_ext')
    edit_ext = edit_ext if edit_ext else ".txt"
    if command == "add":
        import_addons()
        text = tdb.cli.get_text()
        if not text:
            text = tdb.session.start("tdb_add", ext=edit_ext)
        if text:
            tdb.records.add_record(text)
        else:
            print("No text provided. Record not added.")

    elif command == "show":
        tdb.records.print_records(options)

    elif command == "config":
        tdb.cli.run(f"{tdb.config.get('editor')} {tdb.config.get_filename()}")

    elif command == "archive":
            tdb.cli.run(f"{tdb.config.get('editor')} {tdb.db.get_archive()}")
            
    elif command == "edit":
        import_addons()
        if any(options.values()):
            records = tdb.records.split_db_records(options)
            content = "".join([str(r) for r in records])
            update_called = False
            def update_db(previous, text):
                nonlocal content
                nonlocal update_called
                update_called = True
                if not text or text[-1] != "\n": text += "\n"
                tdb.records.modify_db_records(previous, text)
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
            tdb.cli.run(f"{tdb.config.get('editor')} {tdb.db.get_filename()}")

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
            if text:
                tdb.records.add_record(text)
            else:
                print("No text provided. Record not added.")
        else:
            print(f"'{template}' is not a valid file")
    elif command == "listen":
        port = 8000
        try: port = int(options["ocontains"][0])
        except Exception as e: pass 
        tdb.server.start_server(port)
    else:
        print("Invalid command. Try again.")
        sys.exit(1)
        
_profile = False
if __name__ == "__main__":
    if _profile:
        import cProfile
        cProfile.run("main()")
    else:
        main()