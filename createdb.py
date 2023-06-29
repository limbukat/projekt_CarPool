import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('carpool.sqlite')

# Create a cursor object
c = conn.cursor()
c.execute('''DROP TABLE car_category''')

c.execute('''DROP TABLE car''')

c.execute('''DROP TABLE reservation''')

# Execute an SQL statement to create a table
c.execute('''CREATE TABLE car_category
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name text)''')

c.execute('''CREATE TABLE car
             (id INTEGER PRIMARY KEY AUTOINCREMENT, spz text, category int)''')

c.execute('''CREATE TABLE reservation
             (id INTEGER PRIMARY KEY AUTOINCREMENT, car int, start_date date, end_date date, driver text, purpose text)''')

c.execute('''INSERT INTO car_category VALUES
             (1, "Malé auto - Škoda Scala")''')
c.execute('''INSERT INTO car_category VALUES
             (2, "Střední auto - Škoda Octavia")''')
c.execute('''INSERT INTO car_category VALUES
             (3, "Elektrické auto - Škoda Enyaq")''')

c.execute('''INSERT INTO car VALUES
             (0, "1A8 0001", 1)''')
c.execute('''INSERT INTO car VALUES
             (1, "1A8 0002", 1)''')
c.execute('''INSERT INTO car VALUES
             (2, "1A8 0003", 1)''')
c.execute('''INSERT INTO car VALUES
             (3, "1A8 0004", 2)''')
c.execute('''INSERT INTO car VALUES
             (4, "1A8 0005", 2)''')
c.execute('''INSERT INTO car VALUES
             (5, "1A8 0006", 2)''')
c.execute('''INSERT INTO car VALUES
             (6, "1A8 0007", 3)''')
c.execute('''INSERT INTO car VALUES
             (7, "1A8 0008", 3)''')
c.execute('''INSERT INTO car VALUES
             (8, "1A8 0009", 3)''')
c.execute('''INSERT INTO car VALUES
             (9, "1A8 0015", 2)''')
c.execute('''INSERT INTO car VALUES
             (10, "1A8 0016", 2)''')
c.execute('''INSERT INTO car VALUES
             (11, "1A8 0101", 1)''')

# Save (commit) the changes
conn.commit()

# Close the connection
conn.close()
