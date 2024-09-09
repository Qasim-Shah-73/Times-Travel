import sqlite3

# Connect to the SQLite database
connection = sqlite3.connect('site.db')
cursor = connection.cursor()

# Drop the 'invoices' table if it exists
try:
    cursor.execute("DROP TABLE IF EXISTS invoices;")
    print("Dropped table 'invoices' if it existed.")
except sqlite3.Error as e:
    print(f"An error occurred while dropping the table: {e}")

# Execute the PRAGMA command to list foreign key constraints for the 'invoices' table
try:
    cursor.execute("PRAGMA foreign_key_list(invoices);")
    constraints = cursor.fetchall()
    if constraints:
        print("Foreign key constraints for 'invoices' table:")
        for constraint in constraints:
            print(constraint)
    else:
        print("No foreign key constraints found for 'invoices' table.")
except sqlite3.Error as e:
    print(f"An error occurred while executing PRAGMA command: {e}")

# Close the connection
connection.close()
