import sqlite3

conn = sqlite3.connect("data/databse.db")

conn.execute("""""")

cursor = conn.execute("Select * FROM users")

users = cursor.fetchall()

for user in users:
    print(user)

conn.commit()
conn.close()