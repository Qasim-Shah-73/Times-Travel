import sqlite3

# Connect to your SQLite database
connection = sqlite3.connect('site.db')
cursor = connection.cursor()

# Drop the temporary table if it exists
try:
    cursor.execute("DROP TABLE IF EXISTS _alembic_tmp_agencies;")
    print("Dropped table _alembic_tmp_agencies if it existed.")
except sqlite3.Error as e:
    print(f"An error occurred while dropping the table: {e}")

# Execute the PRAGMA command to list foreign key constraints
try:
    cursor.execute("PRAGMA foreign_key_list(agencies);")
    constraints = cursor.fetchall()
    print("Foreign key constraints for 'agencies' table:")
    for constraint in constraints:
        print(constraint)
except sqlite3.Error as e:
    print(f"An error occurred while executing PRAGMA command: {e}")

# Close the connection
connection.close()
