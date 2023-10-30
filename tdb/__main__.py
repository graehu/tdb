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
            if "get_addon_name" in mod_vars:
                if "addon_tag" in mod_vars:
                    tdb.tags.register_cmd(module.get_addon_name(), module.addon_tag)
                if "addon_record" in mod_vars:
                    tdb.records.register_cmd(module.addon_record)
            else:
                print("failed to add '"+str(e)+"'. missing expected interface 'get_addon_name'.")


def main():
    if len(sys.argv) < 2:
        print("Usage: py -m tdb [add | show | config | edit | archive | template ] [text | options]")
        sys.exit(1)
    command = tdb.cli.get_command()
    options = tdb.cli.parse_options()
    edit_ext = tdb.config.get('edit_ext')
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
                tdb.records.modify_db_records(previous, text)
                content = text
                tdb.db.serialise()

            text = tdb.session.start("tdb_edit", content, ext=edit_ext, update_cb=update_db)
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
        
_profile = False
if __name__ == "__main__":
    if _profile:
        import cProfile
        cProfile.run("main()")
    else:
        main()