import os
import sqlite3
import csv
from tabulate import tabulate

HOME_DIR = os.path.expanduser("~")
DB_DIR = os.path.join(HOME_DIR, ".database")
sqlite_path = os.path.join(DB_DIR, "systemguard.db")
print(f"Connecting to SQLite database at: {sqlite_path}")

# Connect to the database
conn = sqlite3.connect(sqlite_path)
c = conn.cursor()

# Get a list of table names
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
table_names = [row[0] for row in c.fetchall()]

# Prompt the user to select a table
print("Available tables:")
for i, table in enumerate(table_names, 1):
    print(f"{i}. {table}")

table_choice = int(input("Enter the number of the table you want to access: "))
selected_table = table_names[table_choice - 1]
print(f"\nYou selected: {selected_table}\n")

# Show table data
c.execute(f"SELECT * FROM {selected_table};")
column_names = [description[0] for description in c.description]
rows = c.fetchall()

# Print the data in a tabular format
print(tabulate(rows, headers=column_names, tablefmt="grid"))

# Ask if the user wants to export the data as CSV
export_choice = input("\nDo you want to download this data as a CSV file? (yes/no): ").strip().lower()

if export_choice in ['yes', 'y']:
    csv_file_path = os.path.join(DB_DIR, f"{selected_table}.csv")
    with open(csv_file_path, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        # Write the header
        csv_writer.writerow(column_names)
        # Write the data
        csv_writer.writerows(rows)
    print(f"Data exported to {csv_file_path}")

# Close the database connection
conn.close()
