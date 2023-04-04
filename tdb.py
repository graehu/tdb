import datetime
import sys
import os
import tempfile
import re

def extract_tags(text):
    pattern = re.compile(r'@\w+')
    return re.findall(pattern, text)

# Define the function to add a new record to the database.
def add_record(database_file, data):
    # Get the current date and time.
    now = datetime.datetime.now()

    # Join the lines of data with a newline character.
    data = "\n".join(data)

    # Open the database file in append mode.
    with open(database_file, "a") as f:
        # Write the new record to the file.
        f.write(f"|[{now}]|{data}\n")

    print("Record added successfully!")


# Define the function to display all records in the database.
def display_records(database_file):
    # Open the database file in read mode.
    with open(database_file, "r") as f:
        # Read the entire file into memory.
        file_contents = f.read()

    # Split the file contents into individual records.
    records = file_contents.strip().split("|[")

    # Loop through each record and print it.
    for record in records:
        # Split the record into its components.
        parts = record.strip().split("]|")
        if len(parts) != 2:
            continue
        date_str, data_str = parts
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
        data = data_str.split("\n")

        # Print the record.
        print(f"[{date}]:")
        for line in data:
            print(line)
        tags = extract_tags(" ".join(data))
        if tags: print("tags: "+" ".join(tags))




# Set the name of the database file.
database_file = "my_database.txt"

# Check the number of arguments.
if len(sys.argv) < 2:
    print("Usage: python program_name.py [add|display]")
    sys.exit(1)

# Parse the command-line arguments.
command = sys.argv[1]

if command == "add":
    # Check if there are any lines to read from stdin.
    if sys.stdin.isatty():
        # Join the command line arguments into a single string.
        data = [" ".join(sys.argv[2:])]
    else:
        # Read the data from stdin.
        data = []
        for line in sys.stdin:
            data.append(line.strip())

    # If the data is empty, open a temporary file with a text editor.
    if not data:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt") as f:
            # Wait for the user to close the editor.
            if os.name == "nt":
                editor = "notepad"
            else:
                editor = os.environ.get("EDITOR", "nano")
            os.system(f"{editor} {f.name}")
            f.seek(0)
            data = []
            for line in f:
                data.append(line.strip())


    # Add the record to the database if there is data.
    if data:
        add_record(database_file, data)
    else:
        print("No data provided. Record not added.")

elif command == "display":
    # Display all records in the database.
    display_records(database_file)

else:
    print("Invalid command. Try again.")
    sys.exit(1)
