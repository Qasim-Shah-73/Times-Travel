import sqlite3

# Connect to the SQLite database
connection = sqlite3.connect('site.db')
cursor = connection.cursor()

# Drop the '_alembic_tmp_bookings' table if it exists
try:
    cursor.execute("DROP TABLE IF EXISTS _alembic_tmp_bookings;")
    print("Dropped table '_alembic_tmp_bookings' if it existed.")
except sqlite3.Error as e:
    print(f"An error occurred while dropping the table: {e}")

# Execute the PRAGMA command to list foreign key constraints for the '_alembic_tmp_bookings' table
try:
    cursor.execute("PRAGMA foreign_key_list(_alembic_tmp_bookings);")
    constraints = cursor.fetchall()
    if constraints:
        print("Foreign key constraints for '_alembic_tmp_bookings' table:")
        for constraint in constraints:
            print(constraint)
    else:
        print("No foreign key constraints found for '_alembic_tmp_bookings' table.")
except sqlite3.Error as e:
    print(f"An error occurred while executing PRAGMA command: {e}")

# Close the connection
connection.close()
